#!/usr/bin/env python3
"""
Kannada Prosody Mapper (ಕನ್ನಡ ಧ್ವನಿ ವಿತರಣಾ ಮ್ಯಾಪರ್) - High-Impact Expressive Presenter Engine v3.0
Maps language-agnostic ProsodyProfile delivery statistics onto Kannada text structures
using akshara-aware phrase segmentation, focus-word entity detection, 4-phase dynamic phrasing
(Setup Burst ➔ Anticipation ➔ Focus Gravitas ➔ Statement Release), dynamic pitch/speed inflections,
silence-trimmed breath pauses, and broadcast mastering while strictly preserving 100% of the
speaker voice identity (Gagan / Sapna).
"""

import os
import io
import re
import wave
import struct
import shutil
import tempfile
import subprocess
import unicodedata
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
from scipy import signal

from pronunciation_engine import KannadaPronunciationEngine
from speech_director import SpeechDirector

try:
    from kannada_normalizer import KannadaNormalizer
except ImportError:
    class KannadaNormalizer:
        @staticmethod
        def normalize(t): return t

# Measured baseline delivery profile from the high-energy reference presenter video.
# Filters out video editing/B-roll cuts and models distinct speech bursts, pitch dynamics,
# and pause distributions.
BUILTIN_EXPRESSIVE_PROFILE: Dict[str, Any] = {
    "profile_id": "youtube_presenter_v3",
    "pitch_dynamics": {
        "mean_hz": 183.1,
        "median_hz": 180.1,
        "p10_hz": 144.6,
        "p90_hz": 227.5,
        "pitch_movement_hz": 82.8,
        "span_semitones": 7.84,
        "ending_slope": "punchy_falling"
    },
    "speaking_rate": {
        "pace_syl_sec": 5.6,
        "pace_multiplier": 1.04,
        "burst_rate_syl_sec": 6.2,
        "speech_activity_ratio_pct": 82.0,
        "tempo_category": "Natural Human Creator"
    },
    "pauses": {
        "detected_pauses_count": 8,
        "raw_median_ms": 75.0,
        "raw_p90_sec": 0.250,
        "short_breath_ms": 75,
        "anticipation_ms": 80,
        "sentence_boundary_ms": 250,
        "dramatic_emphasis_ms": 120,
        "video_cut_filter_active": True
    },
    "energy_and_punch": {
        "mean_rms_db": -24.0,
        "energy_dynamic_range_db": 18.0,
        "crest_factor_db": 14.0,
        "energy_punch": 1.35,
        "transition_contrast": "Human Conversational"
    },
    "phrasing": {
        "target_phrase_aksharas": 32,
        "median_breath_sec": 0.08,
        "p90_breath_sec": 0.25
    }
}

# Regex patterns for identifying key focus entities in Kannada text
FOCUS_PATTERNS = [
    # Numbers & Quantities (Kannada digits & Arabic digits, currency, percentages)
    r'\b\d+[\d,.]*\b', r'[೦-೯]+', r'₹[\d,.]+', r'ಶೇಕಡಾ', r'ಕೋಟಿ', r'ಲಕ್ಷ', r'ಸಾವಿರ', r'ಶೇಕಡ',
    # Superlatives, Intensifiers & Punch Words
    r'ಅತ್ಯಂತ', r'ಪ್ರಮುಖ', r'ವಿಶೇಷವಾಗಿ', r'ಖಂಡಿತ', r'ಮಹತ್ವದ', r'ಸುವರ್ಣ', r'ಅದ್ಭುತ', r'ಐತಿಹಾಸಿಕ',
    r'ಎಚ್ಚರಿಕೆ', r'ಯಶಸ್ವಿ', r'ನಿಜವಾಗಿಯೂ', r'ಅಸಾಧ್ಯ', r'ಪ್ರಬಲ', r'ಶ್ರೇಷ್ಠ', r'ಮೊದಲ ಬಾರಿಗೆ',
    # Key Proper Nouns, Organizations & Entities
    r'ಭಾರತ', r'ಇಸ್ರೋ', r'ಚಂದ್ರಯಾನ', r'ಗಗನಯಾನ', r'ಆದಿತ್ಯ', r'ಎಸ್‌ಸಿಒ', r'ಎಸ್\u200cಸಿಒ',
    r'ಕರ್ನಾಟಕ', r'ಬೆಂಗಳೂರು', r'ಮೈಸೂರು', r'ವಿಶ್ವದ', r'ಪ್ರಧಾನಿ', r'ಅಮೆರಿಕ',
    # Interrogatives
    r'ಯಾಕೆ', r'ಹೇಗೆ', r'ಏನು', r'ಎಲ್ಲಿ', r'ಯಾರು', r'ಯಾವಾಗ', r'ಎಷ್ಟು'
]
FOCUS_REGEX = re.compile('|'.join(FOCUS_PATTERNS), re.UNICODE)

# Semantic direction is intentionally bounded here, not delegated to Groq.
# These are Edge-TTS-safe values that keep a creator delivery natural.
PROSODY_LIMITS: Dict[str, int] = {
    "MIN_RATE": -12,
    "MAX_RATE": 44,
    "MIN_PITCH": -38,
    "MAX_PITCH": 42,
    "MIN_VOLUME": -8,
    "MAX_VOLUME": 10,
    "MIN_PAUSE": 60,
    "MAX_PAUSE": 550,
}

# Keep Edge TTS in charge of natural sentence intonation. Semantic labels are
# deliberately a light overlay, configurable per request or deployment.
DEFAULT_SEMANTIC_PROSODY_STRENGTH = float(os.getenv("SEMANTIC_PROSODY_STRENGTH", "0.18"))
DEFAULT_HUMANIZATION_STRENGTH = float(os.getenv("HUMANIZATION_STRENGTH", "0.0"))

# Voice Identity Stability: Configurable adjacent prosody continuity constraints
MAX_ADJACENT_PITCH_DELTA_HZ: int = int(os.getenv("MAX_ADJACENT_PITCH_DELTA_HZ", "14"))
MAX_ADJACENT_RATE_DELTA_PCT: int = int(os.getenv("MAX_ADJACENT_RATE_DELTA_PCT", "10"))

# Default audio output format: 22kHz sample rate, 128k bitrate
DEFAULT_SAMPLE_RATE: int = int(os.getenv("DEFAULT_SAMPLE_RATE", "22050"))
DEFAULT_BITRATE: str = os.getenv("DEFAULT_BITRATE", "128k")

# Connector delimiters for natural breathing boundaries (excludes 'ಮತ್ತು' to preserve compound phrases)
CONNECTOR_DELIMS = re.compile(r'([,;:—–]+|\s+ಆದರೆ\s+|\s+ಆದ್ದರಿಂದ\s+|\s+ಆದಾಗ್ಯೂ\s+)', re.UNICODE)

def count_aksharas(text: str) -> int:
    """Calculates Kannada syllable count based on akshara phonology."""
    text = unicodedata.normalize("NFC", text)
    count = 0
    virama = '\u0ccd'
    vowels = set(range(0x0c85, 0x0c95))
    consonants = set(range(0x0c95, 0x0cb9))

    chars = list(text)
    for i, ch in enumerate(chars):
        code = ord(ch)
        if code in vowels:
            count += 1
        elif code in consonants:
            if i + 1 < len(chars) and chars[i+1] == virama:
                continue
            count += 1
    return max(1, count)

def has_focus_entity(text: str) -> bool:
    """Detects whether a phrase contains a focus entity, number, superlative, or proper noun."""
    return bool(FOCUS_REGEX.search(text))

def focus_words(text: str) -> List[str]:
    """Return a small, deduplicated set of words eligible for local emphasis."""
    seen = []
    for match in FOCUS_REGEX.finditer(text):
        word = match.group(0).strip()
        if word and word not in seen:
            seen.append(word)
    return seen[:2]

def _bounded(value: int, lower: str, upper: str) -> int:
    return max(PROSODY_LIMITS[lower], min(PROSODY_LIMITS[upper], int(value)))

def _parse_edge_value(value: str) -> int:
    return int(value.replace("Hz", "").replace("%", "").replace("+", ""))

def trim_silence_pcm(samples: np.ndarray, sr: int = DEFAULT_SAMPLE_RATE, thresh_db: float = -42.0, pad_ms: int = 24) -> np.ndarray:
    """
    Trims leading and trailing silence from Edge-TTS generated audio chunk,
    leaving a conservative 24ms safety margin to preserve natural phonetic onset
    and consonant decay tails.
    """
    if len(samples) == 0:
        return samples
    abs_samples = np.abs(samples)
    peak = np.max(abs_samples)
    if peak < 1e-4:
        return samples

    thresh = peak * (10.0 ** (thresh_db / 20.0))
    win_len = int(0.008 * sr) # 8ms window
    pad_samples = int((pad_ms / 1000.0) * sr)

    kernel = np.ones(win_len) / win_len
    energy = np.convolve(abs_samples, kernel, mode='same')

    above = np.where(energy > thresh)[0]
    if len(above) == 0:
        return samples

    start_idx = max(0, above[0] - pad_samples)
    end_idx = min(len(samples), above[-1] + pad_samples)
    return samples[start_idx:end_idx]

def apply_broadcast_mastering(pcm_data: np.ndarray, sr: int = DEFAULT_SAMPLE_RATE, punch: float = 1.35) -> np.ndarray:
    """
    Applies professional vocal mastering:
    1. 3.2kHz Peaking EQ (+3.5 dB vocal presence boost for speech intelligibility)
    2. Tanh soft-knee dynamic punch compressor (upfront YouTube presenter presence)
    3. True-peak broadcast normalization to -0.5 dBFS (0.95 peak)
    """
    if len(pcm_data) == 0:
        return pcm_data

    # 1. 3.2 kHz Vocal Presence EQ (2nd order biquad peaking filter)
    f0 = 3200.0
    Q = 1.0
    gain_db = 3.5
    A = 10.0 ** (gain_db / 40.0)
    w0 = 2.0 * np.pi * f0 / sr
    alpha = np.sin(w0) / (2.0 * Q)

    b0 = 1.0 + alpha * A
    b1 = -2.0 * np.cos(w0)
    b2 = 1.0 - alpha * A
    a0 = 1.0 + alpha / A
    a1 = -2.0 * np.cos(w0)
    a2 = 1.0 - alpha / A

    b = np.array([b0, b1, b2]) / a0
    a = np.array([a0, a1, a2]) / a0

    filtered = signal.lfilter(b, a, pcm_data)

    # 2. Dynamic Punch Soft-Knee Saturation
    boosted = filtered * max(1.0, min(1.7, punch))
    compressed = np.tanh(boosted)

    # 3. Peak Normalization to 0.95 (-0.5 dBFS)
    max_peak = np.max(np.abs(compressed))
    if max_peak > 1e-4:
        mastered = compressed / max_peak * 0.95
    else:
        mastered = compressed

    return mastered

class KannadaProsodyMapper:
    """
    Translates statistical Delivery Prosody into Kannada phrase-level TTS parameters
    with dynamic pitch excursion (~80-100Hz practical range), high-energy presenter rhythm,
    focus-word deceleration for gravitas, and snappy breath pauses.
    """

    @classmethod
    def segment_kannada_text(cls, text: str, target_aksharas: int = 12) -> List[Dict[str, Any]]:
        """
        Segments Kannada text into expressive breath-group phrases with contextual sentence-ending,
        focus-word detection, and question/exclamation metadata.
        """
        # Split into sentences by major punctuation
        sentence_chunks = re.split(r'([.?!।॥\n]+)', text)
        phrases = []

        for i in range(0, len(sentence_chunks), 2):
            sent_text = sentence_chunks[i].strip()
            punct = sentence_chunks[i+1].strip() if i+1 < len(sentence_chunks) else "."
            if not sent_text:
                continue

            # Sentence types
            is_question = "?" in punct or any(w in sent_text for w in ["ಯಾಕೆ", "ಹೇಗೆ", "ಏನು", "ಎಲ್ಲಿ", "ಯಾರು", "ಯಾವಾಗ", "ಎಷ್ಟು"])
            is_exclamation = "!" in punct

            # Split within sentence using connectors and punctuation
            sub_parts = CONNECTOR_DELIMS.split(sent_text)
            curr_acc = ""

            for part in sub_parts:
                if not part.strip():
                    continue
                if CONNECTOR_DELIMS.match(part):
                    if curr_acc:
                        phrases.append({
                            "text": curr_acc.strip(),
                            "is_sentence_end": False,
                            "is_question": False,
                            "is_exclamation": False,
                            "has_focus": has_focus_entity(curr_acc),
                            "punct": part.strip(),
                            "pause_type": "short"
                        })
                        curr_acc = ""
                else:
                    words = part.split()
                    for w in words:
                        cand = (curr_acc + " " + w).strip()
                        if count_aksharas(cand) > target_aksharas and curr_acc:
                            phrases.append({
                                "text": curr_acc.strip(),
                                "is_sentence_end": False,
                                "is_question": False,
                                "is_exclamation": False,
                                "has_focus": has_focus_entity(curr_acc),
                                "punct": ",",
                                "pause_type": "short"
                            })
                            curr_acc = w
                        else:
                            curr_acc = cand

            if curr_acc.strip():
                phrases.append({
                    "text": curr_acc.strip(),
                    "is_sentence_end": True,
                    "is_question": is_question,
                    "is_exclamation": is_exclamation,
                    "has_focus": has_focus_entity(curr_acc),
                    "punct": punct,
                    "pause_type": "long"
                })

        return phrases

    @classmethod
    def calculate_phrase_parameters(
        cls,
        phrase: Dict[str, Any],
        profile: Dict[str, Any],
        base_voice: str,
        phrase_index: int = 0,
        total_phrases: int = 1,
        energy_mode: str = "high_energy",
        pitch_depth: float = 1.0,
        pacing_multiplier: float = 1.0,
        pause_style: str = "snappy",
        direction: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, str, int, str]:
        """
        Maps reference prosody stats into expressive, dynamic Edge-TTS controls.
        Implements the 4-phase delivery cycle (Setup Burst ➔ Anticipation ➔ Focus Gravitas ➔ Statement Release).
        """
        rate_info = profile.get("speaking_rate", {})
        base_pace_mult = rate_info.get("pace_multiplier", 1.45) * pacing_multiplier

        # Energy Mode Profiles
        energy_offsets = {
            "calm": {"rate_delta": -2, "pitch_scale": 0.65, "pause_mult": 1.15, "tag": "Calm Narrator"},
            "balanced": {"rate_delta": 0, "pitch_scale": 0.85, "pause_mult": 1.0, "tag": "Balanced Explainer"},
            "high_energy": {"rate_delta": 2, "pitch_scale": 1.0, "pause_mult": 1.0, "tag": "Natural Human Creator"},
            "dramatic": {"rate_delta": 4, "pitch_scale": 1.25, "pause_mult": 1.2, "tag": "Dramatic Climax"}
        }
        cfg = energy_offsets.get(energy_mode, energy_offsets["high_energy"])

        # Base presenter rate: ~0% to +5% (conversational, not +44%)
        base_rate = int(max(-2.0, min(8.0, (base_pace_mult - 1.0) * 25.0 + cfg["rate_delta"])))

        # Pause style baselines (human breath gaps, not 500ms dead air)
        if pause_style == "snappy":
            base_setup_pause = 70
            base_anticipation_pause = 75
            base_focus_pause = 80
            base_sentence_pause = 240
        elif pause_style == "dramatic":
            base_setup_pause = 90
            base_anticipation_pause = 100
            base_focus_pause = 110
            base_sentence_pause = 300
        else: # balanced
            base_setup_pause = 75
            base_anticipation_pause = 80
            base_focus_pause = 85
            base_sentence_pause = 250

        is_male = ("gagan" in base_voice.lower() or "male" in base_voice.lower())
        p_scale = pitch_depth * cfg["pitch_scale"]

        is_question = phrase.get("is_question", False)
        is_exclamation = phrase.get("is_exclamation", False)
        is_sentence_end = phrase.get("is_sentence_end", False)
        has_focus = phrase.get("has_focus", False)

        # -------------------------------------------------------------
        # 4-PHASE DYNAMIC PROSODIC CYCLE (Conversational Human Range)
        # -------------------------------------------------------------
        if is_question:
            # 1. Rhetorical Question Peak (+7Hz to +9Hz)
            pitch_hz = int(round((7 if is_male else 9) * p_scale))
            applied_rate = min(8, base_rate + 2)
            pause_ms = int(base_sentence_pause * cfg["pause_mult"])
            tag = "❓ Rhetorical Question Peak"

        elif is_exclamation:
            # 2. Exclamatory Punch (+5Hz to +7Hz)
            pitch_hz = int(round((5 if is_male else 7) * p_scale))
            applied_rate = min(8, base_rate + 2)
            pause_ms = int(base_sentence_pause * 0.9 * cfg["pause_mult"])
            tag = "📢 Exclamatory Punch"

        elif has_focus and not is_sentence_end:
            # 3. Focus Entity Gravitas & Emphasis (+3Hz to +5Hz with gentle deceleration)
            pitch_hz = int(round((4 if is_male else 5) * p_scale))
            applied_rate = max(-3, base_rate - 2)
            pause_ms = int(base_focus_pause * cfg["pause_mult"])
            tag = "🎯 Focus Entity Gravitas"

        elif is_sentence_end:
            # 4. Grounded Statement Landing (-3Hz to -4Hz natural cadence fall)
            pitch_hz = int(round((-3 if is_male else -4) * p_scale))
            applied_rate = max(-3, base_rate - 2)
            pause_ms = int(base_sentence_pause * cfg["pause_mult"])
            tag = "💥 Authoritative Cadence Fall"

        elif phrase_index == 0 or phrase_index % 3 == 0:
            # 5. Setup Clause (+3Hz to +4Hz)
            pitch_hz = int(round((3 if is_male else 4) * p_scale))
            applied_rate = min(8, base_rate + 2)
            pause_ms = int(base_setup_pause * cfg["pause_mult"])
            tag = "⚡ Setup Clause"

        else:
            # 6. Anticipation Build (+2Hz to +3Hz)
            pitch_hz = int(round((2 if is_male else 3) * p_scale))
            applied_rate = base_rate
            pause_ms = int(base_anticipation_pause * cfg["pause_mult"])
            tag = "📈 Anticipation Build-Up"

        applied_rate = _bounded(applied_rate, "MIN_RATE", "MAX_RATE")
        pitch_hz = _bounded(pitch_hz, "MIN_PITCH", "MAX_PITCH")
        pause_ms = _bounded(pause_ms, "MIN_PAUSE", "MAX_PAUSE")
        rate_str = f"+{applied_rate}%" if applied_rate >= 0 else f"{applied_rate}%"
        pitch_str = f"+{pitch_hz}Hz" if pitch_hz >= 0 else f"{pitch_hz}Hz"

        return rate_str, pitch_str, pause_ms, tag

    @classmethod
    def get_phrase_delivery(
        cls,
        phrase: Dict[str, Any],
        profile: Dict[str, Any],
        base_voice: str,
        phrase_index: int,
        total_phrases: int,
        energy_mode: str,
        pitch_depth: float,
        pacing_multiplier: float,
        pause_style: str,
        direction: Optional[Dict[str, Any]],
        semantic_direction: bool = True,
        semantic_prosody_strength: float = DEFAULT_SEMANTIC_PROSODY_STRENGTH,
        humanization_strength: float = 0.0,
        has_previous_phrase: bool = False,
    ) -> Dict[str, Any]:
        """Build inspectable, safe delivery controls for one phrase with optional humanization."""
        active_direction = direction if semantic_direction else None
        strength = max(0.0, min(1.0, float(semantic_prosody_strength))) if semantic_direction else 0.0
        h_strength = max(0.0, min(1.0, float(humanization_strength)))

        rate, pitch, legacy_pause, tag = cls.calculate_phrase_parameters(
            phrase, profile, base_voice, phrase_index, total_phrases,
            energy_mode, pitch_depth, pacing_multiplier, pause_style, active_direction,
        )
        rate_value, pitch_value = _parse_edge_value(rate), _parse_edge_value(pitch)
        intent = active_direction.get("intent", "baseline") if active_direction else "baseline"
        volume, pause_before, pause_after = 0, 0, legacy_pause

        # A semantic label is only a small hint. It never forces a contour,
        # creates a new boundary, or changes an entire sentence into a new style.
        deltas = {
            "hook": (3, 3, 1, 10),
            "explanation": (0, 0, 0, 5),
            "emphasize": (-2, 3, 1, 15),
            "question": (1, 4, 1, 20),
            "conclusion": (-2, -3, 0, 25),
            "contrast": (-1, 3, 1, 20),
            "continuation": (2, 1, 0, -10),
            "baseline": (0, 0, 0, 0),
        }
        rate_delta, pitch_delta, volume_delta, pause_delta = deltas.get(intent, (0, 0, 0, 0))
        rate_value += round(rate_delta * strength)
        pitch_value += round(pitch_delta * strength)
        volume = round(volume_delta * strength)
        pause_before = 0
        pause_after += round(pause_delta * strength)

        # Humanization Layer: subtle conversational timing, contextual phrase endings,
        # and breath-group pause sizing around the baseline (0.0 = pure baseline).
        if h_strength > 0.0:
            # 1. Conversational Timing Variation:
            # - Focal thoughts and numbers are slightly more deliberate
            # - Simple connecting clauses flow slightly quicker
            if phrase.get("has_focus") or intent in ("emphasize", "contrast"):
                rate_value -= round(3 * h_strength)
            elif intent == "continuation" or not phrase.get("is_sentence_end"):
                rate_value += round(2 * h_strength)
            elif intent == "hook":
                rate_value += round(2 * h_strength)

            # 2. Contextual Phrase Ending Variation:
            if phrase.get("is_sentence_end"):
                is_last_phrase = (phrase_index == total_phrases - 1)
                if phrase.get("is_question") or intent == "question":
                    # Question ending: gentle anticipatory inflection
                    pitch_value += round(3 * h_strength)
                    pause_after += round(20 * h_strength)
                elif is_last_phrase or intent == "conclusion":
                    # Paragraph conclusion: authoritative grounding
                    pitch_value -= round(2 * h_strength)
                    pause_after += round(30 * h_strength)
                elif intent == "contrast":
                    # Contrast ending: attentive transition
                    pitch_value += round(2 * h_strength)
                    pause_after += round(20 * h_strength)
                else:
                    # Intermediate sentence continuation
                    pitch_value += round(1 * h_strength)
                    pause_after = max(200, min(280, pause_after))
            else:
                # Mid-sentence breath group: quick 65-90ms natural human breath
                pause_after = max(60, min(95, pause_after))

            # 3. Contrast Pre-Pause
            if intent == "contrast" and has_previous_phrase:
                pause_before = round(20 * h_strength)

        rate_value = _bounded(rate_value, "MIN_RATE", "MAX_RATE")
        pitch_value = _bounded(pitch_value, "MIN_PITCH", "MAX_PITCH")
        volume = _bounded(volume, "MIN_VOLUME", "MAX_VOLUME")
        pause_before = max(0, min(200, pause_before))
        pause_after = _bounded(pause_after, "MIN_PAUSE", "MAX_PAUSE")
        emphasis_words = focus_words(phrase["text"]) if intent == "emphasize" else []
        profile_name = profile.get("profile_id", "uploaded reference profile")
        profile_influence = f"{profile_name}; pace {profile.get('speaking_rate', {}).get('pace_multiplier', 1.0):.2f}x"
        return {
            "rate": f"+{rate_value}%" if rate_value >= 0 else f"{rate_value}%",
            "pitch": f"+{pitch_value}Hz" if pitch_value >= 0 else f"{pitch_value}Hz",
            "volume": f"+{volume}%" if volume >= 0 else f"{volume}%",
            "pause_before_ms": pause_before,
            "pause_after_ms": pause_after,
            "intent": intent,
            "tag": tag,
            "emphasis_words": emphasis_words,
            "reference_profile_influence": profile_influence,
            "direction_source": active_direction.get("source", "disabled") if active_direction else "disabled",
            "semantic_prosody_strength": strength,
            "humanization_strength": h_strength,
        }

    @staticmethod
    def synthesis_segments(text: str, baseline: Dict[str, Any], directed: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Preserve full phrase context; Edge TTS sounds best with complete phrases."""
        return [{"text": text, "delivery": directed, "kind": "full_phrase"}]

    @classmethod
    def apply_continuity_smoothing(
        cls,
        deliveries: List[Dict[str, Any]],
        max_pitch_delta: int = MAX_ADJACENT_PITCH_DELTA_HZ,
        max_rate_delta: int = MAX_ADJACENT_RATE_DELTA_PCT,
    ) -> List[Dict[str, Any]]:
        """
        Applies continuity-aware sequential smoothing across adjacent phrases.
        Prevents abrupt neural vocoder timbre/pitch cliffs while strictly preserving
        the communicative direction and relative dynamics.
        """
        if not deliveries:
            return deliveries

        smoothed = []
        prev_rate_val = None
        prev_pitch_val = None

        for idx, d in enumerate(deliveries):
            d_copy = dict(d)
            raw_rate = _parse_edge_value(d["rate"])
            raw_pitch = _parse_edge_value(d["pitch"])

            d_copy["raw_rate"] = d["rate"]
            d_copy["raw_pitch"] = d["pitch"]

            if idx == 0 or prev_rate_val is None:
                sm_rate = raw_rate
                sm_pitch = raw_pitch
            else:
                # Rate continuity constraint
                rate_diff = raw_rate - prev_rate_val
                if abs(rate_diff) > max_rate_delta:
                    sm_rate = prev_rate_val + (max_rate_delta if rate_diff > 0 else -max_rate_delta)
                else:
                    sm_rate = raw_rate

                # Pitch continuity constraint
                pitch_diff = raw_pitch - prev_pitch_val
                if abs(pitch_diff) > max_pitch_delta:
                    sm_pitch = prev_pitch_val + (max_pitch_delta if pitch_diff > 0 else -max_pitch_delta)
                else:
                    sm_pitch = raw_pitch

            sm_rate = _bounded(sm_rate, "MIN_RATE", "MAX_RATE")
            sm_pitch = _bounded(sm_pitch, "MIN_PITCH", "MAX_PITCH")

            d_copy["rate"] = f"+{sm_rate}%" if sm_rate >= 0 else f"{sm_rate}%"
            d_copy["pitch"] = f"+{sm_pitch}Hz" if sm_pitch >= 0 else f"{sm_pitch}Hz"
            d_copy["smoothed_rate"] = d_copy["rate"]
            d_copy["smoothed_pitch"] = d_copy["pitch"]

            prev_rate_val = sm_rate
            prev_pitch_val = sm_pitch
            smoothed.append(d_copy)

        return smoothed

    @classmethod
    def get_realtime_prosody_plan(
        cls,
        kannada_text: str,
        voice: str = "kn-IN-GaganNeural",
        energy_mode: str = "high_energy",
        pitch_depth: float = 1.0,
        pacing_multiplier: float = 1.0,
        pause_style: str = "snappy",
        prosody_profile: Optional[Dict[str, Any]] = None,
        semantic_direction: bool = True,
        semantic_prosody_strength: float = DEFAULT_SEMANTIC_PROSODY_STRENGTH,
        humanization_strength: float = DEFAULT_HUMANIZATION_STRENGTH,
    ) -> Dict[str, Any]:
        """
        Generates real-time segmented phrase blocks with live applied pitch, rate, and pause metadata.
        Uses KannadaPronunciationEngine to optimize pronunciation while preserving original display text.
        """
        if prosody_profile is None:
            prosody_profile = BUILTIN_EXPRESSIVE_PROFILE

        display_text, speech_text, transforms = KannadaPronunciationEngine.process_pronunciation(kannada_text.strip())
        actual_voice = "kn-IN-GaganNeural" if ("gagan" in voice.lower() or "male" in voice.lower()) else "kn-IN-SapnaNeural"
        target_aksharas = prosody_profile.get("phrasing", {}).get("target_phrase_aksharas", 12)
        phrases = cls.segment_kannada_text(speech_text, target_aksharas=target_aksharas)

        if not phrases:
            phrases = [{"text": speech_text, "is_sentence_end": True, "is_question": False, "is_exclamation": False, "has_focus": has_focus_entity(speech_text), "punct": ".", "pause_type": "long"}]

        # Preview always remains instant and deterministic; synthesis may replace
        # this with Groq's equivalent semantic classification when configured.
        direction_plan = SpeechDirector.local_plan(phrases)

        # 1. Compute raw phrase deliveries
        raw_deliveries = []
        valid_phrases = []
        for idx, p_info in enumerate(phrases):
            phrase_text = p_info["text"]
            if not phrase_text:
                continue
            delivery = cls.get_phrase_delivery(
                p_info, prosody_profile, actual_voice, idx, len(phrases),
                energy_mode, pitch_depth, pacing_multiplier, pause_style,
                direction_plan[idx], semantic_direction,
                semantic_prosody_strength=semantic_prosody_strength,
                humanization_strength=humanization_strength,
                has_previous_phrase=idx > 0,
            )
            raw_deliveries.append(delivery)
            valid_phrases.append(p_info)

        # 2. Apply continuity-aware sequential smoothing
        smoothed_deliveries = cls.apply_continuity_smoothing(raw_deliveries)

        plan = []
        total_estimated_ms = 0

        for idx, (p_info, delivery) in enumerate(zip(valid_phrases, smoothed_deliveries)):
            phrase_text = p_info["text"]
            akshara_count = count_aksharas(phrase_text)
            speed_val = (100 + _parse_edge_value(delivery["rate"])) / 100.0
            speech_ms = int((akshara_count / max(3.5, 7.5 * speed_val)) * 1000)
            total_estimated_ms += speech_ms + delivery["pause_before_ms"] + delivery["pause_after_ms"]

            plan.append({
                "phrase_index": idx + 1,
                "text": phrase_text,
                "aksharas": akshara_count,
                **delivery,
                "estimated_duration_sec": round(speech_ms / 1000.0, 2)
            })

        return {
            "display_text": display_text,
            "speech_text": speech_text,
            "voice": actual_voice,
            "energy_mode": energy_mode,
            "pitch_depth": pitch_depth,
            "pacing_multiplier": pacing_multiplier,
            "pause_style": pause_style,
            "semantic_direction": semantic_direction,
            "semantic_prosody_strength": max(0.0, min(1.0, float(semantic_prosody_strength))) if semantic_direction else 0.0,
            "humanization_strength": max(0.0, min(1.0, float(humanization_strength))),
            "prosody_limits": PROSODY_LIMITS,
            "continuity_constraints": {
                "max_adjacent_pitch_delta_hz": MAX_ADJACENT_PITCH_DELTA_HZ,
                "max_adjacent_rate_delta_pct": MAX_ADJACENT_RATE_DELTA_PCT,
            },
            "total_phrases": len(plan),
            "transformations_applied": len(transforms),
            "estimated_total_sec": round(total_estimated_ms / 1000.0, 2),
            "baseline_metrics": {
                "mean_pitch_hz": prosody_profile["pitch_dynamics"].get("mean_hz", 183.1),
                "median_pitch_hz": prosody_profile["pitch_dynamics"].get("median_hz", 180.1),
                "pitch_movement_hz": prosody_profile["pitch_dynamics"].get("pitch_movement_hz", 82.8),
                "mean_rms_db": prosody_profile["energy_and_punch"].get("mean_rms_db", -26.2),
                "dynamic_range_db": prosody_profile["energy_and_punch"].get("energy_dynamic_range_db", 27.1),
                "burst_rate_syl_sec": prosody_profile["speaking_rate"].get("burst_rate_syl_sec", 8.5)
            },
            "phrases": plan
        }

    @classmethod
    async def synthesize_with_delivery_style(
        cls,
        kannada_text: str,
        voice: str = "kn-IN-GaganNeural",
        energy_mode: str = "high_energy",
        pitch_depth: float = 1.0,
        pacing_multiplier: float = 1.0,
        pause_style: str = "snappy",
        prosody_profile: Optional[Dict[str, Any]] = None,
        semantic_direction: bool = True,
        semantic_prosody_strength: float = DEFAULT_SEMANTIC_PROSODY_STRENGTH,
        humanization_strength: float = DEFAULT_HUMANIZATION_STRENGTH,
        sample_rate: int = DEFAULT_SAMPLE_RATE,
        bitrate: str = DEFAULT_BITRATE,
    ) -> Tuple[bytes, Dict[str, Any]]:
        """
        Synthesizes Kannada text with expressive reference delivery while
        strictly preserving 100% of the selected speaker identity (Gagan / Sapna)
        and applying full pronunciation optimization layer.
        """
        import edge_tts

        if prosody_profile is None:
            prosody_profile = BUILTIN_EXPRESSIVE_PROFILE

        # 1. Pronunciation & Normalization Preprocessing
        display_text, speech_text, transforms = KannadaPronunciationEngine.process_pronunciation(kannada_text.strip())

        # 2. Speaker Voice Identity (Gagan or Sapna)
        actual_voice = "kn-IN-GaganNeural" if ("gagan" in voice.lower() or "male" in voice.lower()) else "kn-IN-SapnaNeural"

        # 3. Target phrase length based on reference breath-group
        target_aksharas = prosody_profile.get("phrasing", {}).get("target_phrase_aksharas", 32)
        phrases = cls.segment_kannada_text(speech_text, target_aksharas=target_aksharas)

        if not phrases:
            phrases = [{"text": speech_text, "is_sentence_end": True, "is_question": False, "is_exclamation": False, "has_focus": has_focus_entity(speech_text), "punct": ".", "pause_type": "long"}]

        # Direction is optional; the local plan is always available as a safe fallback.
        direction_plan = await SpeechDirector.direct(phrases) if semantic_direction else SpeechDirector.local_plan(phrases)

        # Compute raw deliveries
        raw_deliveries = []
        valid_phrases = []
        for idx, p_info in enumerate(phrases):
            phrase_text = p_info["text"]
            if not phrase_text:
                continue
            delivery = cls.get_phrase_delivery(
                p_info, prosody_profile, actual_voice, idx, len(phrases),
                energy_mode, pitch_depth, pacing_multiplier, pause_style,
                direction_plan[idx], semantic_direction,
                semantic_prosody_strength=semantic_prosody_strength,
                humanization_strength=humanization_strength,
                has_previous_phrase=idx > 0,
            )
            raw_deliveries.append(delivery)
            valid_phrases.append(p_info)

        # Apply continuity-aware sequential smoothing
        smoothed_deliveries = cls.apply_continuity_smoothing(raw_deliveries)

        temp_dir = tempfile.mkdtemp(prefix="dhvani_delivery_")
        pcm_chunks = []
        applied_plan = []
        sr = sample_rate

        try:
            for idx, (p_info, delivery) in enumerate(zip(valid_phrases, smoothed_deliveries)):
                phrase_text = p_info["text"]

                if delivery["pause_before_ms"]:
                    pcm_chunks.append(np.zeros(int((delivery["pause_before_ms"] / 1000.0) * sr), dtype=np.float32))

                local_segments = cls.synthesis_segments(phrase_text, delivery, delivery)
                for segment_index, segment in enumerate(local_segments):
                    mp3_path = os.path.join(temp_dir, f"chunk_{idx:03d}_{segment_index}.mp3")
                    wav_path = os.path.join(temp_dir, f"chunk_{idx:03d}_{segment_index}.wav")
                    controls = segment["delivery"]
                    communicate = edge_tts.Communicate(
                        text=segment["text"], voice=actual_voice,
                        pitch=controls["pitch"], rate=controls["rate"], volume=controls["volume"],
                    )
                    await communicate.save(mp3_path)
                    if shutil.which("afconvert"):
                        subprocess.run(["afconvert", "-f", "WAVE", "-d", f"LEI16@{sr}", "-c", "1", mp3_path, wav_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                    elif shutil.which("ffmpeg"):
                        subprocess.run(["ffmpeg", "-y", "-i", mp3_path, "-ac", "1", "-ar", str(sr), wav_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                    with wave.open(wav_path, "rb") as wf:
                        raw = wf.readframes(wf.getnframes())
                        data = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
                    pcm_chunks.append(trim_silence_pcm(data, sr=sr, thresh_db=-42.0, pad_ms=24))
                    if segment_index < len(local_segments) - 1:
                        pcm_chunks.append(np.zeros(int(0.11 * sr), dtype=np.float32))

                # Meaningful phrase pause insertion; timing follows semantic intent.
                if idx < len(valid_phrases) - 1:
                    pause_samples = int((delivery["pause_after_ms"] / 1000.0) * sr)
                    silence = np.zeros(pause_samples, dtype=np.float32)
                    pcm_chunks.append(silence)

                applied_plan.append({
                    "text": phrase_text,
                    **delivery,
                    "emphasis_segments": [{"text": s["text"], "kind": s["kind"]} for s in local_segments],
                })

            if not pcm_chunks:
                raise RuntimeError("No audio generated")

            # Combine all PCM chunks
            combined_audio = np.concatenate(pcm_chunks)

            # 4. Broadcast Audio Mastering (EQ Presence Boost + Dynamic Punch Saturation + Peak Normalization)
            energy_punch = prosody_profile.get("energy_and_punch", {}).get("energy_punch", 1.35)
            mastered_audio = apply_broadcast_mastering(combined_audio, sr=sr, punch=energy_punch)
            out_int16 = (mastered_audio * 32767).astype(np.int16)

            # Export combined audio as standard WAV
            out_wav_path = os.path.join(temp_dir, "combined.wav")
            with wave.open(out_wav_path, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sr)
                wf.writeframes(out_int16.tobytes())

            final_audio_path = out_wav_path
            if shutil.which("ffmpeg"):
                out_mp3_path = os.path.join(temp_dir, "combined.mp3")
                try:
                    subprocess.run(["ffmpeg", "-y", "-i", out_wav_path, "-b:a", bitrate, "-ar", str(sr), out_mp3_path],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                    final_audio_path = out_mp3_path
                except Exception:
                    pass

            with open(final_audio_path, "rb") as f:
                final_bytes = f.read()

            metadata = {
                "display_text": display_text,
                "speech_text": speech_text,
                "voice_used": actual_voice,
                "phrase_count": len(phrases),
                "energy_mode": energy_mode,
                "applied_plan": applied_plan,
                "transformations_applied": len(transforms),
                "overall_pace": prosody_profile.get("speaking_rate", {}).get("pace_syl_sec", 5.6),
                "dynamic_punch": round(energy_punch, 2),
                "speech_director": SpeechDirector.status(),
                "semantic_direction": semantic_direction,
                "semantic_prosody_strength": max(0.0, min(1.0, float(semantic_prosody_strength))) if semantic_direction else 0.0,
                "humanization_strength": max(0.0, min(1.0, float(humanization_strength))),
                "prosody_limits": PROSODY_LIMITS,
                "sample_rate": sr,
                "bitrate": bitrate,
                "duration_sec": round(len(out_int16) / sr, 2)
            }

            return final_bytes, metadata

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
