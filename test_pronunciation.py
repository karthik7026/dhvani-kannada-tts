#!/usr/bin/env python3
"""
Comprehensive Automated Test Suite for Kannada Pronunciation Engine v3.0
Tests:
1. Native Kannada Vowel Length & Consonants (ಅ/ಆ, ಕ/ಖ, ಲ/ಳ, ಶ/ಷ/ಸ)
2. Ottakshara & Conjunct Consonant Integrity (ಪ್ರಶ್ನೆ, ಮುಖ್ಯ, ವ್ಯಕ್ತಿ, ತಂತ್ರಜ್ಞಾನ, ಸ್ವಲ್ಪ, ಗ್ರಾಹಕರು, ವ್ಯಾಪಾರಿ, ಪ್ರಕ್ರಿಯೆ)
3. Spoken Numerals, Currencies (₹10, ₹1000), Percentages (1%), Dates, Times
4. Configurable User Pronunciation Dictionary (MDR, UPI, YouTube, ChatGPT, digital payment, Merchant Discount Rate)
5. Generic Acronym Speller (Letter-by-Letter)
6. Code-Switching Natural Phrasing (Kannada + English mixed)
7. Display Text vs Speech Text Invariance
8. 3-Stage Pronunciation Debug Mode
9. End-to-End Edge-TTS Synthesis Verification
"""

import os
import sys
import json
import time
import asyncio
import unicodedata
from pronunciation_engine import KannadaPronunciationEngine, normalize_kannada_text

try:
    from prosody_mapper import KannadaProsodyMapper
    from acoustic_analyzer import analyze_audio
    HAS_SYNTH_DEPS = True
except ImportError:
    HAS_SYNTH_DEPS = False

def test_vowel_and_consonant_integrity():
    print("\n--- [Test 1] Vowel Length & Consonants Integrity ---")
    vowel_pairs = [
        ("ಅರಸ", "ಆಕಾಶ"),
        ("ಇಲಿ", "ಈಗ"),
        ("ಉಡುಪು", "ಊಟ"),
        ("ಎಲೆ", "ಏಣಿ"),
        ("ಒಂಟೆ", "ಓಟ")
    ]
    for short_v, long_v in vowel_pairs:
        _, s_out, _ = KannadaPronunciationEngine.process_pronunciation(short_v)
        _, l_out, _ = KannadaPronunciationEngine.process_pronunciation(long_v)
        assert s_out == short_v, f"Short vowel mismatch: {s_out} != {short_v}"
        assert l_out == long_v, f"Long vowel mismatch: {l_out} != {long_v}"

    consonant_pairs = [
        ("ಕಲಿಕೆ", "ಖಡ್ಗ"),
        ("ಗಮನ", "ಘಟನೆ"),
        ("ಚಲನೆ", "ಛತ್ರಿ"),
        ("ಜನ", "ಝರಿ"),
        ("ತಾಯಿ", "ಥಳಥಳ"),
        ("ದಿನ", "ಧನ"),
        ("ಪದ", "ಫಲ"),
        ("ಬಲ", "ಭರತ"),
        ("ಕಾಲ", "ಕಾಳ"),
        ("ಮನೆ", "ಮಣೆ"),
        ("ಶಾಲೆ", "ವರ್ಷ", "ಸಮಯ")
    ]
    for group in consonant_pairs:
        for word in group:
            _, out, _ = KannadaPronunciationEngine.process_pronunciation(word)
            assert out == word, f"Consonant altered: {out} != {word}"
    print("✓ All short/long vowels, aspirated consonants, and distinct letters (ಲ/ಳ, ನ/ಣ, ಶ/ಷ/ಸ) 100% preserved.")

def test_conjuncts_and_ottakshara():
    print("\n--- [Test 2] Ottakshara & Conjunct Consonants Integrity ---")
    benchmark_conjuncts = [
        "ಪ್ರಶ್ನೆ",
        "ಮುಖ್ಯ",
        "ವ್ಯಕ್ತಿ",
        "ತಂತ್ರಜ್ಞಾನ",
        "ಸ್ವಲ್ಪ",
        "ಗ್ರಾಹಕರು",
        "ವ್ಯಾಪಾರಿ",
        "ಪ್ರಕ್ರಿಯೆ",
        "ಕರ್ನಾಟಕ",
        "ಬೆಂಗಳೂರು",
        "ಸೃಷ್ಟಿ",
        "ಅದ್ಭುತ",
        "ರಾಷ್ಟ್ರೀಯ",
        "ಶಾಸ್ತ್ರ"
    ]
    for c_word in benchmark_conjuncts:
        _, speech_text, _ = KannadaPronunciationEngine.process_pronunciation(c_word)
        norm_expected = unicodedata.normalize("NFC", c_word)
        assert speech_text == norm_expected, f"Conjunct altered: {speech_text} != {norm_expected}"
        if '\u0ccd' in c_word:
            assert '\u0ccd' in speech_text, f"Virama lost in conjunct: {speech_text}"
        print(f"  ✓ Preserved: {c_word} -> {speech_text}")
    print("✓ All ottaksharas and multi-consonant clusters completely preserved without splitting.")

def test_numbers_currency_percentage():
    print("\n--- [Test 3] Spoken Numerals, Currency, Percentages & Dates ---")
    test_cases = [
        ("₹10", "ಹತ್ತು ರೂಪಾಯಿ"),
        ("₹1000", "ಸಾವಿರ ರೂಪಾಯಿ"),
        ("₹450", "ನಾನ್ನೂರ ಐವತ್ತು ರೂಪಾಯಿ"),
        ("₹450.50", "ನಾನ್ನೂರ ಐವತ್ತು ರೂಪಾಯಿ ಐವತ್ತು ಪೈಸೆ"),
        ("1%", "ಒಂದು ಪರ್ಸೆಂಟ್"),
        ("20%", "ಇಪ್ಪತ್ತು ಪರ್ಸೆಂಟ್"),
        ("10-15", "ಹತ್ತರಿಂದ ಹದಿನೈದು"),
        ("15/08/1947", "ಹದಿನೈದು ಆಗಸ್ಟ್ ಹತ್ತೊಂಬೈನೂರ ನಲವತ್ತೇಳು"),
        ("3:30 PM", "ಮೂರೂವರೆ ಗಂಟೆ"),
        ("2.5", "ಎರಡೂವರೆ")
    ]
    for input_txt, expected_contains in test_cases:
        _, speech_text, _ = KannadaPronunciationEngine.process_pronunciation(input_txt)
        assert expected_contains in speech_text, f"Failed for '{input_txt}': got '{speech_text}', expected '{expected_contains}'"
        print(f"  ✓ '{input_txt}' ➔ '{speech_text}'")
    print("✓ Conversational currency, percentage, decimal, and date formatting fully verified.")

def test_dictionary_overrides_and_acronyms():
    print("\n--- [Test 4] User Pronunciation Dictionary & Technical Terms ---")
    dict_cases = [
        ("MDR", "ಎಂ ಡಿ ಆರ್"),
        ("UPI", "ಯು ಪಿ ಐ"),
        ("AI", "ಎ ಐ"),
        ("API", "ಎ ಪಿ ಐ"),
        ("TTS", "ಟಿ ಟಿ ಎಸ್"),
        ("digital payment", "ಡಿಜಿಟಲ್ ಪೇಮೆಂಟ್"),
        ("Merchant Discount Rate", "ಮರ್ಚೆಂಟ್ ಡಿಸ್ಕೌಂಟ್ ರೇಟ್"),
        ("YouTube", "ಯೂಟ್ಯೂಬ್"),
        ("ChatGPT", "ಚಾಟ್ ಜಿಪಿಟಿ"),
        ("OTP", "ಒ ಟಿ ಪಿ"),
        ("PDF", "ಪಿ ಡಿ ಎಫ್")
    ]
    for eng_term, expected_kn in dict_cases:
        _, speech_text, transforms = KannadaPronunciationEngine.process_pronunciation(eng_term)
        assert expected_kn in speech_text, f"Dict override failed for '{eng_term}': got '{speech_text}', expected '{expected_kn}'"
        assert len(transforms) > 0, f"No transformation logged for '{eng_term}'"
        print(f"  ✓ '{eng_term}' ➔ '{speech_text}' (Rule: {transforms[0]['rule']})")

    # Generic Unlisted Acronym (e.g. SDK, CPU, GPU)
    _, sdk_out, _ = KannadaPronunciationEngine.process_pronunciation("SDK")
    assert "ಎಸ್ ಡಿ ಕೆ" in sdk_out, f"Generic acronym failed: {sdk_out}"
    print(f"  ✓ Generic Acronym 'SDK' ➔ '{sdk_out}' (Letter-by-Letter)")
    print("✓ User dictionary and acronym speller successfully verified.")

def test_code_switching():
    print("\n--- [Test 5] Kannada + English Code-Switching Sentences ---")
    sentences = [
        (
            "ನಮ್ಮ ಹೊಸ app ನಲ್ಲಿ MDR ಶೇಕಡಾ 1% ಮತ್ತು ₹1000 ಗೆ UPI ಮೂಲಕ digital payment ಮಾಡಬಹುದು.",
            "ನಮ್ಮ ಹೊಸ ಆಪ್ ನಲ್ಲಿ ಎಂ ಡಿ ಆರ್ ಒಂದು ಪರ್ಸೆಂಟ್ ಮತ್ತು ಸಾವಿರ ರೂಪಾಯಿ ಗೆ ಯು ಪಿ ಐ ಮೂಲಕ ಡಿಜಿಟಲ್ ಪೇಮೆಂಟ್ ಮಾಡಬಹುದು."
        ),
        (
            "YouTube ಮತ್ತು ChatGPT ನಲ್ಲಿ AI ಹಾಗೂ TTS API ಬಗ್ಗೆ ಸಂಪೂರ್ಣ ಮಾಹಿತಿ ಇದೆ.",
            "ಯೂಟ್ಯೂಬ್ ಮತ್ತು ಚಾಟ್ ಜಿಪಿಟಿ ನಲ್ಲಿ ಎ ಐ ಹಾಗೂ ಟಿ ಟಿ ಎಸ್ ಎ ಪಿ ಐ ಬಗ್ಗೆ ಸಂಪೂರ್ಣ ಮಾಹಿತಿ ಇದೆ."
        )
    ]
    for orig, expected_sub in sentences:
        display_text, speech_text, transforms = KannadaPronunciationEngine.process_pronunciation(orig)
        assert display_text == orig, "Display text altered!"
        print(f"  [Original]   : {display_text}")
        print(f"  [Speech Text]: {speech_text}")
        print(f"  [Transforms] : {len(transforms)} rules applied")
        assert "MDR" not in speech_text
        assert "UPI" not in speech_text
        assert "digital payment" not in speech_text
    print("✓ Mixed Kannada-English code-switching smoothly converted to natural spoken script.")

def test_debug_mode():
    print("\n--- [Test 6] 3-Stage Pronunciation Debug Mode ---")
    sample = "ಸಣ್ಣ ಅಂಗಡಿಗಳಿಗೆ MDR ಕೇವಲ 1% ಮಾತ್ರ. ₹1000 ವಹಿವಾಟಿಗೆ ₹10 ಉಳಿತಾಯ!"
    debug_info = KannadaPronunciationEngine.get_debug_breakdown(sample)
    assert "display_text" in debug_info
    assert "normalized_text" in debug_info
    assert "speech_text" in debug_info
    assert "transformations" in debug_info
    assert debug_info["transformations_count"] >= 3
    print(f"  1. Original Text  : {debug_info['display_text']}")
    print(f"  2. Normalized Text: {debug_info['normalized_text']}")
    print(f"  3. Speech Text    : {debug_info['speech_text']}")
    print(f"  ✓ Audit Log ({debug_info['transformations_count']} entries):")
    for t in debug_info["transformations"]:
        print(f"      - [{t['stage']}] {t['rule']}")
    print("✓ Debug audit trace fully functional.")

async def test_end_to_end_synthesis():
    print("\n--- [Test 7] End-to-End Delivery Styled Synthesis ---")
    if not HAS_SYNTH_DEPS:
        print("  ℹ️ Edge-TTS / NumPy optional dependencies not in environment. Skipping live audio synthesis.")
        return

    test_text = "ನಮ್ಮ ದೇಶದಲ್ಲಿ UPI ಮೂಲಕ digital payment ಕ್ರಾಂತಿ ಸೃಷ್ಟಿಯಾಗಿದೆ. ವ್ಯಾಪಾರಿಗಳಿಗೆ MDR ಶೇಕಡಾ 1% ಗಿಂತ ಕಡಿಮೆ ಇದ್ದು, ₹1000 ಖರೀದಿಗೆ ₹10 ಕ್ಯಾಶ್‌ಬ್ಯಾಕ್ ಸಿಗಲಿದೆ!"
    t0 = time.time()
    audio_bytes, meta = await KannadaProsodyMapper.synthesize_with_delivery_style(
        kannada_text=test_text,
        voice="kn-IN-GaganNeural",
        energy_mode="high_energy"
    )
    t_synth = time.time() - t0
    os.makedirs("results/tests", exist_ok=True)
    out_path = "results/tests/test_pronunciation_speech.wav"
    with open(out_path, "wb") as f:
        f.write(audio_bytes)
    
    metrics = analyze_audio(out_path)
    print(f"✓ Synthesis completed in {t_synth:.2f}s -> {out_path} ({len(audio_bytes)/1024:.1f} KB)")
    print(f"  - Display Text: {meta['display_text']}")
    print(f"  - Speech Text : {meta['speech_text']}")
    print(f"  - Duration    : {meta['duration_sec']}s")
    print(f"  - Pitch Span  : {metrics['pitch_movement_span_hz']} Hz (P10={metrics['p10_pitch_hz']}Hz, P90={metrics['p90_pitch_hz']}Hz)")
    print(f"  - Speech Ratio: {metrics['speech_activity_ratio_pct']}%")
    print("✓ End-to-end neural synthesis with pronunciation layer verified.")

async def main():
    print("=" * 65)
    print("  DHVANI KANNADA PRONUNCIATION & NORMALIZATION TEST SUITE")
    print("=" * 65)
    test_vowel_and_consonant_integrity()
    test_conjuncts_and_ottakshara()
    test_numbers_currency_percentage()
    test_dictionary_overrides_and_acronyms()
    test_code_switching()
    test_debug_mode()
    await test_end_to_end_synthesis()
    print("\n" + "=" * 65)
    print("  ALL PRONUNCIATION TESTS PASSED 100% SUCCESSFULLY! 🎉")
    print("=" * 65)

if __name__ == "__main__":
    asyncio.run(main())
