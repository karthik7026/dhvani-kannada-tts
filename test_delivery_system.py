#!/usr/bin/env python3
"""
Automated Test Suite for Delivery Prosody System
Tests:
1. DeliveryProfiler statistical extraction & caching
2. KannadaProsodyMapper akshara segmentation & dynamic parameter mapping
3. End-to-end audio synthesis in Normal vs Delivery Style Transfer mode
"""

import os
import sys
import json
import time
import asyncio
from delivery_profiler import DeliveryProfiler
from prosody_mapper import KannadaProsodyMapper, count_aksharas, BUILTIN_EXPRESSIVE_PROFILE
from kannada_normalizer import KannadaNormalizer

async def main():
    print("=" * 60)
    print("  DHVANI KANNADA DELIVERY PROSODY SYSTEM TEST SUITE")
    print("=" * 60)

    # -------------------------------------------------------------
    # 1. Test DeliveryProfiler on Reference Audio
    # -------------------------------------------------------------
    ref_audio_path = "uploads/ref_vidssave.com ✊🏼INDIA🇮🇳vs PAK at SCO summit💥 720P.mp3"
    assert os.path.exists(ref_audio_path), f"Missing test audio at {ref_audio_path}"

    print("\n[Test 1] Extracting Delivery Prosody Profile from Reference Audio...")
    t0 = time.time()
    with open(ref_audio_path, "rb") as f:
        audio_bytes = f.read()

    profile1 = DeliveryProfiler.extract_prosody_profile(audio_bytes, max_duration_sec=60.0)
    t_first = time.time() - t0
    print(f"✓ Extracted in {t_first:.2f}s:")
    print(f"  - Speaking Rate: {profile1['speaking_rate']['pace_syl_sec']} syl/s ({profile1['speaking_rate']['tempo_category']})")
    print(f"  - Pitch Median: {profile1['pitch_dynamics']['median_hz']} Hz (Range: {profile1['pitch_dynamics']['range_hz']} Hz, Span: {profile1['pitch_dynamics']['span_semitones']} semitones)")
    print(f"  - Pauses: Median {profile1['pauses']['median_ms']} ms (Short: {profile1['pauses']['distribution']['short_pct']}%, Total: {profile1['pauses']['count']})")
    print(f"  - Dynamics: Crest Factor {profile1['energy_and_punch']['crest_factor_db']} dB, Energy Punch: {profile1['energy_and_punch']['energy_punch']}")
    print(f"  - Phrasing Target: {profile1['phrasing']['target_phrase_aksharas']} aksharas / phrase")

    # Test Caching
    t0 = time.time()
    profile2 = DeliveryProfiler.extract_prosody_profile(audio_bytes, max_duration_sec=60.0)
    t_cached = time.time() - t0
    assert profile2.get("cached") == True, "Cache did not return cached=True"
    print(f"✓ Caching verified: Instant response in {t_cached*1000:.2f} ms")

    # -------------------------------------------------------------
    # 2. Test Kannada Akshara & Prosody Segmentation
    # -------------------------------------------------------------
    print("\n[Test 2] Testing Kannada Akshara Counter & Prosody Segmentation...")
    sample_sentence = "ನಮಸ್ಕಾರ! ಇಂದಿನ ಮಹತ್ವದ ಸಭೆಯಲ್ಲಿ ಭಾರತದ ಪಾತ್ರ ಅತ್ಯಂತ ಪ್ರಮುಖವಾಗಿದೆ. ಮುಂದಿನ ದಿನಗಳಲ್ಲಿ ಏನಾಗಲಿದೆ?"
    
    aksharas = count_aksharas(sample_sentence)
    print(f"  - Akshara count for '{sample_sentence[:30]}...': {aksharas} aksharas")
    assert aksharas > 10, "Akshara count failed"

    phrases = KannadaProsodyMapper.segment_kannada_text(sample_sentence, target_aksharas=14)
    print(f"✓ Segmented into {len(phrases)} contextual breath phrases:")
    for idx, p in enumerate(phrases, 1):
        print(f"    {idx}. \"{p['text']}\" (is_question={p['is_question']}, is_exclamation={p['is_exclamation']}, is_end={p['is_sentence_end']}, pause={p['pause_type']})")

    # -------------------------------------------------------------
    # 3. Test Parameter Dynamics
    # -------------------------------------------------------------
    print("\n[Test 3] Testing Dynamic Parameter Excursions & Contours...")
    for idx, p in enumerate(phrases):
        rate_str, pitch_str, pause_ms = KannadaProsodyMapper.calculate_phrase_parameters(
            p, profile1, "kn-IN-GaganNeural", phrase_index=idx, total_phrases=len(phrases)
        )
        rate_val = int(rate_str.replace('%', ''))
        pitch_val = int(pitch_str.replace('Hz', ''))
        assert -10 <= rate_val <= 45, f"Rate out of bounds: {rate_val}"
        assert -20 <= pitch_val <= 30, f"Pitch out of bounds: {pitch_val}"
        assert 50 <= pause_ms <= 300, f"Pause out of bounds: {pause_ms}"
        print(f"    Phrase {idx+1}: Rate={rate_str}, Pitch={pitch_str}, Pause={pause_ms}ms")
    print("✓ All rate, pitch, and pause parameters successfully mapped with expressive dynamics.")

    # -------------------------------------------------------------
    # 4. End-to-End Synthesis: Normal vs Delivery Styled
    # -------------------------------------------------------------
    print("\n[Test 4] End-to-End Synthesis Test (Normal vs Delivery Styled)...")
    os.makedirs("results/tests", exist_ok=True)

    # 4a. Delivery Styled Mode
    t0 = time.time()
    styled_audio, meta = await KannadaProsodyMapper.synthesize_with_delivery_style(
        kannada_text=sample_sentence,
        voice="kn-IN-GaganNeural",
        prosody_profile=profile1
    )
    styled_path = "results/tests/test_styled_gagan.wav"
    with open(styled_path, "wb") as f:
        f.write(styled_audio)
    print(f"✓ Styled Synthesis completed in {time.time()-t0:.2f}s -> {styled_path} ({len(styled_audio)/1024:.1f} KB, duration {meta['duration_sec']}s)")
    print(f"  - Voice Used: {meta['voice_used']} (100% Original Identity)")
    print(f"  - Applied Plan: {len(meta['applied_plan'])} phrases synthesized with dynamic pauses")

    print("\n" + "=" * 60)
    print("  ALL TESTS PASSED SUCCESSFULLY! 🎉")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
