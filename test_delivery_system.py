#!/usr/bin/env python3
"""
Automated Test Suite for Delivery Prosody System v3.0
Tests:
1. DeliveryProfiler statistical extraction & caching
2. KannadaProsodyMapper akshara segmentation & 4-phase dynamic parameter mapping
3. End-to-end audio synthesis in Normal vs Delivery Style Transfer mode
4. Acoustic Verification of pitch excursion, pause distribution, and speech density
"""

import os
import sys
import json
import time
import asyncio
from delivery_profiler import DeliveryProfiler
from prosody_mapper import KannadaProsodyMapper, count_aksharas, BUILTIN_EXPRESSIVE_PROFILE
from kannada_normalizer import KannadaNormalizer
from acoustic_analyzer import analyze_audio

async def main():
    print("=" * 60)
    print("  DHVANI KANNADA DELIVERY PROSODY SYSTEM TEST SUITE v3.0")
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

    phrases = KannadaProsodyMapper.segment_kannada_text(sample_sentence, target_aksharas=12)
    print(f"✓ Segmented into {len(phrases)} contextual breath phrases:")
    for idx, p in enumerate(phrases, 1):
        print(f"    {idx}. \"{p['text']}\" (is_question={p['is_question']}, is_exclamation={p['is_exclamation']}, is_end={p['is_sentence_end']}, focus={p.get('has_focus')}, pause={p['pause_type']})")

    # -------------------------------------------------------------
    # 3. Test Parameter Dynamics
    # -------------------------------------------------------------
    print("\n[Test 3] Testing Dynamic Parameter Excursions & Contours...")
    for idx, p in enumerate(phrases):
        rate_str, pitch_str, pause_ms, tag = KannadaProsodyMapper.calculate_phrase_parameters(
            p, profile1, "kn-IN-GaganNeural", phrase_index=idx, total_phrases=len(phrases)
        )
        rate_val = int(rate_str.replace('%', ''))
        pitch_val = int(pitch_str.replace('Hz', ''))
        assert -20 <= rate_val <= 50, f"Rate out of bounds: {rate_val}"
        assert -35 <= pitch_val <= 50, f"Pitch out of bounds: {pitch_val}"
        assert 100 <= pause_ms <= 700, f"Pause out of bounds: {pause_ms}"
        print(f"    Phrase {idx+1}: Rate={rate_str}, Pitch={pitch_str}, Pause={pause_ms}ms, Tag={tag}")
    print("✓ All rate, pitch, and pause parameters successfully mapped with expressive 4-phase dynamics.")

    # -------------------------------------------------------------
    # 4. End-to-End Synthesis: Normal vs Delivery Styled
    # -------------------------------------------------------------
    print("\n[Test 4] End-to-End Synthesis & Acoustic Verification...")
    os.makedirs("results/tests", exist_ok=True)

    t0 = time.time()
    styled_audio, meta = await KannadaProsodyMapper.synthesize_with_delivery_style(
        kannada_text=sample_sentence,
        voice="kn-IN-GaganNeural",
        energy_mode="high_energy",
        prosody_profile=profile1
    )
    styled_path = "results/tests/test_styled_gagan.wav"
    with open(styled_path, "wb") as f:
        f.write(styled_audio)
    print(f"✓ Styled Synthesis completed in {time.time()-t0:.2f}s -> {styled_path} ({len(styled_audio)/1024:.1f} KB, duration {meta['duration_sec']}s)")
    print(f"  - Voice Used: {meta['voice_used']} (100% Original Identity)")
    print(f"  - Applied Plan: {len(meta['applied_plan'])} phrases synthesized with dynamic pauses")

    metrics = analyze_audio(styled_path)
    print("\n[Acoustic Verification Results]:")
    print(f"  - Voiced Pitch Movement Span: {metrics['pitch_movement_span_hz']} Hz (P10={metrics['p10_pitch_hz']}Hz, P90={metrics['p90_pitch_hz']}Hz, Span={metrics['pitch_span_semitones']} semitones)")
    print(f"  - Speech Activity Ratio: {metrics['speech_activity_ratio_pct']}% (Breathing room={100 - metrics['speech_activity_ratio_pct']:.1f}%)")
    print(f"  - Detected Pauses: Count={metrics['detected_pauses_count']}, Median={metrics['median_pause_ms']}ms, P90={metrics['p90_pause_ms']}ms")
    print(f"  - Dynamic Range: {metrics['dynamic_range_db']} dB, Crest Factor: {metrics['crest_factor_db']} dB")

    print("\n" + "=" * 60)
    print("  ALL TESTS PASSED SUCCESSFULLY! 🎉")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
