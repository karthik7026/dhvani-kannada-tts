#!/usr/bin/env python3
"""Generate review-required transcript drafts with faster-whisper.

Drafts never count as approved TTS training text. Review every line in the
output manifest before changing its status to ``approved``.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from faster_whisper import WhisperModel


def write_manifest(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    """Checkpoint drafts after each clip so long CPU runs are resumable."""
    with path.open("w", encoding="utf-8", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=fieldnames, delimiter="|")
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in fieldnames} for row in rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Create draft transcripts for local voice clips.")
    parser.add_argument("data_dir", type=Path, help="Directory containing metadata.csv and wavs/.")
    parser.add_argument("--model", default="small", help="Whisper model size or local model path.")
    parser.add_argument("--language", default=None, help="Optional ISO language code; omit for detection.")
    parser.add_argument("--overwrite", action="store_true", help="Replace existing transcript text.")
    parser.add_argument("--limit", type=int, default=0, help="Process at most this many clips; 0 means all.")
    args = parser.parse_args()

    data_dir = args.data_dir.resolve()
    manifest = data_dir / "metadata.csv"
    if not manifest.is_file():
        raise SystemExit(f"Missing {manifest}")

    with manifest.open(encoding="utf-8", newline="") as source:
        rows = list(csv.DictReader(source, delimiter="|"))
    fieldnames = ["audio_file", "transcript", "status"]

    model = WhisperModel(args.model, device="cpu", compute_type="int8")
    completed = 0
    for index, row in enumerate(rows, start=1):
        existing = (row.get("transcript") or "").strip()
        if existing and not args.overwrite:
            continue
        audio_path = data_dir / (row.get("audio_file") or "")
        if not audio_path.is_file():
            print(f"Skipping row {index}: missing {audio_path}")
            continue
        segments, info = model.transcribe(
            str(audio_path), language=args.language, beam_size=5, vad_filter=True
        )
        text = " ".join(segment.text.strip() for segment in segments).strip()
        row["transcript"] = text
        row["status"] = "draft_transcript"
        completed += 1
        write_manifest(manifest, rows, fieldnames)
        print(f"{index}/{len(rows)} [{info.language}]: {text}", flush=True)
        if args.limit and completed >= args.limit:
            break

    write_manifest(manifest, rows, fieldnames)
    print(f"Wrote {completed} draft transcripts. Review them before setting status=approved.")


if __name__ == "__main__":
    main()
