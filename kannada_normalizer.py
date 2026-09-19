#!/usr/bin/env python3
"""
Kannada Normalizer (ಕನ್ನಡ ಪಠ್ಯ ಸಾಮಾನ್ಯೀಕರಣ) v3.0
Pure Python Kannada Text Normalizer with Sandhi & Phonetic Rules.
Integrates with KannadaPronunciationEngine for user dictionary overrides, acronym spelling,
spoken currency/percentage formatting, and conjunct consonant preservation.
"""

import re
from typing import Optional, Dict, Any
from pronunciation_engine import KannadaPronunciationEngine

class KannadaNormalizer:
    """
    Main Kannada Text Normalizer class with full spoken expression support.
    Delegates pronunciation transformations to KannadaPronunciationEngine.
    """

    ONES = KannadaPronunciationEngine.ONES
    TEENS = KannadaPronunciationEngine.TEENS
    TENS_BASE = KannadaPronunciationEngine.TENS_BASE
    TENS_PREFIX = KannadaPronunciationEngine.TENS_PREFIX
    SANDHI_ONES = KannadaPronunciationEngine.SANDHI_ONES
    HUNDREDS_EXACT = KannadaPronunciationEngine.HUNDREDS_EXACT
    HUNDREDS_PREFIX = KannadaPronunciationEngine.HUNDREDS_PREFIX
    MONTHS_MAP = KannadaPronunciationEngine.MONTHS_MAP
    ABBREVIATIONS = KannadaPronunciationEngine.STANDARD_ABBREVIATIONS
    KN_DIGITS_MAP = KannadaPronunciationEngine.KN_DIGITS_MAP

    @classmethod
    def number_to_kannada(cls, n: int, conversational: bool = True) -> str:
        return KannadaPronunciationEngine.number_to_kannada(n, conversational=conversational)

    @classmethod
    def decimal_to_kannada(cls, num_str: str) -> str:
        return KannadaPronunciationEngine.decimal_to_kannada(num_str)

    @classmethod
    def normalize(cls, text: str, percent_style: str = "percent") -> str:
        """
        Normalizes input Kannada text into pronunciation-ready spoken Kannada script.
        """
        if not text:
            return ""
        _, speech_text, _ = KannadaPronunciationEngine.process_pronunciation(text, percent_style=percent_style)
        return speech_text

def normalize_kannada_text(text: str) -> str:
    """Convenience functional wrapper."""
    return KannadaNormalizer.normalize(text)

if __name__ == "__main__":
    sample = "ನಮ್ಮ ಹೊಸ app ನಲ್ಲಿ MDR ಶೇಕಡಾ 1% ಮತ್ತು ₹1000 ಗೆ UPI ಮೂಲಕ digital payment ಮಾಡಬಹುದು. ChatGPT ಮತ್ತು YouTube ನೋಡಿ!"
    print("Input :", sample)
    print("Output:", KannadaNormalizer.normalize(sample))
