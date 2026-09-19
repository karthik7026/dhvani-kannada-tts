#!/usr/bin/env python3
"""
Kannada Prosody Mapper (ಕನ್ನಡ ಧ್ವನಿ ವಿತರಣಾ ಮ್ಯಾಪರ್) - High-Impact Expressive Presenter Engine
Maps language-agnostic ProsodyProfile delivery statistics onto Kannada text structures
using akshara-aware phrase segmentation, dynamic pitch/speed inflections, silence-trimmed breath pauses,
and broadcast mastering while strictly preserving 100% of the speaker voice identity (Gagan / Sapna).
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

# Built-in expressive delivery, measured from the high-energy reference presenter recording.
# Controls prosody only: no speaker timbre/embedding is modified.
BUILTIN_EXPRESSIVE_PROFILE: Dict[str, Any] = {
    "profile_id": "builtin_expressive_v2",
    "speaking_rate": {"pace_syl_sec": 8.5, "pace_multiplier": 1.45, "tempo_category": "Fast Presenter"},
    "pitch_dynamics": {"median_hz": 187.5, "range_hz": 78.3, "span_semitones": 7.34, "ending_slope": "neutral_cadence"},
    "pauses": {"count": 57, "median_ms": 130.0, "p90_ms": 680.0, "pause_ratio_pct": 49.2,
               "distribution": {"short_pct": 71.9, "medium_pct": 14.0, "long_pct": 14.0}},
    "energy_and_punch": {"crest_factor_db": 25.3, "energy_punch": 1.44, "transition_contrast": "High Dynamic Range"},
    "phrasing": {"target_phrase_aksharas": 16, "median_breath_sec": 0.07, "p90_breath_sec": 0.19},
}

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

def trim_silence_pcm(samples: np.ndarray, sr: int = 24000, thresh_db: float = -38.0, pad_ms: int = 15) -> np.ndarray:
    """
    Trims leading and trailing silence from Edge-TTS generated audio chunk,
    leaving a clean 15ms safety margin for natural phonetic onset and decay.
    """
    if len(samples) == 0:
        return samples
    abs_samples = np.abs(samples)
    peak = np.max(abs_samples)
    if peak < 1e-4:
        return samples

    thresh = peak * (10.0 ** (thresh_db / 20.0))
    win_len = int(0.010 * sr) # 10ms window
    pad_samples = int((pad_ms / 1000.0) * sr)

    kernel = np.ones(win_len) / win_len
    energy = np.convolve(abs_samples, kernel, mode='same')

    above = np.where(energy > thresh)[0]
    if len(above) == 0:
        return samples

    start_idx = max(0, above[0] - pad_samples)
    end_idx = min(len(samples), above[-1] + pad_samples)
    return samples[start_idx:end_idx]

def apply_broadcast_mastering(pcm_data: np.ndarray, sr: int = 24000, punch: float = 1.35) -> np.ndarray:
    """
    Applies professional vocal mastering:
    1. 3.2kHz Peaking EQ (+3.2 dB vocal presence boost for speech intelligibility)
    2. Tanh soft-knee dynamic punch compressor (upfront YouTube presenter presence)
    3. True-peak broadcast normalization to -0.5 dBFS (0.95 peak)
    """
    if len(pcm_data) == 0:
        return pcm_data

    # 1. 3.2 kHz Vocal Presence EQ (2nd order biquad peaking filter)
    f0 = 3200.0
    Q = 1.0
    gain_db = 3.2
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
    boosted = filtered * max(1.0, min(1.6, punch))
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
    with dynamic pitch excursion, high-energy presenter rhythm, and snappy breath pauses.
    """

    @classmethod
    def segment_kannada_text(cls, text: str, target_aksharas: int = 14) -> List[Dict[str, Any]]:
        """
        Segments Kannada text into breath-group phrases with contextual sentence-ending metadata.
        """
        # First split into sentences by major punctuation
        sentence_chunks = re.split(r'([.?!।॥\n]+)', text)
        phrases = []

        for i in range(0, len(sentence_chunks), 2):
            sent_text = sentence_chunks[i].strip()
            punct = sentence_chunks[i+1].strip() if i+1 < len(sentence_chunks) else "."
            if not sent_text:
                continue

            # Check if sentence is question, exclamation, or statement
            is_question = "?" in punct or any(w in sent_text for w in ["ಯಾಕೆ", "ಹೇಗೆ", "ಏನು", "ಎಲ್ಲಿ", "ಯಾರು", "ಯಾವಾಗ", "ಎಷ್ಟು"])
            is_exclamation = "!" in punct

            # Split within sentence if longer than target_aksharas
            comma_parts = re.split(r'([,;:—–]+)', sent_text)
            curr_acc = ""

            for part in comma_parts:
                if not part.strip():
                    continue
                if re.match(r'[,;:—–]+', part):
                    if curr_acc:
                        phrases.append({
                            "text": curr_acc.strip(),
                            "is_sentence_end": False,
                            "is_question": False,
                            "is_exclamation": False,
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
        total_phrases: int = 1
    ) -> Tuple[str, str, int]:
        """
        Maps reference prosody stats into expressive, dynamic Edge-TTS controls.
        Applies dramatic pitch swings, fast presenter pacing, and crisp breath pauses.
        """
        rate_info = profile.get("speaking_rate", {})
        pace_multiplier = rate_info.get("pace_multiplier", 1.35)

        # Base presenter rate: +28% to +38% for lively YouTube/Podcast tempo
        base_rate = int(max(26.0, min(38.0, (pace_multiplier - 1.0) * 80.0 + 6.0)))

        # Dynamic pitch variation based on phrase context
        if phrase.get("is_question"):
            # Strong rising inflection for rhetorical questions (+18Hz to +22Hz)
            phrase_pitch_hz = 18 if "gagan" in base_voice.lower() else 22
            applied_rate = min(42, base_rate + 6)
            pause_ms = 180
        elif phrase.get("is_exclamation"):
            # Energetic assertion / punch (+14Hz to +18Hz)
            phrase_pitch_hz = 14 if "gagan" in base_voice.lower() else 18
            applied_rate = min(40, base_rate + 4)
            pause_ms = 190
        elif phrase.get("is_sentence_end"):
            # Punchy falling termination (-10Hz to -14Hz)
            phrase_pitch_hz = -12 if "gagan" in base_voice.lower() else -8
            applied_rate = base_rate
            pause_ms = 200
        else:
            # Rhythmic alternating cadence across continuing clauses
            if phrase_index % 2 == 0:
                phrase_pitch_hz = 8 if "gagan" in base_voice.lower() else 10
                applied_rate = base_rate + 3
            else:
                phrase_pitch_hz = -2 if "gagan" in base_voice.lower() else 0
                applied_rate = base_rate - 2
            pause_ms = 80

        rate_str = f"+{applied_rate}%" if applied_rate >= 0 else f"{applied_rate}%"
        pitch_str = f"+{phrase_pitch_hz}Hz" if phrase_pitch_hz >= 0 else f"{phrase_pitch_hz}Hz"

        return rate_str, pitch_str, pause_ms

    @classmethod
    async def synthesize_with_delivery_style(
        cls,
        kannada_text: str,
        voice: str = "kn-IN-GaganNeural",
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
        target_aksharas = prosody_profile.get("phrasing", {}).get("target_phrase_aksharas", 14)
        phrases = cls.segment_kannada_text(norm_text, target_aksharas=target_aksharas)

        if not phrases:
            phrases = [{"text": norm_text, "is_sentence_end": True, "is_question": False, "is_exclamation": False, "punct": ".", "pause_type": "long"}]

        temp_dir = tempfile.mkdtemp(prefix="dhvani_delivery_")
        pcm_chunks = []
        applied_plan = []
        sr = 24000

        try:
            for idx, p_info in enumerate(phrases):
                phrase_text = p_info["text"]
                if not phrase_text:
                    continue

                rate_str, pitch_str, pause_ms = cls.calculate_phrase_parameters(
                    p_info, prosody_profile, actual_voice, phrase_index=idx, total_phrases=len(phrases)
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
                trimmed_data = trim_silence_pcm(data, sr=sr, thresh_db=-38.0, pad_ms=15)
                pcm_chunks.append(trimmed_data)

                # Snappy breath pause insertion between phrases
                if idx < len(phrases) - 1:
                    pause_samples = int((pause_ms / 1000.0) * sr)
                    silence = np.zeros(pause_samples, dtype=np.float32)
                    pcm_chunks.append(silence)

                applied_plan.append({
                    "phrase": phrase_text,
                    "pitch": pitch_str,
                    "rate": rate_str,
                    "pause_after_ms": pause_ms
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
                "applied_plan": applied_plan,
                "overall_pace": prosody_profile.get("speaking_rate", {}).get("pace_syl_sec", 8.5),
                "dynamic_punch": round(energy_punch, 2),
                "duration_sec": round(len(out_int16) / sr, 2)
            }

            return final_bytes, metadata

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
