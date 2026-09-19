import asyncio
import os
import unittest

from speech_director import SpeechDirector


class SpeechDirectorTests(unittest.TestCase):
    def test_local_fallback_is_complete_and_safe(self):
        old_key = os.environ.pop("GROQ_API_KEY", None)
        phrases = [
            {"text": "ಇದು ಆರಂಭ", "is_sentence_end": False, "has_focus": False, "is_question": False},
            {"text": "ಭಾರತ ಅತ್ಯಂತ ಪ್ರಮುಖ", "is_sentence_end": False, "has_focus": True, "is_question": False},
            {"text": "ಇದು ಏಕೆ?", "is_sentence_end": True, "has_focus": False, "is_question": True},
        ]
        plan = asyncio.run(SpeechDirector.direct(phrases))
        self.assertEqual([p["intent"] for p in plan], ["hook", "emphasize", "question"])
        self.assertTrue(all(p["source"] == "local" for p in plan))
        if old_key:
            os.environ["GROQ_API_KEY"] = old_key


if __name__ == "__main__":
    unittest.main()
