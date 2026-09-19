import unittest

from prosody_mapper import KannadaProsodyMapper, PROSODY_LIMITS


class SemanticProsodyTests(unittest.TestCase):
    text = "ನಮಸ್ಕಾರ. ಭಾರತ ಅತ್ಯಂತ ಪ್ರಮುಖವಾಗಿದೆ. ಇದು ಏಕೆ? ಕೊನೆಯ ಮಾತು ಸ್ಪಷ್ಟವಾಗಿದೆ."

    def test_semantic_plan_has_debug_fields_and_safe_limits(self):
        plan = KannadaProsodyMapper.get_realtime_prosody_plan(self.text)
        self.assertTrue(plan["semantic_direction"])
        for phrase in plan["phrases"]:
            for field in ("intent", "rate", "pitch", "volume", "pause_before_ms", "pause_after_ms", "emphasis_words", "reference_profile_influence"):
                self.assertIn(field, phrase)
            rate = int(phrase["rate"].replace("%", "").replace("+", ""))
            pitch = int(phrase["pitch"].replace("Hz", "").replace("+", ""))
            volume = int(phrase["volume"].replace("%", "").replace("+", ""))
            self.assertGreaterEqual(rate, PROSODY_LIMITS["MIN_RATE"])
            self.assertLessEqual(rate, PROSODY_LIMITS["MAX_RATE"])
            self.assertGreaterEqual(pitch, PROSODY_LIMITS["MIN_PITCH"])
            self.assertLessEqual(pitch, PROSODY_LIMITS["MAX_PITCH"])
            self.assertGreaterEqual(volume, PROSODY_LIMITS["MIN_VOLUME"])
            self.assertLessEqual(volume, PROSODY_LIMITS["MAX_VOLUME"])
            self.assertLessEqual(phrase["pause_after_ms"], PROSODY_LIMITS["MAX_PAUSE"])

    def test_semantic_emphasis_preserves_the_complete_phrase(self):
        phrase = {"text": "ಭಾರತ ಅತ್ಯಂತ ಪ್ರಮುಖವಾಗಿದೆ", "is_sentence_end": True, "has_focus": True, "is_question": False, "is_exclamation": False}
        profile = {"speaking_rate": {"pace_multiplier": 1.0}, "pitch_dynamics": {}, "energy_and_punch": {}}
        baseline = KannadaProsodyMapper.get_phrase_delivery(phrase, profile, "kn-IN-GaganNeural", 0, 1, "balanced", 1.0, 1.0, "snappy", {"intent": "emphasize", "source": "local"}, False)
        directed = KannadaProsodyMapper.get_phrase_delivery(phrase, profile, "kn-IN-GaganNeural", 0, 1, "balanced", 1.0, 1.0, "snappy", {"intent": "emphasize", "source": "local"}, True, 0.20)
        segments = KannadaProsodyMapper.synthesis_segments(phrase["text"], baseline, directed)
        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0]["kind"], "full_phrase")
        self.assertEqual(segments[0]["text"], phrase["text"])

    def test_zero_strength_is_pure_baseline_delivery(self):
        phrase = {"text": "ಭಾರತ ಅತ್ಯಂತ ಪ್ರಮುಖವಾಗಿದೆ", "is_sentence_end": True, "has_focus": True, "is_question": False, "is_exclamation": False}
        profile = {"speaking_rate": {"pace_multiplier": 1.0}, "pitch_dynamics": {}, "energy_and_punch": {}}
        direction = {"intent": "emphasize", "source": "local"}
        baseline = KannadaProsodyMapper.get_phrase_delivery(phrase, profile, "kn-IN-GaganNeural", 0, 1, "balanced", 1.0, 1.0, "snappy", direction, False)
        zero_strength = KannadaProsodyMapper.get_phrase_delivery(phrase, profile, "kn-IN-GaganNeural", 0, 1, "balanced", 1.0, 1.0, "snappy", direction, True, 0.0)
    def test_adjacent_phrase_continuity_smoothing(self):
        plan = KannadaProsodyMapper.get_realtime_prosody_plan(self.text)
        phrases = plan["phrases"]
        max_p = plan["continuity_constraints"]["max_adjacent_pitch_delta_hz"]
        max_r = plan["continuity_constraints"]["max_adjacent_rate_delta_pct"]
        
        for i in range(1, len(phrases)):
            prev_p = int(phrases[i-1]["pitch"].replace("Hz", "").replace("+", ""))
            curr_p = int(phrases[i]["pitch"].replace("Hz", "").replace("+", ""))
            prev_r = int(phrases[i-1]["rate"].replace("%", "").replace("+", ""))
            curr_r = int(phrases[i]["rate"].replace("%", "").replace("+", ""))
            
            self.assertLessEqual(abs(curr_p - prev_p), max_p, f"Pitch step delta {abs(curr_p - prev_p)} exceeds {max_p}Hz")
            self.assertLessEqual(abs(curr_r - prev_r), max_r, f"Rate step delta {abs(curr_r - prev_r)} exceeds {max_r}%")


if __name__ == "__main__":
    unittest.main()
