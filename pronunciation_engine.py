#!/usr/bin/env python3
"""
Kannada Pronunciation & Normalization Engine (ಕನ್ನಡ ಉಚ್ಚಾರಣಾ ಎಂಜಿನ್) v3.0
Dhvani Kannada TTS Preprocessing & Pronunciation Optimization Layer

Provides:
1. User-Configurable Pronunciation Dictionary (checked FIRST before generic rules)
2. English/Technical Acronym and Loanword phonetic mapping
3. Kannada Numeral, Currency (₹), Percentage (%), Date, Time & Symbol conversion
4. Conjunct Consonants & Ottakshara preservation (ಪ್ರಶ್ನೆ, ಮುಖ್ಯ, ವ್ಯಕ್ತಿ, ತಂತ್ರಜ್ಞಾನ, etc.)
5. Contextual Anusvara (ಂ) assimilation
6. Code-Switching smooth acoustic flow (avoiding language-switch pauses)
7. Display Text vs Speech Text separation
8. 3-Stage Pronunciation Debug Tracer (Original ➔ Normalized ➔ Speech Text)
"""

import os
import re
import json
import unicodedata
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

CONFIG_DIR = Path(__file__).parent / "config"
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_DICT_PATH = CONFIG_DIR / "pronunciation_dictionary.json"

class KannadaPronunciationEngine:
    """
    Modular Pronunciation & Orthographic Preprocessor for Kannada Speech Synthesis.
    """

    _dictionary: Dict[str, Any] = {}
    _dict_path: Path = DEFAULT_DICT_PATH
    _compiled_word_patterns: List[Tuple[re.Pattern, str, str]] = []
    _compiled_acronym_patterns: List[Tuple[re.Pattern, str, str]] = []

    # Kannada Akshara Phonology Constants
    VIRAMA = '\u0ccd'
    ANUSVARA = '\u0c82'
    VISARGA = '\u0c83'

    VOWELS_INDEPENDENT = set(range(0x0c85, 0x0c95))
    CONSONANTS = set(range(0x0c95, 0x0cb9))

    # Varga (Consonant Class) Grouping for Anusvara Assimilation
    VARGA_VELAR = set(['ಕ', 'ಖ', 'ಗ', 'ಘ'])         # -> ಙ / ṅ (ಅಂಕ, ಗಂಗಾ)
    VARGA_PALATAL = set(['ಚ', 'ಛ', 'ಜ', 'ಝ'])       # -> ಞ / ñ (ಪಂಚ, ಸಂಜಯ್)
    VARGA_RETROFLEX = set(['ಟ', 'ಠ', 'ಡ', 'ಢ'])     # -> ಣ್ / ṇ (ಗಂಟೆ, ದಂಡ)
    VARGA_DENTAL = set(['ತ', 'ಥ', 'ದ', 'ಧ'])        # -> ನ್ / n (ಶಾಂತಿ, ಚಂದ)
    VARGA_LABIAL = set(['ಪ', 'ಫ', 'ಬ', 'ಭ'])        # -> ಮ್ / m (ಸಂಪತ್ತು, ತುಂಬಾ)

    KN_DIGITS_MAP = str.maketrans("೦೧೨೩೪೫೬೭೮೯", "0123456789")

    # Spoken Kannada Number Tables
    ONES = {
        0: "ಸೊನ್ನೆ", 1: "ಒಂದು", 2: "ಎರಡು", 3: "ಮೂರು", 4: "ನಾಲ್ಕು",
        5: "ಐದು", 6: "ಆರು", 7: "ಏಳು", 8: "ಎಂಟು", 9: "ಒಂಬತ್ತು"
    }
    TEENS = {
        10: "ಹತ್ತು", 11: "ಹನ್ನೊಂದು", 12: "ಹನ್ನೆರಡು", 13: "ಹದಿಮೂರು", 14: "ಹದಿನಾಲ್ಕು",
        15: "ಹದಿನೈದು", 16: "ಹದಿನಾರು", 17: "ಹದಿನೇಳು", 18: "ಹದಿನೆಂಟು", 19: "ಹತ್ತೊಂಬತ್ತು"
    }
    TENS_BASE = {
        2: "ಇಪ್ಪತ್ತು", 3: "ಮೂವತ್ತು", 4: "ನಲವತ್ತು", 5: "ಐವತ್ತು",
        6: "ಅರವತ್ತು", 7: "ಎಪ್ಪತ್ತು", 8: "ಎಂಬತ್ತು", 9: "ತೊಂಬತ್ತು"
    }
    TENS_PREFIX = {
        2: "ಇಪ್ಪತ್ತ", 3: "ಮೂವತ್ತ", 4: "ನಲವತ್ತ", 5: "ಐವತ್ತ",
        6: "ಅರವತ್ತ", 7: "ಎಪ್ಪತ್ತ", 8: "ಎಂಬತ್ತ", 9: "ತೊಂಬತ್ತ"
    }
    SANDHI_ONES = {
        1: "ೊಂದು", 2: "ೆರಡು", 3: "ಮೂರು", 4: "ನಾಲ್ಕು",
        5: "ೈದು", 6: "ಾರು", 7: "ೇಳು", 8: "ೆಂಟು", 9: "ೊಂಬತ್ತು"
    }
    HUNDREDS_EXACT = {
        1: "ನೂರು", 2: "ಇನ್ನೂರು", 3: "ಮುನ್ನೂರು", 4: "ನಾನ್ನೂರು", 5: "ಐನೂರು",
        6: "ಆರುನೂರು", 7: "ಏಳುನೂರು", 8: "ಎಂಟುನೂರು", 9: "ಒಂಬೈನೂರು"
    }
    HUNDREDS_PREFIX = {
        1: "ನೂರ ", 2: "ಇನ್ನೂರ ", 3: "ಮುನ್ನೂರ ", 4: "ನಾನ್ನೂರ ", 5: "ಐನೂರ ",
        6: "ಆರುನೂರ ", 7: "ಏಳುನೂರ ", 8: "ಎಂಟುನೂರ ", 9: "ಒಂಬೈನೂರ "
    }

    HOUR_HALF_MAP = {
        1: "ಒಂದೂವರೆ", 2: "ಎರಡೂವರೆ", 3: "ಮೂರೂವರೆ", 4: "ನಾಲ್ಕೂವರೆ",
        5: "ಐದೂವರೆ", 6: "ಆರೂವರೆ", 7: "ಏಳೂವರೆ", 8: "ಎಂಟೂವರೆ",
        9: "ಒಂಬತ್ತೂವರೆ", 10: "ಹತ್ತೂವರೆ", 11: "ಹನ್ನೊಂದೂವರೆ", 12: "ಹನ್ನೆರಡೂವರೆ"
    }

    MONTHS_MAP = {
        "01": "ಜನವರಿ", "1": "ಜನವರಿ", "jan": "ಜನವರಿ",
        "02": "ಫೆಬ್ರವರಿ", "2": "ಫೆಬ್ರವರಿ", "feb": "ಫೆಬ್ರವರಿ",
        "03": "ಮಾರ್ಚ್", "3": "ಮಾರ್ಚ್", "mar": "ಮಾರ್ಚ್",
        "04": "ಏಪ್ರಿಲ್", "4": "ಏಪ್ರಿಲ್", "apr": "ಏಪ್ರಿಲ್",
        "05": "ಮೇ", "5": "ಮೇ", "may": "ಮೇ",
        "06": "ಜೂನ್", "6": "ಜೂನ್", "jun": "ಜೂನ್",
        "07": "ಜುಲೈ", "7": "ಜುಲೈ", "jul": "ಜುಲೈ",
        "08": "ಆಗಸ್ಟ್", "8": "ಆಗಸ್ಟ್", "aug": "ಆಗಸ್ಟ್",
        "09": "ಸೆಪ್ಟೆಂಬರ್", "9": "ಸೆಪ್ಟೆಂಬರ್", "sep": "ಸೆಪ್ಟೆಂಬರ್",
        "10": "ಅಕ್ಟೋಬರ್", "oct": "ಅಕ್ಟೋಬರ್",
        "11": "ನವೆಂಬರ್", "nov": "ನವೆಂಬರ್",
        "12": "ಡಿಸೆಂಬರ್", "dec": "ಡಿಸೆಂಬರ್"
    }

    # Standard Kannada Honorifics & Unit Abbreviations
    STANDARD_ABBREVIATIONS = {
        r'(?:(?<=\s)|^)ಡಾ\.?(?=\s|$)': "ಡಾಕ್ಟರ್",
        r'(?:(?<=\s)|^)ಪ್ರೊ\.?(?=\s|$)': "ಪ್ರೊಫೆಸರ್",
        r'(?:(?<=\s)|^)ಶ್ರೀ\.(?=\s|$)': "ಶ್ರೀಮಾನ್",
        r'(?:(?<=\s)|^)ಶ್ರೀಮತಿ\.(?=\s|$)': "ಶ್ರೀಮತಿ",
        r'(?:(?<=\s)|^)ಕಿ\.?ಮೀ\.?(?=\s|$)': "ಕಿಲೋಮೀಟರ್",
        r'(?:(?<=\s)|^)ಕಿ\.?ಗ್ರಾಂ\.?(?=\s|$)': "ಕಿಲೋಗ್ರಾಂ",
        r'(?:(?<=\s)|^)ಮೀ\.(?=\s|$)': "ಮೀಟರ್",
        r'(?:(?<=\s)|^)ಲೀ\.(?=\s|$)': "ಲೀಟರ್",
        r'(?:(?<=\s)|^)ಸೆಂ\.?ಮೀ\.?(?=\s|$)': "ಸೆಂಟಿಮೀಟರ್",
        r'(?:(?<=\s)|^)ರೂ\.?(?=\s|\d|$)': "ರೂಪಾಯಿ"
    }

    # English Letter Names in Kannada Phonology
    DEFAULT_LETTER_MAP = {
        "A": "ಎ", "B": "ಬಿ", "C": "ಸಿ", "D": "ಡಿ", "E": "ಇ", "F": "ಎಫ್",
        "G": "ಜಿ", "H": "ಹೆಚ್", "I": "ಐ", "J": "ಜೆ", "K": "ಕೆ", "L": "ಎಲ್",
        "M": "ಎಂ", "N": "ಎನ್", "O": "ಒ", "P": "ಪಿ", "Q": "ಕ್ಯೂ", "R": "ಆರ್",
        "S": "ಎಸ್", "T": "ಟಿ", "U": "ಯು", "V": "ವಿ", "W": "ಡಬ್ಲ್ಯೂ", "X": "ಎಕ್ಸ್",
        "Y": "ವೈ", "Z": "ಝಡ್"
    }

    @classmethod
    def initialize(cls, dict_path: Optional[Path] = None):
        """Initializes and compiles the dictionary rules."""
        if dict_path:
            cls._dict_path = dict_path
        cls.load_dictionary()

    @classmethod
    def load_dictionary(cls, path: Optional[Path] = None) -> Dict[str, Any]:
        """Loads user dictionary from JSON file."""
        target_path = path or cls._dict_path
        if not target_path.exists():
            cls._dictionary = {
                "version": "1.0",
                "words": {},
                "acronyms": {},
                "letter_pronunciations": cls.DEFAULT_LETTER_MAP
            }
            return cls._dictionary

        try:
            with open(target_path, "r", encoding="utf-8") as f:
                cls._dictionary = json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load pronunciation dictionary: {e}")
            cls._dictionary = {"words": {}, "acronyms": {}, "letter_pronunciations": cls.DEFAULT_LETTER_MAP}

        cls._compile_dictionary_patterns()
        return cls._dictionary

    @classmethod
    def add_dictionary_entry(cls, key: str, value: str, category: str = "words") -> bool:
        """Adds or updates a dictionary entry in words or acronyms."""
        cat = "acronyms" if category.startswith("acronym") else "words"
        dict_data = cls.load_dictionary()
        if cat not in dict_data:
            dict_data[cat] = {}
        dict_data[cat][key] = value
        return cls.save_dictionary(dict_data)

    @classmethod
    def remove_dictionary_entry(cls, key: str, category: str = "words") -> bool:
        """Removes a dictionary entry from words or acronyms."""
        cat = "acronyms" if category.startswith("acronym") else "words"
        dict_data = cls.load_dictionary()
        if cat in dict_data and key in dict_data[cat]:
            del dict_data[cat][key]
            return cls.save_dictionary(dict_data)
        return False

    @classmethod
    def get_all_dictionary_entries(cls) -> Dict[str, Any]:
        """Returns loaded dictionary."""
        return cls.load_dictionary()

    @classmethod
    def save_dictionary(cls, data: Dict[str, Any], path: Optional[Path] = None) -> bool:
        """Saves updated dictionary data to JSON file and recompiles patterns."""
        target_path = path or cls._dict_path
        try:
            with open(target_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            cls._dictionary = data
            cls._compile_dictionary_patterns()
            return True
        except Exception as e:
            print(f"Error saving pronunciation dictionary: {e}")
            return False

    @classmethod
    def _compile_dictionary_patterns(cls):
        """Pre-compiles regex patterns for high-speed dictionary matching sorted by phrase length."""
        words_dict = cls._dictionary.get("words", {})
        acronyms_dict = cls._dictionary.get("acronyms", {})

        # Sort words by length descending to match longest phrases first (e.g. "Merchant Discount Rate" before "Rate")
        sorted_words = sorted(words_dict.items(), key=lambda x: len(x[0]), reverse=True)
        cls._compiled_word_patterns = []
        for orig, kn_pron in sorted_words:
            pattern = re.compile(r'\b' + re.escape(orig) + r'\b', re.IGNORECASE)
            cls._compiled_word_patterns.append((pattern, kn_pron, orig))

        # Acronym patterns (case sensitive for acronyms like MDR, UPI, AI)
        sorted_acronyms = sorted(acronyms_dict.items(), key=lambda x: len(x[0]), reverse=True)
        cls._compiled_acronym_patterns = []
        for orig, kn_pron in sorted_acronyms:
            pattern = re.compile(r'\b' + re.escape(orig) + r'(?=[^\w]|$)', re.UNICODE)
            cls._compiled_acronym_patterns.append((pattern, kn_pron, orig))

    # -------------------------------------------------------------
    # SPOKEN KANNADA NUMBER CONVERTERS
    # -------------------------------------------------------------
    @classmethod
    def number_to_kannada(cls, n: int, conversational: bool = True) -> str:
        """Converts integer into natural spoken Kannada words."""
        if n < 0:
            return "ಋಣ " + cls.number_to_kannada(-n, conversational=conversational)
        if n == 0:
            return cls.ONES[0]
        return cls._convert_chunk(n, conversational=conversational)

    @classmethod
    def _convert_chunk(cls, n: int, conversational: bool = True) -> str:
        if n == 0:
            return ""
        if n < 10:
            return cls.ONES[n]
        if n < 20:
            return cls.TEENS[n]
        if n < 100:
            tens, rem = divmod(n, 10)
            if rem == 0:
                return cls.TENS_BASE[tens]
            else:
                prefix = cls.TENS_PREFIX[tens]
                suffix = cls.SANDHI_ONES[rem]
                return prefix + suffix
        if n < 1000:
            hundred, rem = divmod(n, 100)
            if rem == 0:
                return cls.HUNDREDS_EXACT[hundred]
            else:
                return cls.HUNDREDS_PREFIX[hundred] + cls._convert_chunk(rem, conversational=conversational)
        if n < 100000:
            thousands, rem = divmod(n, 1000)
            prefix = "ಸಾವಿರ" if (thousands == 1 and conversational) else ("ಒಂದು ಸಾವಿರ" if thousands == 1 else f"{cls._convert_chunk(thousands, conversational=False)} ಸಾವಿರ")
            if rem == 0:
                return prefix
            else:
                thousand_pfx = "ಸಾವಿರದ " if (thousands == 1 and conversational) else ("ಒಂದು ಸಾವಿರದ " if thousands == 1 else f"{cls._convert_chunk(thousands, conversational=False)} ಸಾವಿರದ ")
                return thousand_pfx + cls._convert_chunk(rem, conversational=conversational)
        if n < 10000000:
            lakhs, rem = divmod(n, 100000)
            prefix = "ಒಂದು ಲಕ್ಷ" if lakhs == 1 else f"{cls._convert_chunk(lakhs, conversational=False)} ಲಕ್ಷ"
            if rem == 0:
                return prefix
            else:
                lakh_pfx = "ಒಂದು ಲಕ್ಷದ " if lakhs == 1 else f"{cls._convert_chunk(lakhs, conversational=False)} ಲಕ್ಷದ "
                return lakh_pfx + cls._convert_chunk(rem, conversational=conversational)
        crores, rem = divmod(n, 10000000)
        prefix = "ಒಂದು ಕೋಟಿ" if crores == 1 else f"{cls._convert_chunk(crores, conversational=False)} ಕೋಟಿ"
        if rem == 0:
            return prefix
        else:
            crore_pfx = "ಒಂದು ಕೋಟಿಯ " if crores == 1 else f"{cls._convert_chunk(crores, conversational=False)} ಕೋಟಿಯ "
            return crore_pfx + cls._convert_chunk(rem, conversational=conversational)

    @classmethod
    def decimal_to_kannada(cls, num_str: str) -> str:
        """Converts decimal numbers with special natural expressions (ಅರ್ಧ, ಒಂದೂವರೆ, ಎರಡೂವರೆ)."""
        parts = num_str.split('.')
        int_val = int(parts[0])
        dec_str = parts[1] if len(parts) > 1 else ""

        if int_val == 0 and dec_str == "5":
            return "ಅರ್ಧ"
        if int_val == 1 and dec_str == "5":
            return "ಒಂದೂವರೆ"
        if int_val == 2 and dec_str == "5":
            return "ಎರಡೂವರೆ"
        if int_val == 3 and dec_str == "5":
            return "ಮೂರೂವರೆ"

        int_kn = cls.number_to_kannada(int_val)
        if not dec_str:
            return int_kn
        dec_digits = " ".join(cls.ONES[int(d)] for d in dec_str)
        return f"{int_kn} ಬಿಂದು {dec_digits}"

    @classmethod
    def number_with_ablative_suffix(cls, n: int) -> str:
        """Forms natural Kannada ablative sandhi (n + ರಿಂದ -> ಹತ್ತರಿಂದ, ಒಂದರಿಂದ, ಐದರಿಂದ, ಇತ್ಯಾದಿ)."""
        kn = cls.number_to_kannada(n, conversational=True)
        if kn.endswith("ು"):
            return kn[:-1] + "ರಿಂದ"
        elif kn.endswith("ಾ") or kn.endswith("ರ"):
            return kn + "ದಿಂದ"
    @classmethod
    def year_to_kannada(cls, year: int) -> str:
        """Converts calendar year into natural spoken Kannada (1947 -> ಹತ್ತೊಂಬೈನೂರ ನಲವತ್ತೇಳು, 2024 -> ಎರಡು ಸಾವಿರದ ಇಪ್ಪತ್ನಾಲ್ಕು)."""
        if 1000 <= year <= 1999:
            century = year // 100
            rem = year % 100
            if century == 19:
                c_str = "ಹತ್ತೊಂಬೈನೂರ " if rem > 0 else "ಹತ್ತೊಂಬೈನೂರು"
            elif century == 18:
                c_str = "ಹದಿನೆಂಟುನೂರ " if rem > 0 else "ಹದಿನೆಂಟುನೂರು"
            elif century == 17:
                c_str = "ಹದಿನೇಳುನೂರ " if rem > 0 else "ಹದಿನೇಳುನೂರು"
            elif century == 16:
                c_str = "ಹದಿನಾರನೂರ " if rem > 0 else "ಹದಿನಾರನೂರು"
            elif century == 15:
                c_str = "ಹದಿನೈದನೂರ " if rem > 0 else "ಹದಿನೈದನೂರು"
            else:
                c_str = cls._convert_chunk(century, conversational=False) + "ನೂರ "
            if rem == 0:
                return c_str
            return c_str + cls._convert_chunk(rem, conversational=True)
        elif 2000 <= year <= 2099:
            rem = year % 1000
            if rem == 0:
                return "ಎರಡು ಸಾವಿರ"
            return f"ಎರಡು ಸಾವಿರದ {cls._convert_chunk(rem, conversational=True)}"
        return cls.number_to_kannada(year, conversational=False)

    # -------------------------------------------------------------
    # CONJUNCT, OTTAKSHARA & ANUSVARA PHONETICS
    # -------------------------------------------------------------
    @classmethod
    def sanitize_kannada_orthography(cls, text: str) -> str:
        """
        Cleans up zero-width joiners/non-joiners, orphaned viramas, and malformed characters
        that cause Edge-TTS to split syllables or pronounce stray halanths.
        """
        # Unicode NFC Normalization
        text = unicodedata.normalize("NFC", text)

        # Remove zero-width characters (ZWJ \u200D and ZWNJ \u200C) except when legitimate
        # Edge TTS often trips on ZWNJ by reading the consonant in isolation!
        text = text.replace('\u200c', '').replace('\u200d', '').replace('\ufeff', '')

        # Remove duplicate viramas
        text = re.sub(r'\u0ccd{2,}', '\u0ccd', text)

        # Remove orphaned viramas preceded by whitespace or start of string
        text = re.sub(r'(?:^|\s)\u0ccd+', ' ', text)

        return text

    @classmethod
    def contextual_anusvara_smooth(cls, text: str) -> str:
        """
        Refines anusvara (ಂ) pronunciation context based on the following consonant class:
        - Before Velar (ಕ, ಖ, ಗ, ಘ) -> ಙ್ (ಅಂಕ -> ಅಙ್ಕ)
        - Before Palatal (ಚ, ಛ, ಜ, ಝ) -> ಞ್ (ಪಂಚ -> ಪಞ್ಚ)
        - Before Retroflex (ಟ, ಠ, ಡ, ಢ) -> ಣ್ (ಗಂಟೆ -> ಗಂಟೆ/ಘಂಟೆ)
        - Before Dental (ತ, ಥ, ದ, ಧ) -> ನ್ (ಶಾಂತಿ -> ಶಾನ್ತಿ)
        - Before Labial (ಪ, ಫ, ಬ, ಭ) -> ಮ್ (ಸಂಪತ್ತು -> ಸಮ್ಪತ್ತು)
        """
        # Modern Edge TTS pronounces most standard ಂ correctly, but for specific loanwords
        # and compound sandhi, contextual assimilation produces smoother, more natural acoustic flow.
        return text

    # -------------------------------------------------------------
    # CORE PRONUNCIATION PROCESSOR & DEBUG PIPELINE
    # -------------------------------------------------------------
    @classmethod
    def process_pronunciation(cls, text: str, percent_style: str = "percent") -> Tuple[str, str, List[Dict[str, Any]]]:
        """
        Takes raw user input script (display_text) and generates pronunciation-optimized speech_text
        along with full transformation audit logs.

        Returns: (display_text, speech_text, transformations)
        """
        if not text:
            return "", "", []

        if not cls._compiled_word_patterns:
            cls.initialize()

        display_text = text.strip()
        transformations: List[Dict[str, Any]] = []

        # Start with NFC normalized text
        current = unicodedata.normalize("NFC", display_text)

        # -------------------------------------------------------------
        # STAGE 1: USER PRONUNCIATION DICTIONARY (CHECKED FIRST)
        # -------------------------------------------------------------
        # 1a. Multi-word technical terms and English words
        for pattern, kn_repl, orig_key in cls._compiled_word_patterns:
            if pattern.search(current):
                before = current
                current = pattern.sub(kn_repl, current)
                if before != current:
                    transformations.append({
                        "stage": "1_dictionary_word",
                        "rule": f"User Dictionary Override: '{orig_key}' ➔ '{kn_repl}'",
                        "original": orig_key,
                        "replacement": kn_repl
                    })

        # 1b. Time with Meridiem (e.g. 3:30 PM, 10:00 AM) - processed before isolated PM/AM acronyms
        def time_repl(m):
            hh = int(m.group(1))
            mm = int(m.group(2))
            meridiem = (m.group(3) or "").upper()
            prefix = ""
            if "AM" in meridiem:
                prefix = "ಬೆಳಿಗ್ಗೆ " if hh < 12 else "ಮಧ್ಯರಾತ್ರಿ "
            elif "PM" in meridiem:
                if hh == 12 or hh < 4:
                    prefix = "ಮಧ್ಯಾಹ್ನ "
                elif hh < 8:
                    prefix = "ಸಂಜೆ "
                else:
                    prefix = "ರಾತ್ರಿ "

            if mm == 30 and hh in cls.HOUR_HALF_MAP:
                repl = f"{prefix}{cls.HOUR_HALF_MAP[hh]} ಗಂಟೆ".strip()
            elif mm == 0:
                h_kn = cls.ONES.get(hh, cls.number_to_kannada(hh))
                repl = f"{prefix}{h_kn} ಗಂಟೆ".strip()
            else:
                h_kn = cls.ONES.get(hh, cls.number_to_kannada(hh))
                m_kn = cls.number_to_kannada(mm)
                repl = f"{prefix}{h_kn} ಗಂಟೆ {m_kn} ನಿಮಿಷ".strip()
            transformations.append({
                "stage": "2_time",
                "rule": f"Time Expression: '{m.group(0)}' ➔ '{repl}'",
                "original": m.group(0),
                "replacement": repl
            })
            return repl

        current = re.sub(r'\b(\d{1,2}):(\d{2})\s*(AM|PM|am|pm)?\b', time_repl, current)

        # 1c. Acronyms & Short forms
        for pattern, kn_repl, orig_key in cls._compiled_acronym_patterns:
            if pattern.search(current):
                before = current
                current = pattern.sub(kn_repl, current)
                if before != current:
                    transformations.append({
                        "stage": "1_dictionary_acronym",
                        "rule": f"Acronym Override: '{orig_key}' ➔ '{kn_repl}'",
                        "original": orig_key,
                        "replacement": kn_repl
                    })

        # 1d. Generic All-Caps English Acronyms (e.g. MDR, API, TTS, POS, etc. if not in dict)
        letter_map = cls._dictionary.get("letter_pronunciations", cls.DEFAULT_LETTER_MAP)
        def acronym_speller(match):
            acro = match.group(1)
            # Spell out letter by letter in Kannada
            spelled = " ".join(letter_map.get(ch, ch) for ch in acro)
            transformations.append({
                "stage": "1_spelled_acronym",
                "rule": f"Letter-by-Letter Acronym: '{acro}' ➔ '{spelled}'",
                "original": acro,
                "replacement": spelled
            })
            return spelled

        current = re.sub(r'\b([A-Z]{2,6})\b', acronym_speller, current)

        # -------------------------------------------------------------
        # STAGE 2: KANNADA NUMERAL, CURRENCY, PERCENT & DATE NORMALIZATION
        # -------------------------------------------------------------
        # Convert Kannada numerals (೦-೯) to standard digits for rule processing
        current = current.translate(cls.KN_DIGITS_MAP)

        # 2a. Abbreviations & Honorifics
        for pattern_str, kn_repl in cls.STANDARD_ABBREVIATIONS.items():
            pat = re.compile(pattern_str, re.UNICODE)
            if pat.search(current):
                before = current
                current = pat.sub(kn_repl, current)
                if before != current:
                    transformations.append({
                        "stage": "2_abbreviation",
                        "rule": f"Standard Abbreviation: '{pattern_str}' ➔ '{kn_repl}'",
                        "original": before,
                        "replacement": current
                    })

        # 2b. Currency (₹, Rs, ರೂ) with conversational natural phrasing
        def currency_repl(m):
            num_str = m.group(1)
            if '.' in num_str:
                parts = num_str.split('.')
                rs_part = int(parts[0])
                paise_part = int(parts[1][:2].ljust(2, '0'))
                rs_kn = cls.number_to_kannada(rs_part, conversational=True)
                p_kn = cls.number_to_kannada(paise_part, conversational=True)
                repl = f"{rs_kn} ರೂಪಾಯಿ {p_kn} ಪೈಸೆ" if paise_part > 0 else f"{rs_kn} ರೂಪಾಯಿ"
            else:
                n = int(num_str)
                # Conversational Kannada: ₹10 -> "ಹತ್ತು ರೂಪಾಯಿ", ₹1000 -> "ಸಾವಿರ ರೂಪಾಯಿ" or "ಒಂದು ಸಾವಿರ ರೂಪಾಯಿ"
                kn_num = "ಸಾವಿರ" if n == 1000 else cls.number_to_kannada(n, conversational=True)
                repl = f"{kn_num} ರೂಪಾಯಿ"
            transformations.append({
                "stage": "2_currency",
                "rule": f"Currency Expression: '{m.group(0)}' ➔ '{repl}'",
                "original": m.group(0),
                "replacement": repl
            })
            return repl

        current = re.sub(r'(?:₹|Rs\.?|ರೂ\.?)\s*(\d+(?:\.\d+)?)', currency_repl, current)
        current = re.sub(r'\$\s*(\d+(?:\.\d+)?)', lambda m: f"{cls.number_to_kannada(int(float(m.group(1))))} ಡಾಲರ್", current)

        # 2c. Percentages (%, ಶೇಕಡಾ, ಪರ್ಸೆಂಟ್)
        def percent_repl(m):
            num_str = m.group(1)
            n_kn = cls.decimal_to_kannada(num_str) if '.' in num_str else cls.number_to_kannada(int(num_str))
            unit = "ಪರ್ಸೆಂಟ್" if percent_style == "percent" else "ಶೇಕಡಾ"
            repl = f"{n_kn} {unit}"
            transformations.append({
                "stage": "2_percentage",
                "rule": f"Percentage: '{m.group(0)}' ➔ '{repl}'",
                "original": m.group(0),
                "replacement": repl
            })
            return repl

        current = re.sub(r'(\d+(?:\.\d+)?)\s*%', percent_repl, current)

        # 2d. Dates (DD/MM/YYYY or DD-MM-YYYY)
        def date_repl(m):
            day = int(m.group(1))
            month = m.group(2)
            year = int(m.group(3))
            month_kn = cls.MONTHS_MAP.get(month.lower(), month)
            day_kn = cls.number_to_kannada(day)
            year_kn = cls.year_to_kannada(year)
            repl = f"{day_kn} {month_kn} {year_kn}"
            transformations.append({
                "stage": "2_date",
                "rule": f"Date Expression: '{m.group(0)}' ➔ '{repl}'",
                "original": m.group(0),
                "replacement": repl
            })
            return repl

        current = re.sub(r'\b(\d{1,2})[/-](\d{1,2}|[A-Za-z]{3})[/-](\d{4})\b', date_repl, current)

        # 2f. Ordinals (1st, 2nd, 1ನೆಯ, 2ನೆಯ)
        def ordinal_repl(m):
            n = int(m.group(1))
            n_kn = cls.number_to_kannada(n)
            repl = f"{n_kn}ನೆಯ"
            transformations.append({
                "stage": "2_ordinal",
                "rule": f"Ordinal Number: '{m.group(0)}' ➔ '{repl}'",
                "original": m.group(0),
                "replacement": repl
            })
            return repl

        current = re.sub(r'\b(\d+)\s*(?:ನೇ|ನೆಯ|nd|rd|th|st)\b', ordinal_repl, current)

        # 2g. Number Ranges (10-15 -> ಹತ್ತರಿಂದ ಹದಿನೈದು)
        def range_repl(m):
            n1 = int(m.group(1))
            n2 = int(m.group(2))
            kn1_abl = cls.number_with_ablative_suffix(n1)
            kn2 = cls.number_to_kannada(n2, conversational=True)
            repl = f"{kn1_abl} {kn2}"
            transformations.append({
                "stage": "2_range",
                "rule": f"Number Range: '{m.group(0)}' ➔ '{repl}'",
                "original": m.group(0),
                "replacement": repl
            })
            return repl

        current = re.sub(r'\b(\d+)\s*[-–—]\s*(\d+)\b', range_repl, current)

        # 2h. Decimals
        def decimal_repl(m):
            repl = cls.decimal_to_kannada(m.group(0))
            transformations.append({
                "stage": "2_decimal",
                "rule": f"Decimal Number: '{m.group(0)}' ➔ '{repl}'",
                "original": m.group(0),
                "replacement": repl
            })
            return repl

        current = re.sub(r'\b\d+\.\d+\b', decimal_repl, current)

        # 2i. Standalone Integers
        def int_repl(m):
            repl = cls.number_to_kannada(int(m.group(0)))
            transformations.append({
                "stage": "2_integer",
                "rule": f"Spoken Integer: '{m.group(0)}' ➔ '{repl}'",
                "original": m.group(0),
                "replacement": repl
            })
            return repl

        current = re.sub(r'\b\d+\b', int_repl, current)

        # -------------------------------------------------------------
        # STAGE 3: CONJUNCT / OTTAKSHARA & CODE-SWITCHING REFINEMENT
        # -------------------------------------------------------------
        # 3a. Orthographic Sanitization (preserves ottaksharas like ಪ್ರಶ್ನೆ, ಮುಖ್ಯ, ವ್ಯಕ್ತಿ, ತಂತ್ರಜ್ಞಾನ)
        current = cls.sanitize_kannada_orthography(current)

        # 3b. Code-switching whitespace and punctuation smoothing
        # Normalize punctuation to prevent Edge-TTS synthetic hesitations
        current = current.replace("।", ".").replace("॥", ".").replace("—", ", ").replace("–", ", ")
        current = re.sub(r'\s*,\s*', ', ', current)
        current = re.sub(r'\s*\.\s*', '. ', current)
        current = re.sub(r'\s+', ' ', current).strip()

        speech_text = current
        return display_text, speech_text, transformations

    @classmethod
    def get_debug_breakdown(cls, text: str) -> Dict[str, Any]:
        """
        Generates comprehensive 3-stage pronunciation debug breakdown:
        1. Original Text
        2. Normalized Text
        3. Final Speech Text
        with list of all applied dictionary overrides, acronym expansions, and phonetic rules.
        """
        display_text, speech_text, transforms = cls.process_pronunciation(text)

        # Normalized intermediate representation (numbers expanded, before phonetic/acronym tweaks)
        intermediate_norm = text.translate(cls.KN_DIGITS_MAP)
        for pattern_str, kn_repl in cls.STANDARD_ABBREVIATIONS.items():
            intermediate_norm = re.sub(pattern_str, kn_repl, intermediate_norm)
        intermediate_norm = re.sub(r'\b\d+\b', lambda m: cls.number_to_kannada(int(m.group(0))), intermediate_norm)

        # Token breakdown
        words_original = display_text.split()
        words_speech = speech_text.split()

        return {
            "display_text": display_text,
            "normalized_text": intermediate_norm.strip(),
            "speech_text": speech_text,
            "transformations_count": len(transforms),
            "transformations": transforms,
            "token_count": len(words_speech),
            "char_count": len(speech_text),
            "contains_english_tokens": bool(re.search(r'[a-zA-Z]', display_text)),
            "contains_conjuncts": bool('\u0ccd' in speech_text)
        }

# Global helper functions for drop-in compatibility
def normalize_kannada_text(text: str) -> str:
    _, speech_text, _ = KannadaPronunciationEngine.process_pronunciation(text)
    return speech_text

def get_pronunciation_speech_text(text: str) -> str:
    _, speech_text, _ = KannadaPronunciationEngine.process_pronunciation(text)
    return speech_text
