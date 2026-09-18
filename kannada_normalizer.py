#!/usr/bin/env python3
"""
Pure Python Kannada Text Normalizer with Sandhi & Phonetic Rules
Converts digits, currencies, percentages, dates, times, abbreviations, and punctuation into spoken Kannada words.
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

    ABBREVIATIONS = {
        r'\bಡಾ\.?\b': "ಡಾಕ್ಟರ್",
        r'\bಪ್ರೊ\.?\b': "ಪ್ರೊಫೆಸರ್",
        r'\bಶ್ರೀ\.?\b': "ಶ್ರೀಮಾನ್",
        r'\bಶ್ರೀಮತಿ\.?\b': "ಶ್ರೀಮತಿ",
        r'\bಕಿ\.?ಮೀ\.?\b': "ಕಿಲೋಮೀಟರ್",
        r'\bಕಿ\.?ಗ್ರಾಂ\.?\b': "ಕಿಲೋಗ್ರಾಂ",
        r'\bಮೀ\.?\b': "ಮೀಟರ್",
        r'\bಲೀ\.?\b': "ಲೀಟರ್",
        r'\bಬಿಬಿಎಂಪಿ\b': "ಬಿ ಬಿ ಎಂ ಪಿ",
        r'\bಕೆಎಸ್‌ಆರ್‌ಟಿಸಿ\b': "ಕೆ ಎಸ್ ಆರ್ ಟಿ ಸಿ",
        r'\bಬಿಎಂಟಿಸಿ\b': "ಬಿ ಎಂ ಟಿ ಸಿ",
        r'\bಐಪಿಎಲ್\b': "ಐ ಪಿ ಎಲ್",
        r'\bಎಸ್‌ಸಿಒ\b': "ಎಸ್ ಸಿ ಒ",
        r'\bಇಸ್ರೋ\b': "ಇಸ್ರೋ",
        r'\bಯುಪಿಐ\b': "ಯು ಪಿ ಐ",
        r'\bಎಐ\b': "ಎ ಐ"
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
    def decimal_to_kannada(cls, num_str: str) -> str:
        parts = num_str.split('.')
        int_part = cls.number_to_kannada(int(parts[0]))
        if len(parts) > 1 and parts[1]:
            if parts[0] == "0" and parts[1] == "5":
                return "ಅರ್ಧ"
            if parts[0] == "1" and parts[1] == "5":
                return "ಒಂದೂವರೆ"
            if parts[0] == "2" and parts[1] == "5":
                return "ಎರಡೂವರೆ"
            dec_digits = " ".join(cls.ONES[int(d)] for d in parts[1])
            return f"{int_part} ಬಿಂದು {dec_digits}"
        return int_part

    @classmethod
    def normalize(cls, text: str) -> str:
        if not text:
            return ""
        res = text.translate(cls.KN_DIGITS_MAP)

        # 1. Abbreviations
        for pattern, repl in cls.ABBREVIATIONS.items():
            res = re.sub(pattern, repl, res)

        # 2. Currency
        res = re.sub(r'(?:₹|Rs\.?|ರೂ\.?)\s*(\d+(?:\.\d+)?)', 
                     lambda m: (cls.decimal_to_kannada(m.group(1)) if '.' in m.group(1) else cls.number_to_kannada(int(m.group(1)))) + " ರೂಪಾಯಿಗಳು", res)
        res = re.sub(r'\$\s*(\d+(?:\.\d+)?)', 
                     lambda m: (cls.decimal_to_kannada(m.group(1)) if '.' in m.group(1) else cls.number_to_kannada(int(m.group(1)))) + " ಡಾಲರ್‌ಗಳು", res)

        # 3. Percentages
        res = re.sub(r'(\d+(?:\.\d+)?)\s*%', 
                     lambda m: (cls.decimal_to_kannada(m.group(1)) if '.' in m.group(1) else cls.number_to_kannada(int(m.group(1)))) + " ಪ್ರತಿಶತ", res)

        # 4. Dates DD/MM/YYYY or DD-MM-YYYY
        def date_repl(m):
            day = int(m.group(1))
            month = m.group(2)
            year = int(m.group(3))
            month_kn = cls.MONTHS_MAP.get(month, month)
            return f"{cls.number_to_kannada(day)} {month_kn} {cls.number_to_kannada(year)}"
        res = re.sub(r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b', date_repl, res)

        # 5. Time HH:MM AM/PM
        def time_repl(m):
            hh = int(m.group(1))
            mm = int(m.group(2))
            meridiem = (m.group(3) or "").upper()
            prefix = "ಬೆಳಿಗ್ಗೆ " if "AM" in meridiem else ("ಸಂಜೆ " if "PM" in meridiem else "")
            h_str = f"{cls.number_to_kannada(hh)} ಗಂಟೆ"
            m_str = f" {cls.number_to_kannada(mm)} ನಿಮಿಷ" if mm > 0 else ""
            return f"{prefix}{h_str}{m_str}".strip()
        res = re.sub(r'\b(\d{1,2}):(\d{2})\s*(AM|PM|am|pm)?\b', time_repl, res)

        # 6. Ordinals 1st, 2nd, 1ನೆಯ, 2ನೆಯ
        res = re.sub(r'(\d+)\s*(?:ನೇ|ನೆಯ|nd|rd|th|st)', lambda m: cls.number_to_kannada(int(m.group(1))) + "ನೆಯ", res)

        # 7. Decimal Numbers
        res = re.sub(r'\b\d+\.\d+\b', lambda m: cls.decimal_to_kannada(m.group(0)), res)

        # 8. Standalone Integers
        res = re.sub(r'\b\d+\b', lambda m: cls.number_to_kannada(int(m.group(0))), res)

        # 9. Punctuation cleanup
        res = res.replace("।", ".").replace("॥", ".").strip()
        res = re.sub(r'\s+', ' ', res)
        return res

def normalize_kannada_text(text: str) -> str:
    return KannadaNormalizer.normalize(text)
