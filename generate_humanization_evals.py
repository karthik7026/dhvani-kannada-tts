#!/usr/bin/env python3
"""
Generate the 4 Humanization Layer evaluation audio files:
1. results/humanization_00_baseline.wav (strength = 0.00)
2. results/humanization_05.wav (strength = 0.05)
3. results/humanization_10.wav (strength = 0.10)
4. results/humanization_15.wav (strength = 0.15)
"""

import os
import sys
import json
import asyncio
from pathlib import Path

# Ensure user site-packages are accessible
user_site = os.path.expanduser("~/Library/Python/3.9/lib/python/site-packages")
if user_site not in sys.path:
    sys.path.insert(0, user_site)

from prosody_mapper import KannadaProsodyMapper
from kannada_normalizer import KannadaNormalizer
from pronunciation_engine import KannadaPronunciationEngine

MDR_TEST_SCRIPT = (
    "ನಾವು ₹1000 ಡಿಜಿಟಲ್ ಪೇಮೆಂಟ್ ಮಾಡಿದಾಗ, ವ್ಯಾಪಾರಿ 1% MDR ಕಡಿತಗೊಳಿಸುತ್ತಾನೆ. "
    "ದಿನಾಂಕ 15/08/1947 ರಂದು ಆರಂಭವಾದ ಈ ಪದ್ಧತಿಯು ಇಂದು YouTube ಮತ್ತು ChatGPT ನಂತಹ AI ತಂತ್ರಜ್ಞಾನಗಳ ಮೂಲಕ ಲಕ್ಷಾಂತರ ಜನರಿಗೆ ತಲುಪಿದೆ."
)

OUTPUT_DIR = Path("results")

async def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    strengths = [
        ("humanization_00_baseline", 0.00),
        ("humanization_05", 0.05),
        ("humanization_10", 0.10),
        ("humanization_15", 0.15)
    ]
    
    results_summary = []
    
    print("=== Standard MDR Evaluation Script ===")
    print(f"Text: {MDR_TEST_SCRIPT}\n")
    
    # Check normalization & pronunciation preprocessing
    display_text, speech_text, transforms = KannadaPronunciationEngine.process_pronunciation(MDR_TEST_SCRIPT)
    print(f"Speech Phonetic Text: {speech_text}")
    print(f"Applied Transforms ({len(transforms)}): {transforms}\n")
    
    for filename_stem, strength in strengths:
        print(f"Generating {filename_stem}.wav (strength = {strength:.2f})...")
        audio_bytes, meta = await KannadaProsodyMapper.synthesize_with_delivery_style(
            kannada_text=MDR_TEST_SCRIPT,
            voice="kn-IN-GaganNeural",
            energy_mode="high_energy",
            semantic_direction=True,
            humanization_strength=strength
        )
        
        out_wav = OUTPUT_DIR / f"{filename_stem}.wav"
        with open(out_wav, "wb") as f:
            f.write(audio_bytes)
        
        file_size = len(audio_bytes)
        print(f" Saved: {out_wav} ({file_size:,} bytes)")
        
        results_summary.append({
            "name": filename_stem,
            "strength": strength,
            "file": str(out_wav),
            "size_bytes": file_size,
            "phrases": meta.get("applied_plan", [])
        })
        
    summary_path = OUTPUT_DIR / "humanization_comparison.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(results_summary, f, ensure_ascii=False, indent=2)
    print(f"\nSaved metadata comparison to {summary_path}")

if __name__ == "__main__":
    asyncio.run(main())
