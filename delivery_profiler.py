#!/usr/bin/env python3
"""
Acoustic Delivery Profiler (ಧ್ವನಿ ವಿತರಣಾ ಪ್ರೊಫೈಲರ್)
Extracts statistical speaking style & prosody characteristics from reference audio:
- Pitch movement, range, variance, and sentence-ending inflections
- Speaking rate (syllables / second)
- Short / Medium / Long pause distributions
- Energy / RMS variation, crest factor, and dynamic punch
- Breath-group and phrase length statistics
"""

import io
import os
import math
import wave
import struct
import shutil
import tempfile
import hashlib
import subprocess
import numpy as np
import soundfile as sf
from typing import Dict, Any, List, Optional, Tuple

# In-memory cache for extracted ProsodyProfiles: { audio_hash: profile_dict }
PROSODY_PROFILE_CACHE: Dict[str, Dict[str, Any]] = {}

def _audio_suffix(audio_bytes: bytes) -> str:
    """Infer a usable file suffix when an HTTP upload has no reliable path."""
    header = audio_bytes[:16]
    if header.startswith(b"RIFF") and header[8:12] == b"WAVE":
        return ".wav"
    if header.startswith(b"ID3") or header[:2] in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"):
        return ".mp3"
    if header[4:8] == b"ftyp":
        return ".m4a"
    return ".audio"

def decode_audio_to_pcm(
    audio_bytes: bytes, target_sr: int = 24000, max_duration_sec: Optional[float] = None
) -> Tuple[List[float], int, float]:
    """
    Decodes audio bytes (MP3/WAV/AAC/M4A) into mono PCM samples [-1.0, 1.0].
    SoundFile is preferred because upload bytes do not retain a system-recognised
    filename; afconvert/ffmpeg remain fallbacks for codecs it cannot read.
    """
    with tempfile.NamedTemporaryFile(suffix=_audio_suffix(audio_bytes), delete=False) as in_f:
        in_f.write(audio_bytes)
        in_path = in_f.name

    out_wav_path = in_path + ".wav"
    try:
        try:
            with sf.SoundFile(in_path) as source:
                source_sr = source.samplerate
                total_duration_sec = len(source) / source_sr
                frames = len(source)
                if max_duration_sec is not None:
                    frames = min(frames, int(max_duration_sec * source_sr))
                decoded = source.read(frames=frames, dtype="float32", always_2d=True)

            mono = decoded.mean(axis=1)
            if source_sr != target_sr and len(mono) > 1:
                output_size = max(1, round(len(mono) * target_sr / source_sr))
                positions = np.linspace(0, len(mono) - 1, output_size)
                mono = np.interp(positions, np.arange(len(mono)), mono).astype(np.float32)
            return mono.tolist(), target_sr, total_duration_sec
        except (RuntimeError, OSError, ValueError):
            pass

        if shutil.which("afconvert"):
            subprocess.run([
                "afconvert", "-f", "WAVE", "-d", f"LEI16@{target_sr}", "-c", "1",
                in_path, out_wav_path
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        elif shutil.which("ffmpeg"):
            subprocess.run([
                "ffmpeg", "-y", "-i", in_path, "-ac", "1", "-ar", str(target_sr),
                out_wav_path
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        else:
            # Try raw wave read
            shutil.copy(in_path, out_wav_path)

        with wave.open(out_wav_path, "rb") as wf:
            n_frames = wf.getnframes()
            sr = wf.getframerate()
            raw = wf.readframes(n_frames)
            
        # Unpack int16 to float [-1.0, 1.0]
        count = len(raw) // 2
        ints = struct.unpack(f"<{count}h", raw)
        samples = [val / 32768.0 for val in ints]
        return samples, sr, len(samples) / sr
    finally:
        for p in [in_path, out_wav_path]:
            if os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass

class DeliveryProfiler:
    """
    Analyzes reference audio files (Telugu, Kannada, English, etc.)
    and computes a language-agnostic ProsodyProfile for TTS delivery steering.
    """

    @staticmethod
    def get_audio_hash(audio_bytes: bytes) -> str:
        return hashlib.sha256(audio_bytes).hexdigest()

    @classmethod
    def extract_prosody_profile(cls, audio_bytes: bytes, max_duration_sec: float = 60.0) -> Dict[str, Any]:
        """
        Extracts statistical prosody features from audio bytes with caching.
        Optionally trims to max_duration_sec for clean, representative sampling.
        """
        audio_hash = cls.get_audio_hash(audio_bytes)
        if audio_hash in PROSODY_PROFILE_CACHE:
            cached = PROSODY_PROFILE_CACHE[audio_hash].copy()
            cached["cached"] = True
            return cached

        try:
            samples_all, sr, total_duration_sec = decode_audio_to_pcm(
                audio_bytes, target_sr=24000, max_duration_sec=max_duration_sec
            )

            # Trim to max_duration_sec for clean analysis
            max_samples = int(max_duration_sec * sr)
            samples = samples_all[:max_samples] if len(samples_all) > max_samples else samples_all
            duration_sec = len(samples) / sr

            # -------------------------------------------------------------
            # 1. Frame-Level RMS Energy & Adaptive VAD for Pauses
            # -------------------------------------------------------------
            frame_len = int(0.025 * sr) # 25 ms (600 samples)
            hop_len = int(0.010 * sr)   # 10 ms (240 samples)
            
            rms_frames = []
            for i in range(0, len(samples) - frame_len, hop_len):
                frame = samples[i:i + frame_len]
                sum_sq = sum(x * x for x in frame)
                rms_val = math.sqrt(sum_sq / len(frame) + 1e-12)
                rms_frames.append(rms_val)

            if not rms_frames:
                rms_frames = [0.1]

            # Adaptive VAD threshold
            sorted_rms = sorted(rms_frames)
            idx15 = int(0.15 * len(sorted_rms))
            idx95 = int(0.95 * len(sorted_rms))
            p15 = sorted_rms[idx15]
            p95 = sorted_rms[idx95]
            vad_thresh = p15 + 0.30 * max(1e-5, (p95 - p15))
            raw_speech = [r > vad_thresh for r in rms_frames]

            # Morphological Silence Bridging & Hangover:
            # Step A: Bridge short speech dropouts (<= 50ms / 5 frames) inside active speech
            bridged_speech = list(raw_speech)
            gap = 0
            for i in range(len(bridged_speech)):
                if not bridged_speech[i]:
                    gap += 1
                else:
                    if 0 < gap <= 5 and (i - gap > 0):
                        for k in range(i - gap, i):
                            bridged_speech[k] = True
                    gap = 0

            # Step B: Bridge short noise bursts / clicks (<= 60ms / 6 frames) inside continuous pause
            noise = 0
            for i in range(len(bridged_speech)):
                if bridged_speech[i]:
                    noise += 1
                else:
                    if 0 < noise <= 6 and (i - noise > 0):
                        for k in range(i - noise, i):
                            bridged_speech[k] = False
                    noise = 0

            # Identify Pauses (bridged silence runs >= 100 ms / 10 frames)
            min_pause_frames = 10
            pauses_ms = []
            speech_runs_frames = []
            
            curr_silence = 0
            curr_speech = 0
            
            for speech_active in bridged_speech:
                if speech_active:
                    if curr_silence >= min_pause_frames:
                        pauses_ms.append(curr_silence * 10)
                    curr_silence = 0
                    curr_speech += 1
                else:
                    if curr_speech > 0:
                        speech_runs_frames.append(curr_speech * 10)
                    curr_speech = 0
                    curr_silence += 1

            if curr_silence >= min_pause_frames:
                pauses_ms.append(curr_silence * 10)
            if curr_speech > 0:
                speech_runs_frames.append(curr_speech * 10)

            # Pause distribution
            pause_count = len(pauses_ms)
            if pauses_ms:
                s_pauses = sorted(pauses_ms)
                n_p = len(s_pauses)
                if n_p % 2 == 1:
                    pause_median_ms = float(s_pauses[n_p // 2])
                else:
                    pause_median_ms = float(s_pauses[n_p // 2 - 1] + s_pauses[n_p // 2]) / 2.0
                pause_p10_ms = float(s_pauses[int(0.10 * n_p)])
                pause_p90_ms = float(s_pauses[min(n_p - 1, int(0.90 * n_p))])
                total_pause_time_sec = sum(pauses_ms) / 1000.0
            else:
                pause_median_ms = 180.0
                pause_p10_ms = 110.0
                pause_p90_ms = 450.0
                total_pause_time_sec = 0.0
                
            pause_ratio = total_pause_time_sec / max(0.1, duration_sec)

            short_pauses = [p for p in pauses_ms if p < 250]
            med_pauses = [p for p in pauses_ms if 250 <= p <= 500]
            long_pauses = [p for p in pauses_ms if p > 500]

            pause_distribution = {
                "short_pct": round(len(short_pauses) / max(1, pause_count) * 100, 1),
                "medium_pct": round(len(med_pauses) / max(1, pause_count) * 100, 1),
                "long_pct": round(len(long_pauses) / max(1, pause_count) * 100, 1)
            }

            # Breath group / speech run duration
            if speech_runs_frames:
                s_runs = sorted(speech_runs_frames)
                median_breath_sec = float(s_runs[len(s_runs) // 2] / 1000.0)
                p90_breath_sec = float(s_runs[min(len(s_runs) - 1, int(0.90 * len(s_runs)))] / 1000.0)
            else:
                median_breath_sec = 0.65
                p90_breath_sec = 1.20

            # -------------------------------------------------------------
            # 2. Syllable Nuclei Counting & Speaking Rate
            # -------------------------------------------------------------
            # 10ms energy envelope
            sub_step = int(sr * 0.010) # 10ms
            raw_env = np.array([np.mean(np.abs(samples[i:i + sub_step])) for i in range(0, len(samples) - sub_step, sub_step)], dtype=np.float32)
            
            # Smooth energy envelope with 50ms Hann window to eliminate high-frequency ripple
            kernel = np.hanning(7)
            kernel = kernel / np.sum(kernel)
            smooth_env = np.convolve(raw_env, kernel, mode='same') if len(raw_env) >= 7 else raw_env

            # Count prominent syllable peaks with minimum 120ms separation (~8.3 syl/sec theoretical physical max)
            min_dist_frames = 12 # 120ms separation between syllable nuclei
            peaks = 0
            last_peak_idx = -min_dist_frames
            peak_thresh = p15 + 0.18 * max(1e-5, (p95 - p15))

            for i in range(1, len(smooth_env) - 1):
                if smooth_env[i] > smooth_env[i - 1] and smooth_env[i] > smooth_env[i + 1]:
                    if smooth_env[i] > peak_thresh and (i - last_peak_idx) >= min_dist_frames:
                        peaks += 1
                        last_peak_idx = i
            
            active_speech_sec = max(0.5, duration_sec - total_pause_time_sec)
            # Broad sensible sanity bounds (2.5 - 12.0 syl/sec) without artificial 8.5 clamp
            raw_pace = peaks / active_speech_sec
            pace_syl_sec = float(min(12.0, max(2.5, raw_pace)))
            pace_multiplier = float(min(1.50, max(0.70, pace_syl_sec / 4.8)))
            target_phrase_aksharas = int(min(18, max(8, round(p90_breath_sec * pace_syl_sec))))

            # -------------------------------------------------------------
            # 3. Pitch Tracking (F0 Contour, Median, Range & Slope)
            # -------------------------------------------------------------
            pitch_frame_len = int(0.040 * sr) # 40 ms (960 samples)
            pitch_hop_len = int(0.020 * sr)   # 20 ms (480 samples)
            pitches = []

            for i in range(0, len(samples) - pitch_frame_len, pitch_hop_len):
                frame = samples[i:i + pitch_frame_len]
                f_rms = math.sqrt(sum(x*x for x in frame) / len(frame) + 1e-12)
                if f_rms < vad_thresh:
                    continue
                
                # Autocorrelation
                min_lag = int(sr / 350) # ~68
                max_lag = int(sr / 75)  # ~320
                best_corr = -1.0
                best_lag = min_lag

                # Energy at lag 0
                e0 = sum(x*x for x in frame)
                if e0 < 1e-6:
                    continue

                for lag in range(min_lag, min(max_lag, len(frame) // 2), 2):
                    c = sum(frame[j] * frame[j + lag] for j in range(len(frame) - lag))
                    norm_c = c / e0
                    if norm_c > best_corr:
                        best_corr = norm_c
                        best_lag = lag

                if best_corr > 0.35:
                    f0 = sr / best_lag
                    pitches.append(f0)

            if len(pitches) > 10:
                s_pitches = sorted(pitches)
                pitch_median_hz = float(s_pitches[len(s_pitches) // 2])
                pitch_p10_hz = float(s_pitches[int(0.10 * len(s_pitches))])
                pitch_p90_hz = float(s_pitches[min(len(s_pitches) - 1, int(0.90 * len(s_pitches)))])
                pitch_range_hz = float(pitch_p90_hz - pitch_p10_hz)
                pitch_std = float(math.sqrt(sum((p - pitch_median_hz)**2 for p in pitches) / len(pitches)))
                pitch_span_semitones = float(12.0 * math.log2(max(1.0, pitch_p90_hz / max(1.0, pitch_p10_hz))))
            else:
                pitch_median_hz = 176.0
                pitch_p10_hz = 125.0
                pitch_p90_hz = 227.0
                pitch_range_hz = 102.0
                pitch_std = 32.0
                pitch_span_semitones = 8.44

            # Sentence Ending slope
            ending_slope = "falling_punchy"
            if len(pitches) > 15:
                recent_p = pitches[-10:]
                if recent_p[-1] > recent_p[0] + 10:
                    ending_slope = "rising_rhetorical"
                elif recent_p[-1] < recent_p[0] - 8:
                    ending_slope = "falling_punchy"
                else:
                    ending_slope = "neutral_cadence"

            # -------------------------------------------------------------
            # 4. Energy Dynamics, Crest Factor & Dynamic Punch
            # -------------------------------------------------------------
            rms_mean = float(sum(rms_frames) / len(rms_frames))
            rms_std = float(math.sqrt(sum((r - rms_mean)**2 for r in rms_frames) / len(rms_frames)))
            peak_val = float(max(abs(x) for x in samples))
            crest_factor_db = float(20.0 * math.log10(peak_val / max(1e-5, rms_mean)))
            energy_punch = float(min(2.0, max(0.8, (rms_std / max(1e-4, rms_mean)) * 1.5)))

            # Compile Full Normalized ProsodyProfile
            profile: Dict[str, Any] = {
                "profile_id": f"profile_{audio_hash[:8]}",
                "audio_hash": audio_hash,
                "analyzed_duration_sec": round(duration_sec, 2),
                "total_duration_sec": round(total_duration_sec, 2),
                "speaking_rate": {
                    "pace_syl_sec": round(pace_syl_sec, 2),
                    "pace_multiplier": round(pace_multiplier, 2),
                    "tempo_category": "Ultra-Fast Presenter" if pace_syl_sec >= 6.5 else ("Fast Explainer" if pace_syl_sec >= 5.8 else "Standard")
                },
                "pitch_dynamics": {
                    "median_hz": round(pitch_median_hz, 1),
                    "range_hz": round(pitch_range_hz, 1),
                    "p10_hz": round(pitch_p10_hz, 1),
                    "p90_hz": round(pitch_p90_hz, 1),
                    "span_semitones": round(pitch_span_semitones, 2),
                    "std_hz": round(pitch_std, 1),
                    "ending_slope": ending_slope
                },
                "pauses": {
                    "count": pause_count,
                    "median_ms": round(pause_median_ms, 1),
                    "p90_ms": round(pause_p90_ms, 1),
                    "pause_ratio_pct": round(pause_ratio * 100, 1),
                    "distribution": pause_distribution
                },
                "energy_and_punch": {
                    "crest_factor_db": round(crest_factor_db, 1),
                    "energy_punch": round(energy_punch, 2),
                    "rms_variation": round(rms_std, 3),
                    "transition_contrast": "High Dynamic Range" if energy_punch >= 1.2 else "Moderate"
                },
                "phrasing": {
                    "target_phrase_aksharas": target_phrase_aksharas,
                    "median_breath_sec": round(median_breath_sec, 2),
                    "p90_breath_sec": round(p90_breath_sec, 2)
                },
                "cached": False
            }

            PROSODY_PROFILE_CACHE[audio_hash] = profile
            return profile

        except Exception as e:
            print(f"Error extracting prosody profile: {e}")
            return {
                "profile_id": "profile_default",
                "audio_hash": "default",
                "analyzed_duration_sec": 10.0,
                "speaking_rate": {"pace_syl_sec": 6.65, "pace_multiplier": 1.26, "tempo_category": "Fast Explainer"},
                "pitch_dynamics": {"median_hz": 176.0, "range_hz": 102.0, "p10_hz": 125.0, "p90_hz": 227.0, "span_semitones": 8.44, "ending_slope": "falling_punchy"},
                "pauses": {"count": 15, "median_ms": 169.0, "p90_ms": 450.0, "pause_ratio_pct": 25.0, "distribution": {"short_pct": 70.0, "medium_pct": 20.0, "long_pct": 10.0}},
                "energy_and_punch": {"crest_factor_db": 17.5, "energy_punch": 1.35, "transition_contrast": "High Dynamic Range"},
                "phrasing": {"target_phrase_aksharas": 12, "median_breath_sec": 0.65, "p90_breath_sec": 1.20},
                "cached": False
            }

if __name__ == "__main__":
    test_path = "uploads/ref_vidssave.com ✊🏼INDIA🇮🇳vs PAK at SCO summit💥 720P.mp3"
    if os.path.exists(test_path):
        with open(test_path, "rb") as f:
            data = f.read()
        prof = DeliveryProfiler.extract_prosody_profile(data)
        import json
        print(json.dumps(prof, indent=2))
