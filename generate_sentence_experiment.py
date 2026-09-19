#!/usr/bin/env python3
"""
Dhvani Sentence-Level Experiment  (A / B / C)
=============================================

Goal: Compare sentence-level synthesis (1 Edge call per sentence)
against the current phrase-chunked delivery (10+ calls).

VERSION A — PRONUNCIATION ONLY
  - 1 Edge call per complete sentence
  - rate=+0%, pitch=+0Hz, volume=default
  - No semantic prosody, no extra pauses

VERSION B — SENTENCE + NATURAL PAUSES
  - Same 1 call per sentence
  - Rate/pitch near default
  - Structural pauses inserted between sentences using punctuation
    and thought-boundary heuristics

VERSION C — SUBTLE SEMANTIC DELIVERY
  - Same 1 call per sentence (NOT split into sub-sentence chunks)
  - SpeechDirector labels allowed but mapped to gentle variations
  - Rate: 0% to +12%  |  Pitch: ±8–12 Hz  |  Volume: stable
  - Emphasis via slight timing/rate reduction, not separate clips

Outputs:
  results/A_pronunciation_sentence.wav
  results/B_sentence_pauses.wav
  results/C_subtle_semantic.wav
  results/sentence_experiment_report.json
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import wave
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np

# ---------------------------------------------------------------------------
# Project imports
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).parent))
from pronunciation_engine import KannadaPronunciationEngine
from speech_director import SpeechDirector

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MDR_TEST_SCRIPT = (
    "ನಾವು ₹1000 ಡಿಜಿಟಲ್ ಪೇಮೆಂಟ್ ಮಾಡಿದಾಗ, ವ್ಯಾಪಾರಿ 1% MDR ಕಡಿತಗೊಳಿಸುತ್ತಾನೆ. "
    "ದಿನಾಂಕ 15/08/1947 ರಂದು ಆರಂಭವಾದ ಈ ಪದ್ಧತಿಯು ಇಂದು YouTube ಮತ್ತು ChatGPT "
    "ನಂತಹ AI ತಂತ್ರಜ್ಞಾನಗಳ ಮೂಲಕ ಲಕ್ಷಾಂತರ ಜನರಿಗೆ ತಲುಪಿದೆ."
)

VOICE = "kn-IN-GaganNeural"
SAMPLE_RATE = 24000
RESULTS_DIR = Path(__file__).parent / "results"

# ---------------------------------------------------------------------------
# Audio helpers
# ---------------------------------------------------------------------------

def mp3_to_pcm(mp3_path: str, wav_path: str, sr: int = SAMPLE_RATE) -> np.ndarray:
    """Convert mp3 → WAV → float32 PCM using afconvert or ffmpeg."""
    if shutil.which("afconvert"):
        subprocess.run(
            ["afconvert", "-f", "WAVE", "-d", "LEI16@24000", "-c", "1", mp3_path, wav_path],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
        )
    elif shutil.which("ffmpeg"):
        subprocess.run(
            ["ffmpeg", "-y", "-i", mp3_path, "-ac", "1", "-ar", str(sr), wav_path],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
        )
    else:
        raise RuntimeError("Neither afconvert nor ffmpeg found")

    with wave.open(wav_path, "rb") as wf:
        raw = wf.readframes(wf.getnframes())
        data = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    return data


def peak_normalize(pcm: np.ndarray, target: float = 0.95) -> np.ndarray:
    peak = np.max(np.abs(pcm))
    if peak < 1e-6:
        return pcm
    return pcm * (target / peak)


def save_wav(pcm: np.ndarray, path: str, sr: int = SAMPLE_RATE) -> None:
    out = (pcm * 32767).astype(np.int16)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(out.tobytes())


def silence(duration_ms: float, sr: int = SAMPLE_RATE) -> np.ndarray:
    return np.zeros(int((duration_ms / 1000.0) * sr), dtype=np.float32)


# ---------------------------------------------------------------------------
# Sentence splitter
# ---------------------------------------------------------------------------

def split_into_sentences(text: str) -> List[str]:
    """Split Kannada text on sentence-ending punctuation (. ? ! |)
    Returns complete sentences with trailing punctuation preserved."""
    # Split on period, question mark, exclamation, or pipe followed by space or end
    parts = re.split(r'(?<=[.?!|])\s+', text.strip())
    sentences = [s.strip() for s in parts if s.strip()]
    return sentences


# ---------------------------------------------------------------------------
# Edge TTS helpers
# ---------------------------------------------------------------------------

async def synthesize_sentence(
    text: str,
    voice: str,
    rate: str = "+0%",
    pitch: str = "+0Hz",
    volume: str = "+0%",
    temp_dir: str = "/tmp",
    tag: str = "chunk",
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """Single Edge TTS call for one complete sentence. Returns (pcm, metadata)."""
    import edge_tts

    mp3_path = os.path.join(temp_dir, f"{tag}.mp3")
    wav_path = os.path.join(temp_dir, f"{tag}.wav")

    t0 = time.time()
    communicate = edge_tts.Communicate(text=text, voice=voice, pitch=pitch, rate=rate, volume=volume)
    await communicate.save(mp3_path)
    tts_time = round(time.time() - t0, 3)

    pcm = mp3_to_pcm(mp3_path, wav_path)
    duration_sec = round(len(pcm) / SAMPLE_RATE, 3)

    meta = {
        "text_sent_to_edge": text,
        "rate": rate,
        "pitch": pitch,
        "volume": volume,
        "edge_calls": 1,
        "duration_sec": duration_sec,
        "tts_time_sec": tts_time,
        "sub_sentence_split": False,
    }
    return pcm, meta


# ---------------------------------------------------------------------------
# VERSION A: Pronunciation Only — Flat prosody, 1 call per sentence
# ---------------------------------------------------------------------------

async def generate_version_a(
    sentences: List[str], speech_sentences: List[str], temp_dir: str
) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
    """Flat rate=+0%, pitch=+0Hz, volume=default. One call per sentence."""
    pcm_chunks: List[np.ndarray] = []
    report: List[Dict[str, Any]] = []

    for i, (orig, speech) in enumerate(zip(sentences, speech_sentences)):
        pcm, meta = await synthesize_sentence(
            text=speech, voice=VOICE,
            rate="+0%", pitch="+0Hz", volume="+0%",
            temp_dir=temp_dir, tag=f"a_{i:02d}",
        )
        meta["original_sentence"] = orig
        report.append(meta)
        pcm_chunks.append(pcm)

        # Natural inter-sentence gap (only Edge's own trailing silence)
        if i < len(sentences) - 1:
            pcm_chunks.append(silence(100))  # minimal 100ms gap between sentences

    combined = np.concatenate(pcm_chunks) if pcm_chunks else np.array([], dtype=np.float32)
    return peak_normalize(combined), report


# ---------------------------------------------------------------------------
# VERSION B: Sentence + Natural Pauses — Thought-boundary pauses
# ---------------------------------------------------------------------------

def classify_sentence_boundary(sentence: str) -> float:
    """Return pause duration (ms) after this sentence based on punctuation."""
    text = sentence.strip()
    if text.endswith("?"):
        return 450   # question — listener processing time
    if text.endswith("!"):
        return 400   # exclamation — brief dramatic hold
    if text.endswith("."):
        # Check for comma/semicolon within — suggests complex thought
        if "," in text or ";" in text:
            return 500  # longer sentence boundary
        return 400      # standard sentence gap
    return 350  # default


async def generate_version_b(
    sentences: List[str], speech_sentences: List[str], temp_dir: str
) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
    """Sentence-level synthesis with structural pauses between sentences.
    Rate/pitch stay near default. Pauses are based on punctuation/boundaries."""
    pcm_chunks: List[np.ndarray] = []
    report: List[Dict[str, Any]] = []

    for i, (orig, speech) in enumerate(zip(sentences, speech_sentences)):
        # Slight rate bump (+5%) for natural reading flow, pitch at default
        pcm, meta = await synthesize_sentence(
            text=speech, voice=VOICE,
            rate="+5%", pitch="+0Hz", volume="+0%",
            temp_dir=temp_dir, tag=f"b_{i:02d}",
        )
        meta["original_sentence"] = orig
        report.append(meta)
        pcm_chunks.append(pcm)

        # Structural pause between sentences
        if i < len(sentences) - 1:
            pause_ms = classify_sentence_boundary(orig)
            meta["pause_after_ms"] = pause_ms
            pcm_chunks.append(silence(pause_ms))

    combined = np.concatenate(pcm_chunks) if pcm_chunks else np.array([], dtype=np.float32)
    return peak_normalize(combined), report


# ---------------------------------------------------------------------------
# VERSION C: Subtle Semantic Delivery — Light SpeechDirector overlay
# ---------------------------------------------------------------------------

# Constrained prosody map for Version C: sentence-level only
SEMANTIC_SENTENCE_MAP: Dict[str, Dict[str, str]] = {
    "hook":         {"rate": "+5%",   "pitch": "+8Hz",   "volume": "+0%"},
    "explanation":  {"rate": "+8%",   "pitch": "+0Hz",   "volume": "+0%"},
    "emphasize":    {"rate": "+0%",   "pitch": "+10Hz",  "volume": "+2%"},
    "question":     {"rate": "+3%",   "pitch": "+12Hz",  "volume": "+0%"},
    "conclusion":   {"rate": "+0%",   "pitch": "-5Hz",   "volume": "+0%"},
    "contrast":     {"rate": "+5%",   "pitch": "-8Hz",   "volume": "+0%"},
    "continuation": {"rate": "+10%",  "pitch": "+0Hz",   "volume": "+0%"},
}


def sentence_to_pseudo_phrases(sentence: str, idx: int, total: int) -> Dict[str, Any]:
    """Create a minimal phrase-like dict for SpeechDirector compatibility."""
    text = sentence.strip()
    return {
        "text": text,
        "is_sentence_end": True,
        "is_question": text.endswith("?"),
        "is_exclamation": text.endswith("!"),
        "has_focus": bool(re.search(r'[₹%\d]|ಪ್ರಮುಖ|ಮಹತ್ವ|ಲಕ್ಷ', text)),
        "punct": text[-1] if text else ".",
        "pause_type": "long" if idx == total - 1 else "medium",
    }


async def generate_version_c(
    sentences: List[str], speech_sentences: List[str], temp_dir: str
) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
    """Sentence-level synthesis with SpeechDirector semantic labels
    mapped to gentle rate/pitch variations within tight limits."""
    pcm_chunks: List[np.ndarray] = []
    report: List[Dict[str, Any]] = []

    # Build pseudo-phrase list for director
    pseudo_phrases = [
        sentence_to_pseudo_phrases(s, i, len(sentences))
        for i, s in enumerate(sentences)
    ]

    # Get semantic directions
    direction_plan = await SpeechDirector.direct(pseudo_phrases)

    for i, (orig, speech) in enumerate(zip(sentences, speech_sentences)):
        intent = direction_plan[i]["intent"] if i < len(direction_plan) else "explanation"
        source = direction_plan[i].get("source", "unknown") if i < len(direction_plan) else "fallback"
        prosody = SEMANTIC_SENTENCE_MAP.get(intent, SEMANTIC_SENTENCE_MAP["explanation"])

        pcm, meta = await synthesize_sentence(
            text=speech, voice=VOICE,
            rate=prosody["rate"], pitch=prosody["pitch"], volume=prosody["volume"],
            temp_dir=temp_dir, tag=f"c_{i:02d}",
        )
        meta["original_sentence"] = orig
        meta["semantic_intent"] = intent
        meta["semantic_source"] = source
        report.append(meta)
        pcm_chunks.append(pcm)

        # Thought-boundary pause
        if i < len(sentences) - 1:
            pause_ms = classify_sentence_boundary(orig)
            meta["pause_after_ms"] = pause_ms
            pcm_chunks.append(silence(pause_ms))

    combined = np.concatenate(pcm_chunks) if pcm_chunks else np.array([], dtype=np.float32)
    return peak_normalize(combined), report


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    temp_dir = tempfile.mkdtemp(prefix="dhvani_sentence_exp_")

    print("=" * 60)
    print("DHVANI SENTENCE-LEVEL EXPERIMENT")
    print("=" * 60)

    # Step 1: Pronunciation preprocessing (UNCHANGED from production)
    print("\n[1/5] Pronunciation preprocessing...")
    display_text, speech_text, transforms = KannadaPronunciationEngine.process_pronunciation(
        MDR_TEST_SCRIPT.strip()
    )
    print(f"  Display text: {display_text[:80]}...")
    print(f"  Speech text:  {speech_text[:80]}...")
    print(f"  Transforms:   {len(transforms)} applied")

    # Step 2: Split into complete sentences
    print("\n[2/5] Sentence splitting...")
    display_sentences = split_into_sentences(display_text)
    speech_sentences = split_into_sentences(speech_text)
    print(f"  Display sentences: {len(display_sentences)}")
    for i, s in enumerate(display_sentences):
        print(f"    S{i+1}: {s}")
    print(f"  Speech sentences:  {len(speech_sentences)}")
    for i, s in enumerate(speech_sentences):
        print(f"    S{i+1}: {s}")

    # Ensure matching counts
    if len(display_sentences) != len(speech_sentences):
        print(f"\n  WARNING: Sentence count mismatch! display={len(display_sentences)}, speech={len(speech_sentences)}")
        # Use speech_text sentences as ground truth, map display if possible
        min_count = min(len(display_sentences), len(speech_sentences))
        display_sentences = display_sentences[:min_count]
        speech_sentences = speech_sentences[:min_count]

    # Step 3: Generate VERSION A
    print("\n[3/5] Generating VERSION A (pronunciation only, flat prosody)...")
    pcm_a, report_a = await generate_version_a(sentences=display_sentences, speech_sentences=speech_sentences, temp_dir=temp_dir)
    out_a = str(RESULTS_DIR / "A_pronunciation_sentence.wav")
    save_wav(pcm_a, out_a)
    print(f"  ✓ Saved: {out_a}")
    print(f"  Edge calls: {sum(r['edge_calls'] for r in report_a)}")
    print(f"  Duration: {round(len(pcm_a)/SAMPLE_RATE, 2)}s")

    # Step 4: Generate VERSION B
    print("\n[4/5] Generating VERSION B (sentence + natural pauses)...")
    pcm_b, report_b = await generate_version_b(sentences=display_sentences, speech_sentences=speech_sentences, temp_dir=temp_dir)
    out_b = str(RESULTS_DIR / "B_sentence_pauses.wav")
    save_wav(pcm_b, out_b)
    print(f"  ✓ Saved: {out_b}")
    print(f"  Edge calls: {sum(r['edge_calls'] for r in report_b)}")
    print(f"  Duration: {round(len(pcm_b)/SAMPLE_RATE, 2)}s")

    # Step 5: Generate VERSION C
    print("\n[5/5] Generating VERSION C (subtle semantic delivery)...")
    pcm_c, report_c = await generate_version_c(sentences=display_sentences, speech_sentences=speech_sentences, temp_dir=temp_dir)
    out_c = str(RESULTS_DIR / "C_subtle_semantic.wav")
    save_wav(pcm_c, out_c)
    print(f"  ✓ Saved: {out_c}")
    print(f"  Edge calls: {sum(r['edge_calls'] for r in report_c)}")
    print(f"  Duration: {round(len(pcm_c)/SAMPLE_RATE, 2)}s")

    # Full report
    full_report = {
        "experiment": "sentence_level_vs_phrase_chunked",
        "test_script": MDR_TEST_SCRIPT,
        "voice": VOICE,
        "pronunciation_transforms": len(transforms),
        "display_text": display_text,
        "speech_text": speech_text,
        "sentence_count": len(display_sentences),
        "version_a": {
            "label": "Pronunciation Only — Flat prosody",
            "architecture": "1 Edge call per sentence",
            "rate": "+0%", "pitch": "+0Hz", "volume": "+0%",
            "total_edge_calls": sum(r["edge_calls"] for r in report_a),
            "sub_sentence_splits": any(r["sub_sentence_split"] for r in report_a),
            "total_duration_sec": round(len(pcm_a) / SAMPLE_RATE, 2),
            "sentences": report_a,
        },
        "version_b": {
            "label": "Sentence + Natural Pauses",
            "architecture": "1 Edge call per sentence + structural pauses",
            "rate": "+5%", "pitch": "+0Hz", "volume": "+0%",
            "total_edge_calls": sum(r["edge_calls"] for r in report_b),
            "sub_sentence_splits": any(r["sub_sentence_split"] for r in report_b),
            "total_duration_sec": round(len(pcm_b) / SAMPLE_RATE, 2),
            "sentences": report_b,
        },
        "version_c": {
            "label": "Subtle Semantic Delivery",
            "architecture": "1 Edge call per sentence + SpeechDirector labels",
            "prosody_limits": "rate 0-12%, pitch ±8-12Hz, volume stable",
            "total_edge_calls": sum(r["edge_calls"] for r in report_c),
            "sub_sentence_splits": any(r["sub_sentence_split"] for r in report_c),
            "total_duration_sec": round(len(pcm_c) / SAMPLE_RATE, 2),
            "sentences": report_c,
        },
    }

    report_path = str(RESULTS_DIR / "sentence_experiment_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(full_report, f, ensure_ascii=False, indent=2)
    print(f"\n✓ Full report: {report_path}")

    # Summary table
    print("\n" + "=" * 60)
    print("EXPERIMENT SUMMARY")
    print("=" * 60)
    print(f"{'Version':<12} {'Edge Calls':<12} {'Duration':<12} {'Sub-splits':<12}")
    print("-" * 48)
    for label, key in [("A (flat)", "version_a"), ("B (pauses)", "version_b"), ("C (semantic)", "version_c")]:
        calls = full_report[key]["total_edge_calls"]
        dur = full_report[key]["total_duration_sec"]
        splits = "Yes" if full_report[key]["sub_sentence_splits"] else "No"
        print(f"{label:<12} {calls:<12} {dur:<12} {splits:<12}")
    print()
    print("Files generated:")
    print(f"  {out_a}")
    print(f"  {out_b}")
    print(f"  {out_c}")
    print(f"  {report_path}")
    print()
    print("⚠  Do NOT auto-select a winner. Listen and compare.")

    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    asyncio.run(main())
