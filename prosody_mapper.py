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

# Measured baseline delivery profile from the high-energy reference presenter video.
# Filters out video editing/B-roll cuts and models distinct speech bursts, pitch dynamics,
# and pause distributions.
BUILTIN_EXPRESSIVE_PROFILE: Dict[str, Any] = {
    "profile_id": "youtube_presenter_v3",
    "pitch_dynamics": {
        "mean_hz": 162.1,
        "median_hz": 157.1,
        "p10_hz": 123.3,
        "p90_hz": 206.2,
        "pitch_movement_hz": 82.9,
        "span_semitones": 8.92,
        "ending_slope": "punchy_falling"
    },
    "speaking_rate": {
        "pace_syl_sec": 8.5,
        "pace_multiplier": 1.45,
        "burst_rate_syl_sec": 8.5,
        "speech_activity_ratio_pct": 45.5,
        "tempo_category": "Ultra-Fast Presenter"
    },
    "pauses": {
        "detected_pauses_count": 575,
        "raw_median_ms": 448.0,
        "raw_p90_sec": 1.12,
        "short_breath_ms": 80,
        "sentence_boundary_ms": 190,
        "dramatic_emphasis_ms": 450,
        "video_cut_filter_active": True
    },
    "energy_and_punch": {
        "mean_rms_db": -23.9,
        "energy_dynamic_range_db": 26.3,
        "crest_factor_db": 24.8,
        "energy_punch": 1.45,
        "transition_contrast": "High Dynamic Range"
    },
    "phrasing": {
        "target_phrase_aksharas": 14,
        "median_breath_sec": 0.08,
        "p90_breath_sec": 0.22
    }
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
        total_phrases: int = 1,
        energy_mode: str = "high_energy",
        pitch_depth: float = 1.0,
        pacing_multiplier: float = 1.0,
        pause_style: str = "snappy"
    ) -> Tuple[str, str, int, str]:
        """
        Maps reference prosody stats into expressive, dynamic Edge-TTS controls.
        Supports real-time energy section modes, pitch excursion depth, and pause styling.
        """
        rate_info = profile.get("speaking_rate", {})
        base_pace_mult = rate_info.get("pace_multiplier", 1.35) * pacing_multiplier

        # Energy Mode Profiles
        energy_offsets = {
            "calm": {"rate_delta": -12, "pitch_scale": 0.6, "pause_mult": 1.3, "tag": "Calm Narrator"},
            "balanced": {"rate_delta": 0, "pitch_scale": 0.85, "pause_mult": 1.1, "tag": "Balanced Explainer"},
            "high_energy": {"rate_delta": 8, "pitch_scale": 1.0, "pause_mult": 0.9, "tag": "High-Energy Presenter"},
            "dramatic": {"rate_delta": 14, "pitch_scale": 1.35, "pause_mult": 1.4, "tag": "Dramatic Climax"}
        }
        cfg = energy_offsets.get(energy_mode, energy_offsets["high_energy"])

        # Base presenter rate: +26% to +44%
        base_rate = int(max(18.0, min(44.0, (base_pace_mult - 1.0) * 80.0 + cfg["rate_delta"])))

        # Pause style baselines
        if pause_style == "snappy":
            base_short_pause = 75
            base_sentence_pause = 180
            base_dramatic_pause = 380
        elif pause_style == "dramatic":
            base_short_pause = 140
            base_sentence_pause = 300
            base_dramatic_pause = 600
        else: # balanced
            base_short_pause = 100
            base_sentence_pause = 240
            base_dramatic_pause = 450

        p_scale = pitch_depth * cfg["pitch_scale"]

        # Dynamic pitch & rhythm variation based on phrase context
        if phrase.get("is_question"):
            # Strong rising inflection for rhetorical questions (+18Hz to +24Hz)
            pitch_hz = int(round((18 if "gagan" in base_voice.lower() else 22) * p_scale))
            applied_rate = min(44, base_rate + 6)
            pause_ms = int(base_sentence_pause * cfg["pause_mult"])
            tag = "❓ Rhetorical Question Rise"
        elif phrase.get("is_exclamation"):
            # Energetic assertion / punch (+14Hz to +18Hz)
            pitch_hz = int(round((14 if "gagan" in base_voice.lower() else 18) * p_scale))
            applied_rate = min(42, base_rate + 4)
            pause_ms = int(base_sentence_pause * cfg["pause_mult"])
            tag = "📢 Exclamatory Assertion"
        elif phrase.get("is_sentence_end"):
            # Punchy falling termination (-10Hz to -14Hz)
            pitch_hz = int(round((-12 if "gagan" in base_voice.lower() else -8) * p_scale))
            applied_rate = base_rate
            pause_ms = int(base_sentence_pause * cfg["pause_mult"])
            tag = "💥 Punchy Falling Cadence"
        else:
            # Rhythmic alternating cadence across continuing clauses
            if phrase_index % 2 == 0:
                pitch_hz = int(round((8 if "gagan" in base_voice.lower() else 10) * p_scale))
                applied_rate = base_rate + 3
                tag = "⚡ Rising Clause Build-Up"
            else:
                pitch_hz = int(round((-2 if "gagan" in base_voice.lower() else 0) * p_scale))
                applied_rate = base_rate - 2
                tag = "🌊 Melodic Clause Flow"
            pause_ms = int(base_short_pause * cfg["pause_mult"])

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
        target_aksharas = prosody_profile.get("phrasing", {}).get("target_phrase_aksharas", 14)
        phrases = cls.segment_kannada_text(norm_text, target_aksharas=target_aksharas)

        if not phrases:
            phrases = [{"text": norm_text, "is_sentence_end": True, "is_question": False, "is_exclamation": False, "punct": ".", "pause_type": "long"}]

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
            # Estimate speech duration based on pace
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
                "mean_pitch_hz": prosody_profile["pitch_dynamics"].get("mean_hz", 162.1),
                "median_pitch_hz": prosody_profile["pitch_dynamics"].get("median_hz", 157.1),
                "pitch_movement_hz": prosody_profile["pitch_dynamics"].get("pitch_movement_hz", 82.9),
                "mean_rms_db": prosody_profile["energy_and_punch"].get("mean_rms_db", -23.9),
                "dynamic_range_db": prosody_profile["energy_and_punch"].get("energy_dynamic_range_db", 26.3),
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
