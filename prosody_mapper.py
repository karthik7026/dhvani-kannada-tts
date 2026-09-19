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
        "pace_syl_sec": 8.5,
        "pace_multiplier": 1.45,
        "burst_rate_syl_sec": 8.5,
        "speech_activity_ratio_pct": 73.4,
        "tempo_category": "High-Energy Presenter"
    },
    "pauses": {
        "detected_pauses_count": 34,
        "raw_median_ms": 140.0,
        "raw_p90_sec": 0.524,
        "short_breath_ms": 180,
        "anticipation_ms": 300,
        "sentence_boundary_ms": 500,
        "dramatic_emphasis_ms": 650,
        "video_cut_filter_active": True
    },
    "energy_and_punch": {
        "mean_rms_db": -26.2,
        "energy_dynamic_range_db": 27.1,
        "crest_factor_db": 17.5,
        "energy_punch": 1.45,
        "transition_contrast": "High Dynamic Range"
    },
    "phrasing": {
        "target_phrase_aksharas": 12,
        "median_breath_sec": 0.18,
        "p90_breath_sec": 0.50
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

# Connector delimiters for natural breathing boundaries
CONNECTOR_DELIMS = re.compile(r'([,;:—–]+|\s+ಮತ್ತು\s+|\s+ಹಾಗೆಯೇ\s+|\s+ಆದರೆ\s+|\s+ಇದರಿಂದ\s+|\s+ಅಲ್ಲದೆ\s+|\s+ಆದ್ದರಿಂದ\s+|\s+ಈಗ\s+|\s+ನೋಡಿ\s+)', re.UNICODE)

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

def trim_silence_pcm(samples: np.ndarray, sr: int = 24000, thresh_db: float = -38.0, pad_ms: int = 8) -> np.ndarray:
    """
    Trims leading and trailing silence from Edge-TTS generated audio chunk,
    leaving a clean 8ms safety margin for natural phonetic onset and decay.
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

def apply_broadcast_mastering(pcm_data: np.ndarray, sr: int = 24000, punch: float = 1.45) -> np.ndarray:
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
        pause_style: str = "snappy"
    ) -> Tuple[str, str, int, str]:
        """
        Maps reference prosody stats into expressive, dynamic Edge-TTS controls.
        Implements the 4-phase delivery cycle (Setup Burst ➔ Anticipation ➔ Focus Gravitas ➔ Statement Release).
        """
        rate_info = profile.get("speaking_rate", {})
        base_pace_mult = rate_info.get("pace_multiplier", 1.45) * pacing_multiplier

        # Energy Mode Profiles
        energy_offsets = {
            "calm": {"rate_delta": -14, "pitch_scale": 0.65, "pause_mult": 1.25, "tag": "Calm Narrator"},
            "balanced": {"rate_delta": 0, "pitch_scale": 0.85, "pause_mult": 1.10, "tag": "Balanced Explainer"},
            "high_energy": {"rate_delta": 6, "pitch_scale": 1.0, "pause_mult": 1.0, "tag": "High-Energy Presenter"},
            "dramatic": {"rate_delta": 10, "pitch_scale": 1.35, "pause_mult": 1.35, "tag": "Dramatic Climax"}
        }
        cfg = energy_offsets.get(energy_mode, energy_offsets["high_energy"])

        # Base presenter rate: ~+28% to +44%
        base_rate = int(max(18.0, min(42.0, (base_pace_mult - 1.0) * 80.0 + cfg["rate_delta"])))

        # Pause style baselines
        if pause_style == "snappy":
            base_setup_pause = 190
            base_anticipation_pause = 270
            base_focus_pause = 320
            base_sentence_pause = 500
        elif pause_style == "dramatic":
            base_setup_pause = 240
            base_anticipation_pause = 340
            base_focus_pause = 400
            base_sentence_pause = 620
        else: # balanced
            base_setup_pause = 210
            base_anticipation_pause = 290
            base_focus_pause = 350
            base_sentence_pause = 540

        is_male = ("gagan" in base_voice.lower() or "male" in base_voice.lower())
        p_scale = pitch_depth * cfg["pitch_scale"]

        is_question = phrase.get("is_question", False)
        is_exclamation = phrase.get("is_exclamation", False)
        is_sentence_end = phrase.get("is_sentence_end", False)
        has_focus = phrase.get("has_focus", False)

        # -------------------------------------------------------------
        # 4-PHASE DYNAMIC PROSODIC CYCLE
        # -------------------------------------------------------------
        if is_question:
            # 1. Rhetorical Question Peak (+38Hz to +46Hz)
            pitch_hz = int(round((38 if is_male else 46) * p_scale))
            applied_rate = min(44, base_rate + 6)
            pause_ms = int(base_sentence_pause * cfg["pause_mult"])
            tag = "❓ Rhetorical Question Peak"

        elif is_exclamation:
            # 2. Exclamatory Punch (+32Hz to +38Hz)
            pitch_hz = int(round((32 if is_male else 38) * p_scale))
            applied_rate = min(42, base_rate + 4)
            pause_ms = int(base_sentence_pause * 0.9 * cfg["pause_mult"])
            tag = "📢 Exclamatory Punch"

        elif has_focus and not is_sentence_end:
            # 3. Focus Entity Gravitas & Emphasis (+38Hz to +44Hz peak with deliberate tempo deceleration)
            pitch_hz = int(round((38 if is_male else 44) * p_scale))
            applied_rate = max(6, base_rate - 20) # Decelerate so numbers/entities hit with acoustic gravity
            pause_ms = int(base_focus_pause * cfg["pause_mult"])
            tag = "🎯 Focus Entity Gravitas"

        elif is_sentence_end:
            # 4. Punchy Falling Statement Cadence (-28Hz to -34Hz deep grounding)
            pitch_hz = int(round((-30 if is_male else -34) * p_scale))
            applied_rate = max(12, base_rate - 12)
            pause_ms = int(base_sentence_pause * cfg["pause_mult"])
            tag = "💥 Authoritative Cadence Fall"

        elif phrase_index == 0 or phrase_index % 3 == 0:
            # 5. Fast Setup Burst (+12Hz to +16Hz)
            pitch_hz = int(round((14 if is_male else 18) * p_scale))
            applied_rate = min(44, base_rate + 6)
            pause_ms = int(base_setup_pause * cfg["pause_mult"])
            tag = "⚡ Fast Setup Burst"

        else:
            # 6. Anticipation Climb (+24Hz to +30Hz)
            pitch_hz = int(round((26 if is_male else 30) * p_scale))
            applied_rate = base_rate
            pause_ms = int(base_anticipation_pause * cfg["pause_mult"])
            tag = "📈 Anticipation Build-Up"

        rate_str = f"+{applied_rate}%" if applied_rate >= 0 else f"{applied_rate}%"
        pitch_str = f"+{pitch_hz}Hz" if pitch_hz >= 0 else f"{pitch_hz}Hz"

        return rate_str, pitch_str, pause_ms, tag

    @classmethod
    def get_realtime_prosody_plan(
        cls,
        kannada_text: str,
        voice: str = "kn-IN-GaganNeural",
        energy_mode: str = "high_energy",
        pitch_depth: float = 1.0,
        pacing_multiplier: float = 1.0,
        pause_style: str = "snappy",
        prosody_profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generates real-time segmented phrase blocks with live applied pitch, rate, and pause metadata.
        """
        if prosody_profile is None:
            prosody_profile = BUILTIN_EXPRESSIVE_PROFILE

        norm_text = KannadaNormalizer.normalize(kannada_text.strip())
        actual_voice = "kn-IN-GaganNeural" if ("gagan" in voice.lower() or "male" in voice.lower()) else "kn-IN-SapnaNeural"
        target_aksharas = prosody_profile.get("phrasing", {}).get("target_phrase_aksharas", 12)
        phrases = cls.segment_kannada_text(norm_text, target_aksharas=target_aksharas)

        if not phrases:
            phrases = [{"text": norm_text, "is_sentence_end": True, "is_question": False, "is_exclamation": False, "has_focus": has_focus_entity(norm_text), "punct": ".", "pause_type": "long"}]

        plan = []
        total_estimated_ms = 0

        for idx, p_info in enumerate(phrases):
            phrase_text = p_info["text"]
            if not phrase_text:
                continue

            rate_str, pitch_str, pause_ms, tag = cls.calculate_phrase_parameters(
                p_info, prosody_profile, actual_voice,
                phrase_index=idx, total_phrases=len(phrases),
                energy_mode=energy_mode, pitch_depth=pitch_depth,
                pacing_multiplier=pacing_multiplier, pause_style=pause_style
            )

            akshara_count = count_aksharas(phrase_text)
            speed_val = (100 + int(rate_str.replace('%', ''))) / 100.0
            speech_ms = int((akshara_count / max(3.5, 7.5 * speed_val)) * 1000)
            total_estimated_ms += speech_ms + pause_ms

            plan.append({
                "phrase_index": idx + 1,
                "text": phrase_text,
                "aksharas": akshara_count,
                "pitch": pitch_str,
                "rate": rate_str,
                "pause_after_ms": pause_ms,
                "tag": tag,
                "estimated_duration_sec": round(speech_ms / 1000.0, 2)
            })

        return {
            "voice": actual_voice,
            "energy_mode": energy_mode,
            "pitch_depth": pitch_depth,
            "pacing_multiplier": pacing_multiplier,
            "pause_style": pause_style,
            "total_phrases": len(plan),
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
        prosody_profile: Optional[Dict[str, Any]] = None
    ) -> Tuple[bytes, Dict[str, Any]]:
        """
        Synthesizes Kannada text with expressive reference delivery while
        strictly preserving 100% of the selected speaker identity (Gagan / Sapna).
        """
        import edge_tts

        if prosody_profile is None:
            prosody_profile = BUILTIN_EXPRESSIVE_PROFILE

        # 1. Normalize text
        norm_text = KannadaNormalizer.normalize(kannada_text.strip())

        # 2. Speaker Voice Identity (Gagan or Sapna)
        actual_voice = "kn-IN-GaganNeural" if ("gagan" in voice.lower() or "male" in voice.lower()) else "kn-IN-SapnaNeural"

        # 3. Target phrase length based on reference breath-group
        target_aksharas = prosody_profile.get("phrasing", {}).get("target_phrase_aksharas", 12)
        phrases = cls.segment_kannada_text(norm_text, target_aksharas=target_aksharas)

        if not phrases:
            phrases = [{"text": norm_text, "is_sentence_end": True, "is_question": False, "is_exclamation": False, "has_focus": has_focus_entity(norm_text), "punct": ".", "pause_type": "long"}]

        temp_dir = tempfile.mkdtemp(prefix="dhvani_delivery_")
        pcm_chunks = []
        applied_plan = []
        sr = 24000

        try:
            for idx, p_info in enumerate(phrases):
                phrase_text = p_info["text"]
                if not phrase_text:
                    continue

                rate_str, pitch_str, pause_ms, tag = cls.calculate_phrase_parameters(
                    p_info, prosody_profile, actual_voice,
                    phrase_index=idx, total_phrases=len(phrases),
                    energy_mode=energy_mode, pitch_depth=pitch_depth,
                    pacing_multiplier=pacing_multiplier, pause_style=pause_style
                )

                mp3_path = os.path.join(temp_dir, f"chunk_{idx:03d}.mp3")
                wav_path = os.path.join(temp_dir, f"chunk_{idx:03d}.wav")

                communicate = edge_tts.Communicate(
                    text=phrase_text,
                    voice=actual_voice,
                    pitch=pitch_str,
                    rate=rate_str
                )
                await communicate.save(mp3_path)

                # Convert to PCM wav using afconvert (macOS) or ffmpeg
                if shutil.which("afconvert"):
                    subprocess.run(["afconvert", "-f", "WAVE", "-d", "LEI16@24000", "-c", "1", mp3_path, wav_path],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                elif shutil.which("ffmpeg"):
                    subprocess.run(["ffmpeg", "-y", "-i", mp3_path, "-ac", "1", "-ar", "24000", wav_path],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

                with wave.open(wav_path, "rb") as wf:
                    raw = wf.readframes(wf.getnframes())
                    data = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0

                # Silence trimming on each phrase
                trimmed_data = trim_silence_pcm(data, sr=sr, thresh_db=-38.0, pad_ms=8)
                pcm_chunks.append(trimmed_data)

                # Breath pause insertion between phrases
                if idx < len(phrases) - 1:
                    pause_samples = int((pause_ms / 1000.0) * sr)
                    silence = np.zeros(pause_samples, dtype=np.float32)
                    pcm_chunks.append(silence)

                applied_plan.append({
                    "phrase": phrase_text,
                    "pitch": pitch_str,
                    "rate": rate_str,
                    "pause_after_ms": pause_ms,
                    "tag": tag
                })

            if not pcm_chunks:
                raise RuntimeError("No audio generated")

            # Combine all PCM chunks
            combined_audio = np.concatenate(pcm_chunks)

            # 4. Broadcast Audio Mastering (EQ Presence Boost + Dynamic Punch Saturation + Peak Normalization)
            energy_punch = prosody_profile.get("energy_and_punch", {}).get("energy_punch", 1.45)
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
                    subprocess.run(["ffmpeg", "-y", "-i", out_wav_path, "-b:a", "192k", out_mp3_path],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                    final_audio_path = out_mp3_path
                except Exception:
                    pass

            with open(final_audio_path, "rb") as f:
                final_bytes = f.read()

            metadata = {
                "voice_used": actual_voice,
                "phrase_count": len(phrases),
                "energy_mode": energy_mode,
                "applied_plan": applied_plan,
                "overall_pace": prosody_profile.get("speaking_rate", {}).get("pace_syl_sec", 8.5),
                "dynamic_punch": round(energy_punch, 2),
                "duration_sec": round(len(out_int16) / sr, 2)
            }

            return final_bytes, metadata

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
