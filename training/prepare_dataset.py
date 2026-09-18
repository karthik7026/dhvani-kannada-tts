#!/usr/bin/env python3
"""Create reviewable TTS training clips and a transcript manifest from one recording.

This script does not train or clone a voice. It identifies candidate speech
regions by energy, writes short WAV clips, and creates metadata.csv with blank
transcript fields that must be reviewed and completed before fine-tuning.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np
import soundfile as sf


def speech_segments(
    samples: np.ndarray,
    sample_rate: int,
    min_seconds: float,
    max_seconds: float,
) -> list[tuple[int, int]]:
    """Return conservative speech candidates based on 30 ms RMS frames."""
    frame_size = max(1, round(sample_rate * 0.03))
    usable = len(samples) - (len(samples) % frame_size)
    frames = samples[:usable].reshape(-1, frame_size)
    rms = np.sqrt(np.mean(frames**2, axis=1) + 1e-10)
    floor = np.percentile(rms, 20)
    ceiling = np.percentile(rms, 90)
    threshold = floor + (ceiling - floor) * 0.28
    active = rms >= threshold

    # Fill pauses shorter than 250 ms so ordinary within-sentence pauses stay
    # in the same clip.
    max_gap = max(1, round(0.25 / 0.03))
    gap_start = None
    for index, is_active in enumerate(active):
        if not is_active and gap_start is None:
            gap_start = index
        elif is_active and gap_start is not None:
            if index - gap_start <= max_gap:
                active[gap_start:index] = True
            gap_start = None

    segments: list[tuple[int, int]] = []
    start = None
    max_frames = max(1, round(max_seconds / 0.03))
    min_frames = max(1, round(min_seconds / 0.03))
    for index, is_active in enumerate(active):
        if is_active and start is None:
            start = index
        at_end = index == len(active) - 1
        if start is not None and ((not is_active) or at_end or index - start >= max_frames):
            end = index if not is_active else index + 1
            if end - start >= min_frames:
                segments.append((start * frame_size, min(len(samples), end * frame_size)))
            start = None
    return segments


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare speech clips for manual TTS transcription.")
    parser.add_argument("input", type=Path, help="Your own source recording (MP3, WAV, or other SoundFile-supported format).")
    parser.add_argument("--output", type=Path, default=Path("training/data"), help="Output directory.")
    parser.add_argument("--min-seconds", type=float, default=1.5)
    parser.add_argument("--max-seconds", type=float, default=12.0)
    args = parser.parse_args()

    audio, source_rate = sf.read(args.input, dtype="float32", always_2d=True)
    mono = audio.mean(axis=1)
    target_rate = 24_000
    if source_rate != target_rate:
        target_size = round(len(mono) * target_rate / source_rate)
        mono = np.interp(
            np.linspace(0, len(mono) - 1, target_size), np.arange(len(mono)), mono
        ).astype(np.float32)

    wav_dir = args.output / "wavs"
    wav_dir.mkdir(parents=True, exist_ok=True)
    segments = speech_segments(mono, target_rate, args.min_seconds, args.max_seconds)

    manifest_path = args.output / "metadata.csv"
    with manifest_path.open("w", encoding="utf-8", newline="") as manifest:
        writer = csv.writer(manifest, delimiter="|")
        writer.writerow(["audio_file", "transcript", "status"])
        for number, (start, end) in enumerate(segments, start=1):
            name = f"voice_{number:04d}.wav"
            sf.write(wav_dir / name, mono[start:end], target_rate, subtype="PCM_16")
            writer.writerow([f"wavs/{name}", "", "needs_transcript_and_review"])

    print(f"Created {len(segments)} candidate clips in {wav_dir}")
    print(f"Complete the transcript column in {manifest_path} before training.")


if __name__ == "__main__":
    main()
