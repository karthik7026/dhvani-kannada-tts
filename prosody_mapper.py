#!/usr/bin/env python3
"""
Kannada Prosody Mapper (ಕನ್ನಡ ಧ್ವನಿ ವಿತರಣಾ ಮ್ಯಾಪರ್)
Maps language-agnostic ProsodyProfile delivery statistics onto Kannada text structures
using safe, clamped Edge-TTS controls (rate, pitch contours, pause durations, emphasis)
while preserving 100% of the speaker voice identity (Gagan / Sapna).
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

try:
    from kannada_normalizer import KannadaNormalizer
except ImportError:
    class KannadaNormalizer:
        @staticmethod
        def normalize(t): return t

# Built-in expressive delivery, measured from the user-provided high-quality
# reference recording (30-second analysis). It controls prosody only: no
# speaker embedding, voice identity, or audio samples are reused at synthesis.
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

class KannadaProsodyMapper:
    """
    Translates statistical Delivery Prosody into Kannada phrase-level TTS parameters.
    """

    @classmethod
    def segment_kannada_text(cls, text: str, target_aksharas: int = 12) -> List[Dict[str, Any]]:
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
            is_question = "?" in punct or any(w in sent_text for w in ["ಯಾಕೆ", "ಹೇಗೆ", "ಏನು", "ಎಲ್ಲಿ", "ಯಾರು"])
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
        base_voice: str
    ) -> Tuple[str, str, int]:
        """
        Maps reference prosody stats into safe, natural Edge-TTS pitch and rate tags.
        Guarantees speaker identity is strictly preserved.
        """
        rate_info = profile.get("speaking_rate", {})
        pace_multiplier = rate_info.get("pace_multiplier", 1.25)
        
        # Safe Clamped Rate: [-10%, +30%]
        rate_delta_raw = (pace_multiplier - 1.0) * 100.0
        applied_rate_delta = int(np.clip(rate_delta_raw, -10.0, 30.0))
        
        # Pitch adjustments: Safe Clamped [-4Hz, +5Hz]
        # Never alter base voice pitch beyond natural speech inflections
        if phrase.get("is_question"):
            # Rising inflection for questions
            phrase_pitch_hz = 3
            # Slightly faster pace on questions
            applied_rate_delta = min(30, applied_rate_delta + 4)
        elif phrase.get("is_exclamation"):
            # High energy punch
            phrase_pitch_hz = 2
            applied_rate_delta = min(30, applied_rate_delta + 2)
        elif phrase.get("is_sentence_end"):
            # Punchy falling termination (typical of energetic news/explainers)
            ending_slope = profile.get("pitch_dynamics", {}).get("ending_slope", "falling_punchy")
            phrase_pitch_hz = -3 if ending_slope == "falling_punchy" else 0
        else:
            # Mid-sentence continuation
            phrase_pitch_hz = 1

        rate_str = f"+{applied_rate_delta}%" if applied_rate_delta >= 0 else f"{applied_rate_delta}%"
        pitch_str = f"+{phrase_pitch_hz}Hz" if phrase_pitch_hz >= 0 else f"{phrase_pitch_hz}Hz"

        # Pause duration calculation
        pauses_info = profile.get("pauses", {})
        if phrase.get("pause_type") == "long":
            pause_ms = int(np.clip(pauses_info.get("p90_ms", 450.0) * 0.8, 300, 550))
        else:
            pause_ms = int(np.clip(pauses_info.get("median_ms", 150.0), 120, 220))

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
        strictly preserving the configured speaker identity (Gagan/Sapna).
        """
        import edge_tts

        if prosody_profile is None:
            prosody_profile = BUILTIN_EXPRESSIVE_PROFILE

        # 1. Normalize text
        norm_text = KannadaNormalizer.normalize(kannada_text.strip())

        # 2. Speaker Voice Identity (Gagan or Sapna)
        actual_voice = "kn-IN-GaganNeural" if ("gagan" in voice.lower() or "male" in voice.lower()) else "kn-IN-SapnaNeural"

        # The built-in style must remain a single Edge utterance. Splitting a
        # sentence into many tiny requests makes Edge add end-of-utterance
        # silence to every word-sized fragment, which sounds like 2–3 s gaps.
        if prosody_profile is None or prosody_profile.get("profile_id") == "builtin_expressive_v2":
            import edge_tts

            # Apply measured delivery to one complete utterance. The 45%
            # reference pace multiplier is softened to Edge's natural range;
            # splitting at every breath group would add artificial silence.
            reference_rate = prosody_profile["speaking_rate"]["pace_multiplier"]
            rate_delta = int(np.clip(round((reference_rate - 1.0) * 45), 0, 20))
            rate = f"+{rate_delta}%"
            # Keep each selected voice recognisable while transferring the
            # reference's more animated contour and energetic delivery.
            pitch = "-3Hz" if actual_voice == "kn-IN-GaganNeural" else "+2Hz"
            communicate = edge_tts.Communicate(
                text=norm_text,
                voice=actual_voice,
                pitch=pitch,
                rate=rate,
                volume="+3%",
            )
            audio_buffer = io.BytesIO()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_buffer.write(chunk["data"])
            audio_bytes = audio_buffer.getvalue()
            if not audio_bytes:
                raise RuntimeError("No audio generated")
            return audio_bytes, {
                "voice_used": actual_voice,
                "phrase_count": 1,
                "applied_plan": [{"phrase": norm_text, "pitch": pitch, "rate": rate, "pause_after_ms": 0}],
                "overall_pace": prosody_profile["speaking_rate"]["pace_syl_sec"],
                "dynamic_punch": prosody_profile["energy_and_punch"]["energy_punch"],
                "duration_sec": 0.0,
            }

        # 3. Target phrase length based on an uploaded reference breath-group
        target_aksharas = prosody_profile.get("phrasing", {}).get("target_phrase_aksharas", 12)
        phrases = cls.segment_kannada_text(norm_text, target_aksharas=target_aksharas)

        temp_dir = tempfile.mkdtemp(prefix="dhvani_delivery_")
        pcm_chunks = []
        applied_plan = []
        sr = 24000

        try:
            for idx, p_info in enumerate(phrases):
                phrase_text = p_info["text"]
                if not phrase_text:
                    continue

                rate_str, pitch_str, pause_ms = cls.calculate_phrase_parameters(p_info, prosody_profile, actual_voice)
                
                mp3_path = os.path.join(temp_dir, f"chunk_{idx:03d}.mp3")
                wav_path = os.path.join(temp_dir, f"chunk_{idx:03d}.wav")

                communicate = edge_tts.Communicate(
                    text=phrase_text,
                    voice=actual_voice,
                    pitch=pitch_str,
                    rate=rate_str
                )
                await communicate.save(mp3_path)

                # Convert to PCM wav
                if shutil.which("afconvert"):
                    subprocess.run(["afconvert", "-f", "WAVE", "-d", "LEI16@24000", "-c", "1", mp3_path, wav_path],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                elif shutil.which("ffmpeg"):
                    subprocess.run(["ffmpeg", "-y", "-i", mp3_path, "-ac", "1", "-ar", "24000", wav_path],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

                with wave.open(wav_path, "rb") as wf:
                    raw = wf.readframes(wf.getnframes())
                    data = np.frombuffer(raw, dtype=np.int16)
                    pcm_chunks.append(data)

                # Silence pause insertion
                if idx < len(phrases) - 1:
                    pause_samples = int((pause_ms / 1000.0) * sr)
                    silence = np.zeros(pause_samples, dtype=np.int16)
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
            combined_audio = np.concatenate(pcm_chunks).astype(np.float32) / 32768.0

            # 4. Mastered Broadcast Levelling (Preserves Voice Identity, Adds Broadcast Punch)
            energy_punch = prosody_profile.get("energy_and_punch", {}).get("energy_punch", 1.25)
            mastered = np.tanh(combined_audio * min(1.4, max(1.0, energy_punch * 0.95)))
            mastered = mastered / (np.max(np.abs(mastered)) + 1e-6) * 0.96
            out_int16 = (mastered * 32767).astype(np.int16)

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
                "overall_pace": prosody_profile.get("speaking_rate", {}).get("pace_syl_sec", 6.65),
                "dynamic_punch": round(energy_punch, 2),
                "duration_sec": round(len(out_int16) / sr, 2)
            }

            return final_bytes, metadata

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
