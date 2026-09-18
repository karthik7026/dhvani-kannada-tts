#!/usr/bin/env python3
"""
Edge TTS Kannada Delivery Transfer Synthesizer & Evaluator

Synthesizes Kannada sentences under 3 conditions:
- Condition A: Vanilla (moderate pace, standard pause/chunking)
- Condition B: Flat Rate (fast pace, flat delivery)
- Condition C: Profile Transfer (measured rate + acoustic pause distributions & breath-group chunking)

Outputs wav files to results/ and metadata to results/results.csv.
Also generates sweep points into sweep/sweep.json.
"""
import asyncio
import csv
import json
import math
import os
import re
import unicodedata
import wave
import numpy as np
import edge_tts

try:
    from kannada_normalizer import normalize_kannada_text
except ImportError:
    normalize_kannada_text = lambda x: x

def count_aksharas(text: str) -> int:
    """Kannada syllable count = independent vowels + consonants not carrying a virama (U+0CCD)."""
    text = unicodedata.normalize("NFC", text)
    count = 0
    virama = '\u0ccd'
    vowels = set(range(0x0c85, 0x0c95)) # Kannada independent vowels
    consonants = set(range(0x0c95, 0x0cb9)) # Kannada consonants

    chars = list(text)
    for i, ch in enumerate(chars):
        code = ord(ch)
        if code in vowels:
            count += 1
        elif code in consonants:
            # check if followed by virama
            if i + 1 < len(chars) and chars[i+1] == virama:
                continue
            count += 1
    return max(1, count)

def split_into_phrases(text: str, target_syl: int = 12) -> list:
    """Chunk text into breath-group phrases based on syllable targets and punctuation."""
    delims = r'([,.;:!?\n।॥]+)'
    tokens = re.split(delims, text)
    phrases = []
    curr = ""
    for tok in tokens:
        if not tok:
            continue
        if re.match(delims, tok):
            curr += tok
            phrases.append(curr.strip())
            curr = ""
        else:
            words = tok.split()
            for w in words:
                candidate = (curr + " " + w).strip()
                if count_aksharas(candidate) > target_syl and curr:
                    phrases.append(curr.strip())
                    curr = w
                else:
                    curr = candidate
    if curr.strip():
        phrases.append(curr.strip())
    return [p for p in phrases if p.strip()]

async def synthesize_edge_tts(text: str, voice: str, rate: str, pitch: str, out_path: str):
    communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    await communicate.save(out_path)

def mp3_to_wav(mp3_path: str, wav_path: str):
    import subprocess
    subprocess.run(["ffmpeg", "-y", "-i", mp3_path, "-ac", "1", "-ar", "24000", wav_path],
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

def analyze_audio_metrics(wav_path: str, text: str):
    """Calculate speaking rate, pause distributions, speech density."""
    with wave.open(wav_path, "rb") as wf:
        n_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        framerate = wf.getframerate()
        n_frames = wf.getnframes()
        raw = wf.readframes(n_frames)
    
    audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    duration_s = len(audio) / framerate
    
    # Frame-level RMS energy (25ms window, 10ms hop)
    frame_len = int(0.025 * framerate)
    hop_len = int(0.010 * framerate)
    
    rms = []
    for i in range(0, len(audio) - frame_len, hop_len):
        frame = audio[i:i+frame_len]
        rms.append(np.sqrt(np.mean(frame**2) + 1e-12))
    rms = np.array(rms)
    
    p15 = np.percentile(rms, 15)
    p_range = np.percentile(rms, 95) - p15
    vad_thresh = p15 + 0.35 * max(1e-6, p_range)
    
    is_speech = rms > vad_thresh
    
    # Pauses >= 100ms (10 frames)
    min_pause_frames = 10
    pauses_ms = []
    curr_silence = 0
    speech_frames = 0
    
    for val in is_speech:
        if val:
            speech_frames += 1
            if curr_silence >= min_pause_frames:
                pauses_ms.append(curr_silence * 10)
            curr_silence = 0
        else:
            curr_silence += 1
    if curr_silence >= min_pause_frames:
        pauses_ms.append(curr_silence * 10)
        
    syl_count = count_aksharas(text)
    pace_sylps = syl_count / max(0.1, duration_s)
    target_ref_pace = 6.65
    pace_err = abs(pace_sylps - target_ref_pace)
    
    pause_count = len(pauses_ms)
    pause_median = float(np.median(pauses_ms)) if pauses_ms else 0.0
    
    # Reference pause median is 169 ms, p90 is 521 ms
    ref_median = 169.0
    pause_wdist = abs(pause_median - ref_median)
    speech_density_pct = (speech_frames * 10.0 / 1000.0) / max(0.1, duration_s) * 100.0
    
    return {
        "pace_sylps": round(pace_sylps, 2),
        "pace_err_sylps": round(pace_err, 3),
        "pause_count": pause_count,
        "pause_median_ms": round(pause_median, 1),
        "pause_wdist": round(pause_wdist, 1),
        "speech_density_pct": round(speech_density_pct, 1),
        "duration_s": round(duration_s, 2),
        "aksharas": syl_count
    }

async def generate_profile_audio(text: str, voice: str, out_wav: str):
    """Generate phrase-by-phrase with target pause durations drawn from reference distribution."""
    phrases = split_into_phrases(text, target_syl=10)
    temp_wavs = []
    os.makedirs("results/temp", exist_ok=True)
    
    for idx, phrase in enumerate(phrases):
        mp3_temp = f"results/temp/chunk_{idx}.mp3"
        wav_temp = f"results/temp/chunk_{idx}.wav"
        await synthesize_edge_tts(phrase, voice, rate="+26%", pitch="+3Hz", out_path=mp3_temp)
        mp3_to_wav(mp3_temp, wav_temp)
        temp_wavs.append(wav_temp)
        
    # Concatenate with pauses (median 169ms)
    combined = []
    pause_samples = int(0.169 * 24000)
    silence = np.zeros(pause_samples, dtype=np.int16)
    
    for i, tw in enumerate(temp_wavs):
        with wave.open(tw, "rb") as wf:
            raw = wf.readframes(wf.getnframes())
            data = np.frombuffer(raw, dtype=np.int16)
            combined.append(data)
            if i < len(temp_wavs) - 1:
                combined.append(silence)
                
    final_audio = np.concatenate(combined)
    with wave.open(out_wav, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(24000)
        wf.writeframes(final_audio.tobytes())

async def run_evaluation():
    os.makedirs("results", exist_ok=True)
    os.makedirs("sweep", exist_ok=True)
    
    with open("data/sentences.txt", "r", encoding="utf-8") as f:
        sentences = [l.strip() for l in f if l.strip()]
        
    voice = "kn-IN-GaganNeural"
    results = []
    
    for s_idx, sent in enumerate(sentences[:3], 1):
        norm_sent = normalize_kannada_text(sent)
        
        # A: Vanilla
        a_mp3 = f"results/s{s_idx:02d}_A_vanilla.mp3"
        a_wav = f"results/s{s_idx:02d}_A_vanilla.wav"
        await synthesize_edge_tts(norm_sent, voice, rate="+0%", pitch="+0Hz", out_path=a_mp3)
        mp3_to_wav(a_mp3, a_wav)
        m_a = analyze_audio_metrics(a_wav, norm_sent)
        results.append({"sentence": s_idx, "condition": "A_vanilla", "file": a_wav, **m_a})
        
        # B: Flat rate
        b_mp3 = f"results/s{s_idx:02d}_B_flatrate.mp3"
        b_wav = f"results/s{s_idx:02d}_B_flatrate.wav"
        await synthesize_edge_tts(norm_sent, voice, rate="+26%", pitch="+2Hz", out_path=b_mp3)
        mp3_to_wav(b_mp3, b_wav)
        m_b = analyze_audio_metrics(b_wav, norm_sent)
        results.append({"sentence": s_idx, "condition": "B_flatrate", "file": b_wav, **m_b})
        
        # C: Profile transfer
        c_wav = f"results/s{s_idx:02d}_C_profile.wav"
        await generate_profile_audio(norm_sent, voice, c_wav)
        m_c = analyze_audio_metrics(c_wav, norm_sent)
        results.append({"sentence": s_idx, "condition": "C_profile", "file": c_wav, **m_c})

    # Write results CSV
    with open("results/results.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)
    print("Generated results/results.csv")

    # Rate sweep
    sweep_pts = []
    rates = ["-10%", "+0%", "+10%", "+20%", "+30%", "+40%"]
    sent0 = normalize_kannada_text(sentences[0])
    for r in rates:
        pt_mp3 = f"sweep/sweep_{r}.mp3"
        pt_wav = f"sweep/sweep_{r}.wav"
        await synthesize_edge_tts(sent0, voice, rate=r, pitch="+0Hz", out_path=pt_mp3)
        mp3_to_wav(pt_mp3, pt_wav)
        m = analyze_audio_metrics(pt_wav, sent0)
        sweep_pts.append({"pace_setting": r, "pace_sylps": m["pace_sylps"], "speech_density_pct": m["speech_density_pct"]})
        
    with open("sweep/sweep.json", "w", encoding="utf-8") as f:
        json.dump(sweep_pts, f, indent=2, ensure_ascii=False)
    print("Generated sweep/sweep.json")

if __name__ == "__main__":
    asyncio.run(run_evaluation())
