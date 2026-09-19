#!/usr/bin/env python3
"""
Unit tests for DeliveryProfiler:
1. Clean silence
2. Silence interrupted by tiny noise burst (bridging verification)
3. Two genuinely separate pauses
4. Short intentional hesitation
5. Syllable rate measurement
"""

import math
import struct
import unittest
import numpy as np
from delivery_profiler import DeliveryProfiler

def create_synthetic_wav_bytes(samples: list, sr: int = 24000) -> bytes:
    """Helper to convert float samples to 16-bit mono WAV bytes."""
    import io, wave
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        int16_samples = [max(-32768, min(32767, int(s * 32767))) for s in samples]
        raw = struct.pack(f"<{len(int16_samples)}h", *int16_samples)
        wf.writeframes(raw)
    return buf.getvalue()

class TestDeliveryProfiler(unittest.TestCase):

    def setUp(self):
        self.sr = 24000

    def _tone(self, duration_sec: float, freq: float = 200.0, amp: float = 0.5):
        n = int(duration_sec * self.sr)
        return [amp * math.sin(2 * math.pi * freq * i / self.sr) for i in range(n)]

    def _silence(self, duration_sec: float):
        return [0.0] * int(duration_sec * self.sr)

    def _noise(self, duration_sec: float, amp: float = 0.05):
        np.random.seed(42)
        return list(np.random.uniform(-amp, amp, int(duration_sec * self.sr)))

    def test_clean_silence_pauses(self):
        """Speech -> 500ms Clean Silence -> Speech should detect exactly 1 pause ~500ms."""
        audio = self._tone(1.0) + self._silence(0.5) + self._tone(1.0)
        wav_bytes = create_synthetic_wav_bytes(audio, self.sr)
        prof = DeliveryProfiler.extract_prosody_profile(wav_bytes)
        
        self.assertEqual(prof["pauses"]["count"], 1)
        self.assertAlmostEqual(prof["pauses"]["median_ms"], 500.0, delta=50.0)

    def test_silence_interrupted_by_tiny_noise_burst(self):
        """500ms silence interrupted by a 30ms noise click should be bridged into 1 pause."""
        # 200ms silence + 30ms click + 270ms silence (total 500ms pause)
        interrupted_silence = self._silence(0.20) + self._noise(0.03, amp=0.4) + self._silence(0.27)
        audio = self._tone(1.0) + interrupted_silence + self._tone(1.0)
        wav_bytes = create_synthetic_wav_bytes(audio, self.sr)
        prof = DeliveryProfiler.extract_prosody_profile(wav_bytes)
        
        # Bridging should ensure this is 1 single pause (~500ms), NOT 2 separate pauses
        self.assertEqual(prof["pauses"]["count"], 1)
        self.assertAlmostEqual(prof["pauses"]["median_ms"], 500.0, delta=70.0)

    def test_two_genuinely_separate_pauses(self):
        """Speech -> 400ms pause -> 1.0s speech -> 600ms pause -> Speech."""
        audio = (
            self._tone(0.8) + 
            self._silence(0.4) + 
            self._tone(1.0) + 
            self._silence(0.6) + 
            self._tone(0.8)
        )
        wav_bytes = create_synthetic_wav_bytes(audio, self.sr)
        prof = DeliveryProfiler.extract_prosody_profile(wav_bytes)
        
        self.assertEqual(prof["pauses"]["count"], 2)
        # Median of 400ms and 600ms is ~500ms
        self.assertAlmostEqual(prof["pauses"]["median_ms"], 500.0, delta=60.0)

    def test_short_intentional_hesitation(self):
        """Short intentional hesitation (~150ms pause) between two short words."""
        audio = self._tone(0.5) + self._silence(0.15) + self._tone(0.5)
        wav_bytes = create_synthetic_wav_bytes(audio, self.sr)
        prof = DeliveryProfiler.extract_prosody_profile(wav_bytes)
        
        self.assertEqual(prof["pauses"]["count"], 1)
        self.assertAlmostEqual(prof["pauses"]["median_ms"], 150.0, delta=40.0)

    def test_syllable_rate_measurement(self):
        """5 syllable bursts in 1 second should measure approximately ~5.0 syl/sec."""
        syllables = []
        for _ in range(5):
            syllables.extend(self._tone(0.12, freq=220.0, amp=0.6))
            syllables.extend(self._silence(0.08))
        
        wav_bytes = create_synthetic_wav_bytes(syllables, self.sr)
        prof = DeliveryProfiler.extract_prosody_profile(wav_bytes)
        pace = prof["speaking_rate"]["pace_syl_sec"]
        
        # Should measure ~5.0 syl/s (not clamped to 8.5)
        self.assertGreaterEqual(pace, 4.0)
        self.assertLessEqual(pace, 6.5)

if __name__ == "__main__":
    unittest.main()
