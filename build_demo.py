#!/usr/bin/env python3
"""
Builds a self-contained A/B demo page from results/results.csv.

Two modes: labelled (for your examiner) and blind (for listening without
knowing which condition you're hearing). Audio is embedded as base64 so the
page is one file you can email or open anywhere.
"""
import base64
import csv
import json
import os

HTML = """<!DOCTYPE html>
<meta charset="utf-8"><title>Dhvani — delivery transfer demo</title>
<style>
 :root{--fg:#1a1a1a;--mut:#666;--line:#e2e2e2;--bg:#fff}
 @media(prefers-color-scheme:dark){:root{--fg:#e8e8e8;--mut:#999;--line:#333;--bg:#161616}}
 body{font:16px/1.6 system-ui,sans-serif;color:var(--fg);background:var(--bg);
      max-width:820px;margin:40px auto;padding:0 20px}
 h1{font-size:22px;font-weight:500;margin:0 0 4px} h2{font-size:17px;font-weight:500;margin:32px 0 8px}
 .sub{color:var(--mut);margin:0 0 24px}
 table{border-collapse:collapse;width:100%;margin:8px 0 24px;font-size:14px}
 th,td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--line)}
 th{font-weight:500;color:var(--mut)}
 .card{border:1px solid var(--line);border-radius:10px;padding:14px 16px;margin:10px 0}
 .lbl{font-weight:500} .meta{color:var(--mut);font-size:13px;margin-top:4px}
 audio{width:100%;margin-top:8px}
 button{font:inherit;padding:6px 14px;border:1px solid var(--line);border-radius:6px;
        background:transparent;color:var(--fg);cursor:pointer}
 .hidden{display:none}
 .kn{font-size:17px;margin:14px 0 2px}
</style>
<h1>ಧ್ವನಿ — Kannada TTS delivery transfer</h1>
<p class="sub">Same text, three conditions. Descriptions set the voice; measured
statistics set the pace and pause structure.</p>

<button onclick="toggleBlind()">Toggle blind mode</button>

<h2>Measured results</h2>
__TABLE__

<h2>Samples</h2>
__SAMPLES__

<script>
let blind=false;
function toggleBlind(){
  blind=!blind;
  document.querySelectorAll('[data-cond]').forEach((e,i)=>{
    e.textContent = blind ? 'Clip '+(i+1) : e.dataset.cond;
  });
  document.querySelectorAll('.meta').forEach(e=>e.classList.toggle('hidden',blind));
}
</script>
"""

NAMES = {"A_vanilla": "A — vanilla (moderate pace, no chunking)",
         "B_flatrate": "B — flat rate (fast caption, no chunking)",
         "C_profile": "C — profile transfer (fast caption + measured pauses)"}


def b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def build(results_csv="results/results.csv", sentences="data/sentences.txt",
          out="docs/demo.html"):
    rows = list(csv.DictReader(open(results_csv, encoding="utf-8")))
    lines = [l.strip() for l in open(sentences, encoding="utf-8") if l.strip()]

    conds, agg = [], {}
    for r in rows:
        agg.setdefault(r["condition"], []).append(r)
    thead = ("<tr><th>Condition</th><th>Pace (syl/s)</th><th>Pace error</th>"
             "<th>Pause w-dist</th><th>Speech density</th></tr>")
    tbody = ""
    for c in ("A_vanilla", "B_flatrate", "C_profile"):
        if c not in agg:
            continue
        g = agg[c]
        mean = lambda k: sum(float(x[k]) for x in g) / len(g)
        tbody += (f"<tr><td>{NAMES[c]}</td><td>{mean('pace_sylps'):.2f}</td>"
                  f"<td>{mean('pace_err_sylps'):.3f}</td>"
                  f"<td>{mean('pause_wdist'):.1f}</td>"
                  f"<td>{mean('speech_density_pct'):.1f}%</td></tr>")
    table = f"<table>{thead}{tbody}</table>"

    samples = ""
    by_sent = {}
    for r in rows:
        by_sent.setdefault(int(r["sentence"]), []).append(r)
    for s in sorted(by_sent):
        text = lines[s - 1] if s - 1 < len(lines) else f"Sentence {s}"
        samples += f'<p class="kn">{text}</p>'
        for r in sorted(by_sent[s], key=lambda x: x["condition"]):
            if not os.path.exists(r["file"]):
                continue
            samples += (
                f'<div class="card"><div class="lbl" data-cond="{NAMES[r["condition"]]}">'
                f'{NAMES[r["condition"]]}</div>'
                f'<div class="meta">pace {float(r["pace_sylps"]):.2f} syl/s · '
                f'{r["pause_count"]} pauses · median {r["pause_median_ms"]}ms</div>'
                f'<audio controls src="data:audio/wav;base64,{b64(r["file"])}"></audio></div>')

    os.makedirs(os.path.dirname(out), exist_ok=True)
    html = HTML.replace("__TABLE__", table).replace("__SAMPLES__", samples)
    open(out, "w", encoding="utf-8").write(html)
    size = os.path.getsize(out) / 1e6
    print(f"wrote {out}  ({size:.1f} MB, audio embedded)")
    return out


if __name__ == "__main__":
    build()
