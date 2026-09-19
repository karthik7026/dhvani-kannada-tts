#!/usr/bin/env python3
"""
Dhvani Micro-Delivery Humanization Sweep (H0, H1, H2, H3)
=========================================================

Builds a conservative micro-delivery humanization layer on top of
frozen sentence-level synthesis (ONE Edge TTS call per complete sentence).

Generates 4 versions at different humanization strengths:
  - H0_baseline.wav — strength 0.00 (reproduces current sentence-level baseline)
  - H1_human_15.wav — strength 0.15
  - H2_human_30.wav — strength 0.30
  - H3_human_45.wav — strength 0.45

Requirements:
  - Single Groq delivery direction call for all sentences
  - Clear printout whether GROQ or LOCAL_FALLBACK was used
  - Exact sentence-level synthesis (1 Edge call per complete sentence)
  - Per-sentence report: intent, concepts, pace arc, pitch arc, energy arc, ending, strength, edge calls, final params
  - Save to results/ and export to artifact directory
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import wave
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np

# ---------------------------------------------------------------------------
# Project imports
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).parent))
from pronunciation_engine import KannadaPronunciationEngine
from sentence_humanizer import compute_sentence_params, get_delivery_directions

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MDR_TEST_SCRIPT = (
    "ನಾವು ₹1000 ಡಿಜಿಟಲ್ ಪೇಮೆಂಟ್ ಮಾಡಿದಾಗ, ವ್ಯಾಪಾರಿ 1% MDR ಕಡಿತಗೊಳಿಸುತ್ತಾನೆ. "
    "ದಿನಾಂಕ 15/08/1947 ರಂದು ಆರಂಭವಾದ ಈ ಪದ್ಧತಿಯು ಇಂದು YouTube ಮತ್ತು ChatGPT "
    "ನಂತಹ AI ತಂತ್ರಜ್ಞಾನಗಳ ಮೂಲಕ ಲಕ್ಷಾಂತರ ಜನರಿಗೆ ತಲುಪಿದೆ."
)

VOICE = "kn-IN-GaganNeural"
SAMPLE_RATE = 22050
RESULTS_DIR = Path(__file__).parent / "results"
ARTIFACT_DIR = Path("/Users/karthiku/.gemini/antigravity/brain/e94a0d7b-eb69-45f8-864e-a491bfffa395")

SWEEP_CONFIGS = [
    {"label": "H0", "filename": "H0_baseline.wav",  "strength": 0.00, "desc": "Baseline (0.00) — flat, matches Version A exactly"},
    {"label": "H1", "filename": "H1_human_15.wav",  "strength": 0.15, "desc": "Subtle (0.15) — micro delivery touch"},
    {"label": "H2", "filename": "H2_human_30.wav",  "strength": 0.30, "desc": "Moderate (0.30) — balanced human delivery"},
    {"label": "H3", "filename": "H3_human_45.wav",  "strength": 0.45, "desc": "Expressive (0.45) — distinct sentence arcs"},
]

# ---------------------------------------------------------------------------
# Audio helpers
# ---------------------------------------------------------------------------

def mp3_to_pcm(mp3_path: str, wav_path: str, sr: int = SAMPLE_RATE) -> np.ndarray:
    """Convert mp3 -> WAV -> float32 PCM using afconvert or ffmpeg."""
    if shutil.which("afconvert"):
        subprocess.run(
            ["afconvert", "-f", "WAVE", "-d", f"LEI16@{sr}", "-c", "1", mp3_path, wav_path],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
        )
    elif shutil.which("ffmpeg"):
        subprocess.run(
            ["ffmpeg", "-y", "-i", mp3_path, "-ac", "1", "-ar", str(sr), wav_path],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
        )
    else:
        raise RuntimeError("Neither afconvert nor ffmpeg found")

    with wave.open(wav_path, "rb") as wf:
        raw = wf.readframes(wf.getnframes())
        data = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    return data


def peak_normalize(pcm: np.ndarray, target: float = 0.95) -> np.ndarray:
    peak = float(np.max(np.abs(pcm)))
    if peak < 1e-6:
        return pcm
    return pcm * (target / peak)


def save_wav(pcm: np.ndarray, path: str, sr: int = SAMPLE_RATE) -> None:
    out = (pcm * 32767).astype(np.int16)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(out.tobytes())


def silence(duration_ms: float, sr: int = SAMPLE_RATE) -> np.ndarray:
    return np.zeros(int((duration_ms / 1000.0) * sr), dtype=np.float32)


def split_into_sentences(text: str) -> List[str]:
    """Split Kannada text on sentence-ending punctuation (. ? ! |)."""
    parts = re.split(r'(?<=[.?!|])\s+', text.strip())
    return [s.strip() for s in parts if s.strip()]


async def synthesize_sentence(
    text: str,
    voice: str,
    rate: str = "+0%",
    pitch: str = "+0Hz",
    volume: str = "+0%",
    temp_dir: str = "/tmp",
    tag: str = "chunk",
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """Single Edge TTS call for one complete sentence."""
    import edge_tts

    mp3_path = os.path.join(temp_dir, f"{tag}.mp3")
    wav_path = os.path.join(temp_dir, f"{tag}.wav")

    t0 = time.time()
    communicate = edge_tts.Communicate(text=text, voice=voice, pitch=pitch, rate=rate, volume=volume)
    await communicate.save(mp3_path)
    tts_time = round(time.time() - t0, 3)

    pcm = mp3_to_pcm(mp3_path, wav_path, SAMPLE_RATE)
    duration_s = round(len(pcm) / SAMPLE_RATE, 3)

    return pcm, {
        "text": text,
        "rate": rate,
        "pitch": pitch,
        "volume": volume,
        "duration_s": duration_s,
        "tts_time_s": tts_time,
    }


# ---------------------------------------------------------------------------
# Main Sweep Runner
# ---------------------------------------------------------------------------

async def run_sweep():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 75)
    print("DHVANI MICRO-DELIVERY HUMANIZATION SWEEP")
    print("=" * 75)
    print(f"Voice:            {VOICE}")
    print(f"Sample Rate:      {SAMPLE_RATE} Hz")
    print(f"MDR Script:       {MDR_TEST_SCRIPT[:60]}...")
    print("=" * 75 + "\n")

    # Step 1: Pronunciation processing
    engine = KannadaPronunciationEngine()
    display_text, speech_text, transforms = engine.process_pronunciation(MDR_TEST_SCRIPT)

    print(f"[1] Pronunciation Engine applied {len(transforms)} transforms:")
    for t in transforms:
        print(f"    - {t.get('stage', t.get('category', 'rule'))}: '{t['original']}' -> '{t['replacement']}'")

    display_sentences = split_into_sentences(display_text)
    speech_sentences = split_into_sentences(speech_text)

    if len(display_sentences) != len(speech_sentences):
        print(f"Warning: sentence count mismatch ({len(display_sentences)} vs {len(speech_sentences)}). Aligning by speech sentences.")
        display_sentences = speech_sentences

    total_sentences = len(speech_sentences)
    print(f"\n[2] Sentence Segmentation: {total_sentences} complete sentences:")
    for i, s in enumerate(display_sentences):
        print(f"    Sentence {i+1} [display]: {s}")
        print(f"    Sentence {i+1} [speech]:  {speech_sentences[i]}")

    # Step 2: Groq Delivery Directions
    print("\n" + "-" * 75)
    print("[3] Fetching Delivery Directions...")
    directions, source_label = await get_delivery_directions(display_sentences)
    print("=" * 75)
    print(f"DELIVERY DIRECTION SOURCE: >>> {source_label} <<<")
    print("=" * 75)

    for i, d in enumerate(directions):
        print(f"  Sentence {i+1} Directions:")
        print(f"    Intent:             {d.get('intent')}")
        print(f"    Ending:             {d.get('ending')}")
        print(f"    Emotion:            {d.get('emotion')}")
        print(f"    Important Concepts: {d.get('important_concepts')}")
        print(f"    Pace Arc:           {d.get('pace_arc')}")
        print(f"    Energy Arc:         {d.get('energy_arc')}")

    # Step 3: Generate 4 versions in sweep
    sweep_results = []

    with tempfile.TemporaryDirectory() as tmpdir:
        for cfg in SWEEP_CONFIGS:
            label = cfg["label"]
            filename = cfg["filename"]
            strength = cfg["strength"]
            desc = cfg["desc"]

            print("\n" + "=" * 75)
            print(f"GENERATING: {label} — {filename} (Strength = {strength:.2f})")
            print(f"Description: {desc}")
            print("=" * 75)

            sentence_pcms: List[np.ndarray] = []
            sentence_reports: List[Dict[str, Any]] = []
            prev_pitch = 0.0
            prev_rate = 0.0
            total_tts_time = 0.0

            for i, (disp_s, speech_s) in enumerate(zip(display_sentences, speech_sentences)):
                dir_info = directions[i] if i < len(directions) else {}
                params = compute_sentence_params(
                    direction=dir_info,
                    strength=strength,
                    prev_pitch=prev_pitch,
                    prev_rate=prev_rate,
                    sentence_index=i,
                    total_sentences=total_sentences,
                )

                # Exactly 1 Edge call per complete sentence
                pcm, meta = await synthesize_sentence(
                    text=speech_s,
                    voice=VOICE,
                    rate=params["rate"],
                    pitch=params["pitch"],
                    volume=params["volume"],
                    temp_dir=tmpdir,
                    tag=f"{label}_s{i+1}",
                )
                sentence_pcms.append(pcm)
                total_tts_time += meta["tts_time_s"]

                # Inter-sentence pause
                pause_ms = params["pause_after_ms"]
                if i < total_sentences - 1:
                    sentence_pcms.append(silence(pause_ms, SAMPLE_RATE))

                # Update contour tracking
                prev_pitch = params["raw_pitch"]
                prev_rate = params["raw_rate"]

                sent_rep = {
                    "sentence_index": i + 1,
                    "display_text": disp_s,
                    "speech_text": speech_s,
                    "intent": params["intent"],
                    "important_concepts": params["important_concepts"],
                    "pace_arc": params["pace_arc"],
                    "pitch_arc": f"raw {params['raw_pitch']:+.1f}Hz -> clamped {params['pitch']}",
                    "energy_arc": params["energy_arc"],
                    "ending_behavior": params["ending"],
                    "emotion": params["emotion"],
                    "humanization_strength": strength,
                    "edge_call_count": 1,
                    "final_edge_parameters": {
                        "rate": params["rate"],
                        "pitch": params["pitch"],
                        "volume": params["volume"],
                        "pause_after_ms": pause_ms if (i < total_sentences - 1) else 0,
                    },
                    "duration_s": meta["duration_s"],
                    "tts_time_s": meta["tts_time_s"],
                }
                sentence_reports.append(sent_rep)

                print(f"  Sentence {i+1}:")
                print(f"    Intent:        {params['intent']} | Ending: {params['ending']} | Emotion: {params['emotion']}")
                print(f"    Concepts:      {params['important_concepts']}")
                print(f"    Pace Arc:      {params['pace_arc']}")
                print(f"    Energy Arc:    {params['energy_arc']}")
                print(f"    Edge Params:   rate={params['rate']}, pitch={params['pitch']}, vol={params['volume']}, pause={pause_ms}ms")
                print(f"    Synthesis:     duration={meta['duration_s']}s, call_time={meta['tts_time_s']}s (1 Edge call)")

            # Concatenate and normalize
            full_pcm = np.concatenate(sentence_pcms)
            full_pcm = peak_normalize(full_pcm, 0.95)
            total_dur = round(len(full_pcm) / SAMPLE_RATE, 2)

            out_path = RESULTS_DIR / filename
            save_wav(full_pcm, str(out_path), SAMPLE_RATE)
            file_size_kb = round(out_path.stat().st_size / 1024, 1)

            print(f"  -> Saved {out_path} ({file_size_kb} KB, {total_dur}s, total TTS time: {total_tts_time:.2f}s)")

            # Copy to artifact directory for UI playback
            artifact_wav_path = ARTIFACT_DIR / filename
            shutil.copyfile(out_path, artifact_wav_path)
            print(f"  -> Copied to artifact: {artifact_wav_path}")

            sweep_results.append({
                "label": label,
                "filename": filename,
                "strength": strength,
                "description": desc,
                "duration_s": total_dur,
                "file_size_kb": file_size_kb,
                "total_edge_calls": total_sentences,
                "total_tts_time_s": round(total_tts_time, 2),
                "sentence_reports": sentence_reports,
            })

    # Step 4: Write JSON report
    report = {
        "title": "Dhvani Micro-Delivery Humanization Sweep Report",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "voice": VOICE,
        "sample_rate": SAMPLE_RATE,
        "direction_source": source_label,
        "mdr_test_script": MDR_TEST_SCRIPT,
        "pronunciation_transforms_count": len(transforms),
        "total_sentences": total_sentences,
        "sweep_results": sweep_results,
    }

    report_path = RESULTS_DIR / "humanization_sweep_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\nSaved full report to {report_path}")

    # Summary table
    print("\n" + "=" * 90)
    print(f"{'Version':<8} | {'Strength':<9} | {'Calls':<6} | {'Duration':<9} | {'S1 (Rate / Pitch / Pause)':<25} | {'S2 (Rate / Pitch)'}")
    print("-" * 90)
    for res in sweep_results:
        s1 = res["sentence_reports"][0]["final_edge_parameters"]
        s2 = res["sentence_reports"][1]["final_edge_parameters"]
        s1_str = f"{s1['rate']} / {s1['pitch']} / {s1['pause_after_ms']}ms"
        s2_str = f"{s2['rate']} / {s2['pitch']}"
        print(f"{res['label']:<8} | {res['strength']:<9.2f} | {res['total_edge_calls']:<6} | {res['duration_s']}s     | {s1_str:<25} | {s2_str}")
    print("=" * 90 + "\n")


if __name__ == "__main__":
    asyncio.run(run_sweep())
