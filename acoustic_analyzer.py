#!/usr/bin/env python3
"""
Acoustic Verification & Analysis Script for Dhvani Kannada Delivery Prosody
Measures:
1. Voiced F0 Pitch Movement (Median, Mean, P10, P90, Practical Movement Span in Hz)
2. Speech Activity / Density Ratio (%)
3. Detected Pauses (Count, Median ms, P90 ms)
4. Energy Dynamics (Mean RMS, Dynamic Range dB, Crest Factor dB)
"""
import sys
import wave
import numpy as np
from scipy import signal

def extract_pitch_autocorr(audio: np.ndarray, sr: int = 24000, fmin: float = 60.0, fmax: float = 400.0) -> np.ndarray:
    """Extracts frame-by-frame pitch (F0) using normalized autocorrelation with harmonic peak picking."""
    frame_len = int(0.040 * sr) # 40ms frame
    hop_len = int(0.010 * sr)   # 10ms hop
    min_lag = int(sr / fmax)
    max_lag = int(sr / fmin)

    f0_list = []
    # 50Hz high-pass to remove DC / low rumble
    sos = signal.butter(4, 50.0, 'hp', fs=sr, output='sos')
    filtered = signal.sosfilt(sos, audio)

    # Frame energy threshold for voiced frames
    frame_energies = []
    for i in range(0, len(filtered) - frame_len, hop_len):
        frame = filtered[i:i+frame_len]
        frame_energies.append(np.sum(frame**2))
    
    if not frame_energies:
        return np.array([])
        
    energy_thresh = np.percentile(frame_energies, 25) * 1.5

    for i in range(0, len(filtered) - frame_len, hop_len):
        frame = filtered[i:i+frame_len] * np.hanning(frame_len)
        energy = np.sum(frame**2)
        if energy < energy_thresh:
            continue

        # Autocorrelation
        corr = np.correlate(frame, frame, mode='full')
        corr = corr[len(corr)//2:]
        if max_lag >= len(corr):
            continue

        search_slice = corr[min_lag:max_lag]
        if len(search_slice) == 0:
            continue

        peak_idx = np.argmax(search_slice) + min_lag
        peak_val = corr[peak_idx]

        # Normalized autocorrelation peak coefficient
        if corr[0] > 1e-6 and (peak_val / corr[0]) > 0.35:
            # Parabolic interpolation for sub-sample accuracy
            if 0 < peak_idx < len(corr) - 1:
                alpha = corr[peak_idx - 1]
                beta = corr[peak_idx]
                gamma = corr[peak_idx + 1]
                denom = 2.0 * (2.0 * beta - alpha - gamma)
                if abs(denom) > 1e-6:
                    delta = (alpha - gamma) / denom
                    refined_lag = peak_idx + delta
                else:
                    refined_lag = float(peak_idx)
            else:
                refined_lag = float(peak_idx)

            f0 = sr / refined_lag
            if fmin <= f0 <= fmax:
                f0_list.append(f0)

    return np.array(f0_list)

def analyze_audio(wav_path: str):
    with wave.open(wav_path, "rb") as wf:
        sr = wf.getframerate()
        n_frames = wf.getnframes()
        raw = wf.readframes(n_frames)
    
    audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    duration_sec = len(audio) / sr

    # 1. Energy & VAD
    frame_len = int(0.025 * sr) # 25ms
    hop_len = int(0.010 * sr)   # 10ms
    rms = []
    for i in range(0, len(audio) - frame_len, hop_len):
        frame = audio[i:i+frame_len]
        rms.append(np.sqrt(np.mean(frame**2) + 1e-12))
    rms = np.array(rms)
    rms_db = 20 * np.log10(np.maximum(rms, 1e-6))

    # Adaptive VAD threshold
    p15 = np.percentile(rms_db, 15)
    p95 = np.percentile(rms_db, 95)
    dynamic_range_db = p95 - p15
    vad_thresh_db = p15 + 0.30 * max(6.0, dynamic_range_db)

    is_speech = rms_db > vad_thresh_db

    # Pauses >= 80ms (8 frames)
    min_pause_frames = 8
    pauses_ms = []
    curr_silence = 0
    speech_frames = 0

    for val in is_speech:
        if val:
            speech_frames += 1
            if curr_silence >= min_pause_frames:
                pauses_ms.append(curr_silence * 10)
            curr_silence = 0
        else:
            curr_silence += 1
    if curr_silence >= min_pause_frames:
        pauses_ms.append(curr_silence * 10)

    speech_activity_ratio = (speech_frames * 0.010) / max(0.1, duration_sec) * 100.0

    # 2. Pitch Extraction
    f0 = extract_pitch_autocorr(audio, sr=sr)
    if len(f0) > 10:
        p10 = float(np.percentile(f0, 10))
        p90 = float(np.percentile(f0, 90))
        p50 = float(np.median(f0))
        p_mean = float(np.mean(f0))
        pitch_span_hz = p90 - p10
        span_semitones = 12 * np.log2(max(1.0, p90) / max(1.0, p10))
    else:
        p10, p90, p50, p_mean, pitch_span_hz, span_semitones = 0, 0, 0, 0, 0, 0

    # 3. Pauses stats
    pause_count = len(pauses_ms)
    median_pause_ms = float(np.median(pauses_ms)) if pauses_ms else 0.0
    p90_pause_ms = float(np.percentile(pauses_ms, 90)) if pauses_ms else 0.0

    # 4. Crest Factor
    peak = np.max(np.abs(audio))
    rms_overall = np.sqrt(np.mean(audio**2) + 1e-12)
    crest_factor_db = 20 * np.log10(max(1e-4, peak) / max(1e-4, rms_overall))

    return {
        "duration_sec": round(duration_sec, 2),
        "mean_pitch_hz": round(p_mean, 1),
        "median_pitch_hz": round(p50, 1),
        "p10_pitch_hz": round(p10, 1),
        "p90_pitch_hz": round(p90, 1),
        "pitch_movement_span_hz": round(pitch_span_hz, 1),
        "pitch_span_semitones": round(span_semitones, 2),
        "speech_activity_ratio_pct": round(speech_activity_ratio, 1),
        "detected_pauses_count": pause_count,
        "median_pause_ms": round(median_pause_ms, 1),
        "p90_pause_ms": round(p90_pause_ms, 1),
        "mean_rms_db": round(float(np.mean(rms_db)), 1),
        "dynamic_range_db": round(float(dynamic_range_db), 1),
        "crest_factor_db": round(float(crest_factor_db), 1)
    }

if __name__ == "__main__":
    if len(sys.argv) > 1:
        metrics = analyze_audio(sys.argv[1])
        import json
        print(json.dumps(metrics, indent=2))
