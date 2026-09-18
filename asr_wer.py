#!/usr/bin/env python3
"""
Word error rate for synthesised Kannada, via ASR.

This is the intelligibility axis. Pace error tells you that you hit the target
speed; WER tells you what that speed cost. The rate sweep is meaningless without
it - the whole point is finding where the two curves cross.

Default model is Whisper large-v3, which supports Kannada and definitely exists.
AI4Bharat's IndicWhisper is likely better on Indic languages if you can get it
running - swap MODEL_ID and report which you used.
"""
import argparse
import csv
import json
import os
import re
import unicodedata

KN_PUNCT = "।॥,.;:!?\"'()[]{}-–—"


def normalise(s: str) -> str:
    """Strip punctuation and collapse whitespace before comparing."""
    s = unicodedata.normalize("NFC", s)
    s = "".join(" " if ch in KN_PUNCT else ch for ch in s)
    return re.sub(r"\s+", " ", s).strip()


def wer(reference: str, hypothesis: str) -> float:
    """Levenshtein distance over words, divided by reference length."""
    r, h = normalise(reference).split(), normalise(hypothesis).split()
    if not r:
        return 0.0 if not h else 1.0
    prev = list(range(len(h) + 1))
    for i, rw in enumerate(r, 1):
        cur = [i] + [0] * len(h)
        for j, hw in enumerate(h, 1):
            cur[j] = min(prev[j] + 1,          # deletion
                         cur[j - 1] + 1,       # insertion
                         prev[j - 1] + (rw != hw))  # substitution
        prev = cur
    return prev[len(h)] / len(r)


class KannadaASR:
    MODEL_ID = "openai/whisper-large-v3"

    def __init__(self, model_id=None, device=None):
        import torch
        from transformers import pipeline
        self.device = device or (0 if torch.cuda.is_available() else -1)
        self.pipe = pipeline("automatic-speech-recognition",
                             model=model_id or self.MODEL_ID,
                             device=self.device,
                             chunk_length_s=30)

    def transcribe(self, path: str) -> str:
        out = self.pipe(path, generate_kwargs={"language": "kannada", "task": "transcribe"})
        return out["text"].strip()


def score_dir(audio_refs, model_id=None, out_csv="wer.csv"):
    """audio_refs: list of (wav_path, reference_text)."""
    asr = KannadaASR(model_id)
    rows = []
    for path, ref in audio_refs:
        hyp = asr.transcribe(path)
        e = wer(ref, hyp)
        rows.append({"file": os.path.basename(path), "wer": round(e, 4),
                     "reference": ref, "hypothesis": hyp})
        print(f"{os.path.basename(path):28s} WER {e:.3f}")
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print(f"\nmean WER {sum(r['wer'] for r in rows)/len(rows):.3f}  ->  {out_csv}")
    return rows


def sweep_wer(sweep_json="sweep/sweep.json", reference_text=None, model_id=None):
    """Attach WER to each point of the rate sweep. This produces your main graph."""
    data = json.load(open(sweep_json))
    asr = KannadaASR(model_id)
    for pt in data:
        wav = f"sweep/sweep_{pt['pace_setting']}.wav"
        pt["hypothesis"] = asr.transcribe(wav)
        pt["wer"] = round(wer(reference_text, pt["hypothesis"]), 4)
        print(f"{pt['pace_setting']:10s} pace={pt['pace_sylps']:.2f}  WER={pt['wer']:.3f}")
    json.dump(data, open(sweep_json, "w"), ensure_ascii=False, indent=2)
    return data


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--sweep", action="store_true", help="score the rate sweep")
    ap.add_argument("--sentences", default="data/sentences.txt")
    ap.add_argument("--results", default="results")
    ap.add_argument("--model", default=None)
    a = ap.parse_args()

    lines = [l.strip() for l in open(a.sentences, encoding="utf-8") if l.strip()]

    if a.sweep:
        sweep_wer(reference_text=lines[0], model_id=a.model)
    else:
        pairs = []
        for i, ref in enumerate(lines, 1):
            for cond in ("A_vanilla", "B_flatrate", "C_profile"):
                p = os.path.join(a.results, f"s{i:02d}_{cond}.wav")
                if os.path.exists(p):
                    pairs.append((p, ref))
        if not pairs:
            raise SystemExit(f"no wavs found in {a.results} - run evaluate.py first")
        score_dir(pairs, model_id=a.model)
