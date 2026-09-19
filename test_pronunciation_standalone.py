#!/usr/bin/env python3
"""
Comprehensive Standalone Test Suite for Kannada Pronunciation Engine
Covers all requirements from user prompt:
1. Script & Phonetic Preservation (Vowels, Consonants, Conjuncts, Ottaksharas)
2. Spoken Numerals, Currency, Percentages, Dates, Times, Ranges
3. Configurable Pronunciation Dictionary (Technical terms & Acronyms)
4. Acronym Speller (Letter-by-letter Kannada phonetic mapping)
5. Display Text vs Speech Text Separation
6. 3-Stage Pronunciation Debug Mode & Traceability
7. Dictionary Add/Update/Delete Operations
"""

import sys
import unittest
from pronunciation_engine import KannadaPronunciationEngine, normalize_kannada_text, get_pronunciation_speech_text
from kannada_normalizer import KannadaNormalizer

class TestKannadaPronunciationEngine(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.engine = KannadaPronunciationEngine
        cls.normalizer = KannadaNormalizer()

    def test_01_vowel_and_consonant_preservation(self):
        """Verify vowel lengths, aspirated consonants, and distinct sibilants/retroflexes are intact."""
        vowel_pairs = [
            ("ಅಕ್ಕ", "ಆಟ"),
            ("ಇಲಿ", "ಈಜು"),
            ("ಉಡುಗೊರೆ", "ಊಟ"),
            ("ಎಲೆ", "ಏಣಿ"),
            ("ಒಂಟೆ", "ಓಟ")
        ]
        for short_w, long_w in vowel_pairs:
            _, speech_short, _ = self.engine.process_pronunciation(short_w)
            _, speech_long, _ = self.engine.process_pronunciation(long_w)
            self.assertEqual(speech_short, short_w)
            self.assertEqual(speech_long, long_w)

        consonant_pairs = [
            ("ಕರೆ", "ಖಚಿತ"),
            ("ಗಮನ", "ಘನತೆ"),
            ("ಚಲನೆ", "ಛತ್ರಿ"),
            ("ಜನ", "ಝೇಂಕಾರ"),
            ("ತನ", "ಥಿಯೇಟರ್"),
            ("ದಿನ", "ಧ್ವನಿ"),
            ("ಪದ", "ಫಲಿತಾಂಶ"),
            ("ಬಲ", "ಭಾರತ")
        ]
        for unaspirated, aspirated in consonant_pairs:
            _, s_unasp, _ = self.engine.process_pronunciation(unaspirated)
            _, s_asp, _ = self.engine.process_pronunciation(aspirated)
            self.assertEqual(s_unasp, unaspirated)
            self.assertEqual(s_asp, aspirated)

        distinctions = ["ಬಾಲ", "ಬಾಳ", "ಮನೆ", "ಹಣ", "ಶರ", "ಷಣ್ಮುಖ", "ಸರಸ"]
        for word in distinctions:
            _, speech, _ = self.engine.process_pronunciation(word)
            self.assertEqual(speech, word)

    def test_02_conjuncts_and_ottakshara(self):
        """Verify conjunct consonants and ottakshara are preserved cleanly."""
        conjunct_words = [
            "ಪ್ರಶ್ನೆ", "ಮುಖ್ಯ", "ವ್ಯಕ್ತಿ", "ತಂತ್ರಜ್ಞಾನ",
            "ಸ್ವಲ್ಪ", "ಗ್ರಾಹಕರು", "ವ್ಯಾಪಾರಿ", "ಪ್ರಕ್ರಿಯೆ",
            "ಸ್ವಾತಂತ್ರ್ಯ", "ಆಕರ್ಷಕ", "ಕರ್ನಾಟಕ"
        ]
        for w in conjunct_words:
            _, speech, _ = self.engine.process_pronunciation(w)
            self.assertEqual(speech, w, f"Failed preserving conjunct for {w}")
            self.assertIn('\u0ccd', speech, f"Virama lost in conjunct word {w}")

        anusvara_words = ["ಬೆಂಗಳೂರು", "ಹಂಪೆ", "ಸಂತೋಷ", "ಗಂಗಾ"]
        for w in anusvara_words:
            _, speech, _ = self.engine.process_pronunciation(w)
            self.assertEqual(speech, w, f"Failed preserving anusvara for {w}")

    def test_03_spoken_numerals_currency_and_formats(self):
        """Verify currency, percentages, dates, times, and ranges."""
        cases = [
            ("₹1000", "ಸಾವಿರ ರೂಪಾಯಿ"),
            ("₹10", "ಹತ್ತು ರೂಪಾಯಿ"),
            ("₹450", "ನಾನ್ನೂರ ಐವತ್ತು ರೂಪಾಯಿ"),
            ("1%", "ಒಂದು ಪರ್ಸೆಂಟ್"),
            ("2.5%", "ಎರಡೂವರೆ ಪರ್ಸೆಂಟ್"),
            ("10-15", "ಹತ್ತರಿಂದ ಹದಿನೈದು"),
            ("1-5", "ಒಂದರಿಂದ ಐದು"),
            ("15/08/1947", "ಹದಿನೈದು ಆಗಸ್ಟ್ ಹತ್ತೊಂಬೈನೂರ ನಲವತ್ತೇಳು"),
            ("3:30 PM", "ಮಧ್ಯಾಹ್ನ ಮೂರೂವರೆ ಗಂಟೆ"),
            ("9:00 AM", "ಬೆಳಿಗ್ಗೆ ಒಂಬತ್ತು ಗಂಟೆ")
        ]
        for raw, expected in cases:
            _, speech, _ = self.engine.process_pronunciation(raw)
            self.assertEqual(speech, expected, f"Mismatch for '{raw}': got '{speech}', expected '{expected}'")

    def test_04_technical_dictionary_and_acronyms(self):
        """Verify dictionary entries and acronym spelling."""
        cases = [
            ("MDR", "ಎಂ ಡಿ ಆರ್"),
            ("UPI", "ಯು ಪಿ ಐ"),
            ("ChatGPT", "ಚಾಟ್ ಜಿಪಿಟಿ"),
            ("digital payment", "ಡಿಜಿಟಲ್ ಪೇಮೆಂಟ್"),
            ("Merchant Discount Rate", "ಮರ್ಚೆಂಟ್ ಡಿಸ್ಕೌಂಟ್ ರೇಟ್"),
            ("AI", "ಎ ಐ"),
            ("API", "ಎ ಪಿ ಐ"),
            ("YouTube", "ಯೂಟ್ಯೂಬ್"),
            ("QR code", "ಕ್ಯೂ ಆರ್ ಕೋಡ್"),
            ("Google", "ಗೂಗಲ್"),
            ("ISRO", "ಇಸ್ರೋ")
        ]
        for token, expected in cases:
            _, speech, _ = self.engine.process_pronunciation(token)
            self.assertEqual(speech, expected, f"Dictionary mismatch for '{token}'")

    def test_05_unlisted_acronym_spelling(self):
        """Verify unlisted English all-caps acronyms are spelled letter-by-letter in Kannada."""
        cases = [
            ("RBI", "ಆರ್ ಬಿ ಐ"),
            ("ATM", "ಎ ಟಿ ಎಂ"),
            ("BHEL", "ಬಿ ಹೆಚ್ ಇ ಎಲ್"),
            ("GST", "ಜಿ ಎಸ್ ಟಿ"),
            ("KYC", "ಕೆ ವೈ ಸಿ")
        ]
        for token, expected in cases:
            _, speech, _ = self.engine.process_pronunciation(token)
            self.assertEqual(speech, expected, f"Acronym spelling mismatch for '{token}'")

    def test_06_display_vs_speech_text_separation(self):
        """Verify display text remains unchanged while speech text is pronunciation-optimized."""
        text = "ನಾವು ₹1000 ಡಿಜಿಟಲ್ ಪೇಮೆಂಟ್ ಮಾಡಿದಾಗ, ವ್ಯಾಪಾರಿ 1% MDR ಕಡಿತಗೊಳಿಸುತ್ತಾನೆ."
        display, speech, transforms = self.engine.process_pronunciation(text)

        self.assertEqual(display, text)
        self.assertIn("ಸಾವಿರ ರೂಪಾಯಿ", speech)
        self.assertIn("ಒಂದು ಪರ್ಸೆಂಟ್", speech)
        self.assertIn("ಎಂ ಡಿ ಆರ್", speech)
        self.assertNotIn("₹", speech)
        self.assertNotIn("%", speech)
        self.assertNotIn("MDR", speech)
        self.assertTrue(len(transforms) >= 3)

    def test_07_debug_breakdown_tracer(self):
        """Verify 3-stage debug tracer outputs structured metadata."""
        text = "ದಿನಾಂಕ 15/08/1947 ರಂದು ₹1000 ಮತ್ತು 1% MDR ಜಾರಿಗೆ ಬಂತು."
        debug = self.engine.get_debug_breakdown(text)

        self.assertIn("display_text", debug)
        self.assertIn("normalized_text", debug)
        self.assertIn("speech_text", debug)
        self.assertIn("transformations", debug)
        self.assertEqual(debug["display_text"], text)
        self.assertGreaterEqual(debug["transformations_count"], 3)

    def test_08_dynamic_dictionary_customization(self):
        """Verify adding, overriding, and deleting pronunciation dictionary entries."""
        test_key = "TestCryptoTokenXYZ"
        test_val = "ಟೆಸ್ಟ್ ಕ್ರಿಪ್ಟೋ ಟೋಕನ್"

        self.engine.add_dictionary_entry(test_key, test_val, "word")
        _, speech, _ = self.engine.process_pronunciation(f"ಇದು {test_key} ಆಗಿದೆ.")
        self.assertIn("ಟೆಸ್ಟ್ ಕ್ರಿಪ್ಟೋ ಟೋಕನ್", speech)

        self.engine.remove_dictionary_entry(test_key, "word")
        dict_data = self.engine.get_all_dictionary_entries()
        self.assertNotIn(test_key, dict_data.get("words", {}))

if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(TestKannadaPronunciationEngine)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
