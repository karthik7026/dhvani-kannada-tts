#!/usr/bin/env python3
"""
Pure Python Kannada Text Normalizer with Sandhi & Phonetic Rules
Converts digits, currencies, percentages, and punctuation into spoken Kannada words.
"""

import re

class KannadaNormalizer:
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
        1: "ೊಂದು",
        2: "ೆರಡು",
        3: "ಮೂರು",
        4: "ನಾಲ್ಕು",
        5: "ೈದು",
        6: "ಾರು",
        7: "ೇಳು",
        8: "ೆಂಟು",
        9: "ೊಂಬತ್ತು"
    }
    HUNDREDS_EXACT = {
        1: "ನೂರು", 2: "ಇನ್ನೂರು", 3: "ಮುನ್ನೂರು", 4: "ನಾನೂರು", 5: "ಐನೂರು",
        6: "ಆರುನೂರು", 7: "ಏಳುನೂರು", 8: "ಎಂಟುನೂರು", 9: "ಒಂಬೈನೂರು"
    }
    HUNDREDS_PREFIX = {
        1: "ನೂರ ", 2: "ಇನ್ನೂರ ", 3: "ಮುನ್ನೂರ ", 4: "ನಾನೂರ ", 5: "ಐನೂರ ",
        6: "ಆರುನೂರ ", 7: "ಏಳುನೂರ ", 8: "ಎಂಟುನೂರ ", 9: "ಒಂಬೈನೂರ "
    }
    KN_DIGITS_MAP = str.maketrans("೦೧೨೩೪೫೬೭೮೯", "0123456789")

    @classmethod
    def number_to_kannada(cls, n: int) -> str:
        if n < 0:
            return "ಋಣ " + cls.number_to_kannada(-n)
        if n == 0:
            return cls.ONES[0]
        return cls._convert_chunk(n)

    @classmethod
    def _convert_chunk(cls, n: int) -> str:
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
            return cls.HUNDREDS_EXACT[hundred] if rem == 0 else cls.HUNDREDS_PREFIX[hundred] + cls._convert_chunk(rem)
        if n < 100000:
            thousands, rem = divmod(n, 1000)
            prefix = "ಒಂದು ಸಾವಿರ" if thousands == 1 else f"{cls._convert_chunk(thousands)} ಸಾವಿರ"
            return prefix if rem == 0 else (f"ಒಂದು ಸಾವಿರದ {cls._convert_chunk(rem)}" if thousands == 1 else f"{cls._convert_chunk(thousands)} ಸಾವಿರದ {cls._convert_chunk(rem)}")
        if n < 10000000:
            lakhs, rem = divmod(n, 100000)
            prefix = "ಒಂದು ಲಕ್ಷ" if lakhs == 1 else f"{cls._convert_chunk(lakhs)} ಲಕ್ಷ"
            return prefix if rem == 0 else (f"ಒಂದು ಲಕ್ಷದ {cls._convert_chunk(rem)}" if lakhs == 1 else f"{cls._convert_chunk(lakhs)} ಲಕ್ಷದ {cls._convert_chunk(rem)}")
        crores, rem = divmod(n, 10000000)
        prefix = "ಒಂದು ಕೋಟಿ" if crores == 1 else f"{cls._convert_chunk(crores)} ಕೋಟಿ"
        return prefix if rem == 0 else (f"ಒಂದು ಕೋಟಿಯ {cls._convert_chunk(rem)}" if crores == 1 else f"{cls._convert_chunk(crores)} ಕೋಟಿಯ {cls._convert_chunk(rem)}")

    @classmethod
    def normalize(cls, text: str) -> str:
        res = text.translate(cls.KN_DIGITS_MAP)
        res = re.sub(r'(?:₹|Rs\.?|ರೂ\.?)\s*(\d+)', lambda m: cls.number_to_kannada(int(m.group(1))) + " ರೂಪಾಯಿಗಳು", res)
        res = re.sub(r'(\d+)%', lambda m: cls.number_to_kannada(int(m.group(1))) + " ಪ್ರತಿಶತ", res)
        res = re.sub(r'(\d+)\s*(?:ನೇ|ನೆ)', lambda m: cls.number_to_kannada(int(m.group(1))) + "ನೇ", res)
        res = re.sub(r'\b\d+\b', lambda m: cls.number_to_kannada(int(m.group(0))), res)
        res = res.replace("।", ".").strip()
        return res

if __name__ == "__main__":
    test_cases = [
        "ನಮ್ಮಲ್ಲಿ ೧೨೫೦ ಪುಸ್ತಕಗಳಿವೆ ಮತ್ತು ಬೆಲೆ ₹೪೫೦ ಆಗಿದೆ.",
        "ಭಾರತವು 1947 ರಲ್ಲಿ ಸ್ವಾತಂತ್ರ್ಯ ಪಡೆಯಿತು.",
        "ನಿಮಗೆ 20% ರಿಯಾಯಿತಿ ಸಿಗಲಿದೆ."
    ]
    for s in test_cases:
        print(f"In : {s}")
        print(f"Out: {KannadaNormalizer.normalize(s)}\n")
