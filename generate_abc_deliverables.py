#!/usr/bin/env python3
"""
Generate test audio deliverables A, B, C and trace table for Dhvani Kannada TTS.
Script: MDR standard evaluation sentence
Voice: kn-IN-GaganNeural
"""

import os
import sys
import json
import asyncio
import shutil
import subprocess
from pathlib import Path

# Ensure user site-packages are accessible
user_site = os.path.expanduser("~/Library/Python/3.9/lib/python/site-packages")
if user_site not in sys.path:
    sys.path.insert(0, user_site)

from delivery_profiler import DeliveryProfiler
from prosody_mapper import KannadaProsodyMapper, BUILTIN_EXPRESSIVE_PROFILE
from pronunciation_engine import KannadaPronunciationEngine

MDR_TEST_SCRIPT = (
    "ನಾವು ₹1000 ಡಿಜಿಟಲ್ ಪೇಮೆಂಟ್ ಮಾಡಿದಾಗ, ವ್ಯಾಪಾರಿ 1% MDR ಕಡಿತಗೊಳಿಸುತ್ತಾನೆ. "
    "ದಿನಾಂಕ 15/08/1947 ರಂದು ಆರಂಭವಾದ ಈ ಪದ್ಧತಿಯು ಇಂದು YouTube ಮತ್ತು ChatGPT ನಂತಹ AI ತಂತ್ರಜ್ಞಾನಗಳ ಮೂಲಕ ಲಕ್ಷಾಂತರ ಜನರಿಗೆ ತಲುಪಿದೆ."
)

OUTPUT_DIR = Path("results")

async def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ref_audio_path = "uploads/ref_vidssave.com ✊🏼INDIA🇮🇳vs PAK at SCO summit💥 720P.mp3"
    
    # 1. Extract newly fixed profile from reference audio
    fixed_profile = None
    if os.path.exists(ref_audio_path):
        with open(ref_audio_path, "rb") as f:
            ref_bytes = f.read()
        fixed_profile = DeliveryProfiler.extract_prosody_profile(ref_bytes, max_duration_sec=60.0)
    else:
        fixed_profile = BUILTIN_EXPRESSIVE_PROFILE

    # -------------------------------------------------------------
    # Deliverable A: Baseline (Built-in profile, no continuity smoothing)
    # -------------------------------------------------------------
    print("Synthesizing A_current_baseline...")
    audio_a, meta_a = await KannadaProsodyMapper.synthesize_with_delivery_style(
        kannada_text=MDR_TEST_SCRIPT,
        voice="kn-IN-GaganNeural",
        energy_mode="high_energy",
        prosody_profile=BUILTIN_EXPRESSIVE_PROFILE,
        semantic_direction=True,
    )
    wav_a = OUTPUT_DIR / "A_current_baseline.wav"
    mp3_a = OUTPUT_DIR / "A_current_baseline.mp3"
    with open(wav_a, "wb") as f:
        f.write(audio_a)
    if shutil.which("ffmpeg"):
        subprocess.run(["ffmpeg", "-y", "-i", str(wav_a), "-b:a", "192k", str(mp3_a)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    elif shutil.which("afconvert"):
        subprocess.run(["afconvert", "-f", "mp4f", "-d", "aac", str(wav_a), str(mp3_a).replace(".mp3", ".m4a")], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        shutil.copy(str(wav_a), str(mp3_a))
    else:
        shutil.copy(str(wav_a), str(mp3_a))

    # -------------------------------------------------------------
    # Deliverable B: Profiler Fixed (Fresh measured profile)
    # -------------------------------------------------------------
    print("Synthesizing B_profiler_fixed...")
    audio_b, meta_b = await KannadaProsodyMapper.synthesize_with_delivery_style(
        kannada_text=MDR_TEST_SCRIPT,
        voice="kn-IN-GaganNeural",
        energy_mode="high_energy",
        prosody_profile=fixed_profile,
        semantic_direction=True,
    )
    wav_b = OUTPUT_DIR / "B_profiler_fixed.wav"
    mp3_b = OUTPUT_DIR / "B_profiler_fixed.mp3"
    with open(wav_b, "wb") as f:
        f.write(audio_b)
    if shutil.which("ffmpeg"):
        subprocess.run(["ffmpeg", "-y", "-i", str(wav_b), "-b:a", "192k", str(mp3_b)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else:
        shutil.copy(str(wav_b), str(mp3_b))

    # -------------------------------------------------------------
    # Deliverable C: Continuity Fixed (Fixed Profiler + Continuity Smoothing + Softened Trimming)
    # -------------------------------------------------------------
    print("Synthesizing C_continuity_fixed...")
    audio_c, meta_c = await KannadaProsodyMapper.synthesize_with_delivery_style(
        kannada_text=MDR_TEST_SCRIPT,
        voice="kn-IN-GaganNeural",
        energy_mode="high_energy",
        prosody_profile=fixed_profile,
        semantic_direction=True,
    )
    wav_c = OUTPUT_DIR / "C_continuity_fixed.wav"
    mp3_c = OUTPUT_DIR / "C_continuity_fixed.mp3"
    with open(wav_c, "wb") as f:
        f.write(audio_c)
    if shutil.which("ffmpeg"):
        subprocess.run(["ffmpeg", "-y", "-i", str(wav_c), "-b:a", "192k", str(mp3_c)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else:
        shutil.copy(str(wav_c), str(mp3_c))

    print(f"Generated:")
    print(f"  A: {mp3_a} ({os.path.getsize(mp3_a):,} bytes)")
    print(f"  B: {mp3_b} ({os.path.getsize(mp3_b):,} bytes)")
    print(f"  C: {mp3_c} ({os.path.getsize(mp3_c):,} bytes)")

    # Save meta C
    with open(OUTPUT_DIR / "meta_c.json", "w", encoding="utf-8") as f:
        json.dump(meta_c, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    asyncio.run(main())
