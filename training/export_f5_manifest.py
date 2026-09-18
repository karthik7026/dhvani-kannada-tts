#!/usr/bin/env python3
"""Turn reviewed Dhvani metadata into F5-TTS's required manifest format."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Export reviewed TTS clips for F5-TTS.")
    parser.add_argument("data_dir", type=Path, help="Directory containing metadata.csv and wavs/.")
    parser.add_argument("output", type=Path, help="Output CSV for F5-TTS.")
    args = parser.parse_args()

    data_dir = args.data_dir.resolve()
    metadata = data_dir / "metadata.csv"
    if not metadata.is_file():
        raise SystemExit(f"Missing {metadata}")

    accepted: list[tuple[str, str]] = []
    problems: list[str] = []
    with metadata.open(encoding="utf-8", newline="") as source:
        for row_number, row in enumerate(csv.DictReader(source, delimiter="|"), start=2):
            clip = (row.get("audio_file") or "").strip()
            transcript = (row.get("transcript") or "").strip()
            status = (row.get("status") or "").strip()
            clip_path = (data_dir / clip).resolve()
            if not clip or not clip_path.is_file():
                problems.append(f"row {row_number}: missing clip")
            elif not transcript:
                problems.append(f"row {row_number}: missing transcript")
            elif status not in {"approved", "reviewed"}:
                problems.append(f"row {row_number}: set status to approved after review")
            else:
                accepted.append((str(clip_path), transcript))

    if problems:
        preview = "\n".join(problems[:12])
        more = f"\n... and {len(problems) - 12} more" if len(problems) > 12 else ""
        raise SystemExit(f"Dataset review is incomplete:\n{preview}{more}")
    if len(accepted) < 20:
        raise SystemExit("At least 20 reviewed clips are required before export.")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as destination:
        writer = csv.writer(destination, delimiter="|")
        writer.writerow(["audio_file", "text"])
        writer.writerows(accepted)
    print(f"Exported {len(accepted)} reviewed clips to {args.output}")


if __name__ == "__main__":
    main()
