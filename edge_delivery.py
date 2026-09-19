#!/usr/bin/env python3
"""
Edge TTS Kannada Delivery Transfer Synthesizer & Evaluator v3.0

Synthesizes Kannada sentences under 3 conditions:
- Condition A: Vanilla (moderate pace, standard pause/chunking)
- Condition B: Flat Rate (fast pace, flat delivery)
- Condition C: 4-Phase Prosodic Delivery Transfer (dynamic pitch excursion ~80Hz, focus deceleration, broadcast mastering)

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

from kannada_normalizer import normalize_kannada_text
from prosody_mapper import KannadaProsodyMapper, count_aksharas
from acoustic_analyzer import analyze_audio

async def synthesize_edge_tts(text: str, voice: str, rate: str, pitch: str, out_path: str):
    communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    await communicate.save(out_path)

def mp3_to_wav(mp3_path: str, wav_path: str):
    import subprocess
    import shutil
    if shutil.which("afconvert"):
        subprocess.run(["afconvert", "-f", "WAVE", "-d", "LEI16@24000", "-c", "1", mp3_path, wav_path],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    elif shutil.which("ffmpeg"):
        subprocess.run(["ffmpeg", "-y", "-i", mp3_path, "-ac", "1", "-ar", "24000", wav_path],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    else:
        raise RuntimeError("Neither afconvert nor ffmpeg found for audio conversion.")

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
        m_a = analyze_audio(a_wav)
        results.append({"sentence": s_idx, "condition": "A_vanilla", "file": a_wav, **m_a})
        
        # B: Flat rate
        b_mp3 = f"results/s{s_idx:02d}_B_flatrate.mp3"
        b_wav = f"results/s{s_idx:02d}_B_flatrate.wav"
        await synthesize_edge_tts(norm_sent, voice, rate="+26%", pitch="+2Hz", out_path=b_mp3)
        mp3_to_wav(b_mp3, b_wav)
        m_b = analyze_audio(b_wav)
        results.append({"sentence": s_idx, "condition": "B_flatrate", "file": b_wav, **m_b})
        
        # C: Profile transfer (4-Phase Dynamic Prosody Engine)
        c_wav = f"results/s{s_idx:02d}_C_profile.wav"
        audio_bytes, meta = await KannadaProsodyMapper.synthesize_with_delivery_style(
            kannada_text=norm_sent,
            voice=voice,
            energy_mode="high_energy",
            pitch_depth=1.0,
            pacing_multiplier=1.0,
            pause_style="snappy"
        )
        with open(c_wav, "wb") as f:
            f.write(audio_bytes)
        m_c = analyze_audio(c_wav)
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
        m = analyze_audio(pt_wav)
        sweep_pts.append({"pace_setting": r, "speech_activity_ratio_pct": m["speech_activity_ratio_pct"], "pitch_movement_span_hz": m["pitch_movement_span_hz"]})
        
    with open("sweep/sweep.json", "w", encoding="utf-8") as f:
        json.dump(sweep_pts, f, indent=2, ensure_ascii=False)
    print("Generated sweep/sweep.json")

if __name__ == "__main__":
    asyncio.run(run_evaluation())
