# Report outline

Numbers already measured are filled in. `[FILL]` marks what your runs produce.
Write sections 4 and 6 first — they're the ones that carry marks.

---

## 1. Introduction

The problem: Indic TTS for Kannada produces intelligible but flat speech. A
news-presenter register is defined largely by *timing* — fast rate, short breath
groups, frequent short pauses — and no current Kannada TTS system exposes control
over timing at that granularity.

State the contribution plainly:

> Natural-language voice descriptions provide coarse prosodic control. This work
> measures delivery statistics from a reference recording and uses them to drive
> chunking and pause insertion, achieving numeric prosodic targets that the
> description interface alone cannot express.

## 2. Related work

- AI4Bharat IndicF5 — reference-audio cloning, 11 languages, 1417 hours
- AI4Bharat Indic Parler-TTS — description-conditioned, 21 languages, 1806 hours
- Prosody transfer literature generally
- Note the gap: description conditioning is coarse and unquantified

## 3. Method

### 3.1 Delivery profile extraction

Frame-level RMS at 25 ms / 10 ms hop, adaptive VAD threshold at the 15th
percentile plus 35% of the range. Pauses are silences ≥ 100 ms; breath groups are
speech runs ≥ 120 ms. Speaking rate via energy-envelope peak counting as a
syllable-nucleus proxy. F0 by autocorrelation, 70–320 Hz.

### 3.2 Akshara-based chunking

Kannada syllable count = independent vowels + consonants not carrying a virama
(U+0CCD). Target phrase length derived from the reference p90 breath group.

### 3.3 Synthesis

Per-phrase generation, RMS normalisation to a common level, concatenation with
silences drawn from the measured pause distribution.

## 4. Results

### 4.1 Reference profile

Measured from a 52.7 s news segment:

| Metric | Value |
|---|---|
| Speaking rate | 6.65 syl/sec |
| Speech density | 68.2% |
| Breath groups | 77 (median 0.36 s, p90 0.98 s) |
| Pauses | 30 (median 169 ms, p90 521 ms, max 960 ms) |
| Pitch span p10–p90 | 8.44 semitones |
| Crest factor | 17.5 dB |

**Report the contamination honestly.** Spectral centroid came out at 484 Hz with
1.7% of energy above 2 kHz — implausible for clean speech, indicating a music bed
in the source. Timing statistics are robust to this; spectral statistics are not,
and were excluded. The measured 0.36 s median breath group also reflects
over-segmentation by energy-based VAD, so p90 was used as the phrase anchor.

Writing this up is worth more than hiding it.

### 4.2 Condition comparison

| Condition | Pace (syl/s) | Pace error | Pause w-dist | WER | MOS nat. | MOS presenter |
|---|---|---|---|---|---|---|
| A vanilla | [FILL] | [FILL] | [FILL] | [FILL] | [FILL] | [FILL] |
| B flat rate | [FILL] | [FILL] | [FILL] | [FILL] | [FILL] | [FILL] |
| C profile | [FILL] | [FILL] | [FILL] | [FILL] | [FILL] | [FILL] |

The expected pattern: B and C converge on pace error, C wins clearly on pause
w-dist. That divergence is the argument — rate control alone does not reproduce
pause structure.

If B beats C on MOS despite worse w-dist, say so. Concatenation seams are a real
cost and reporting them strengthens the work.

### 4.3 Rate sweep

Plot WER and MOS against measured speaking rate. Mark the crossover.

> `[FILL]` Intelligibility degraded beyond approximately [X] syl/sec, below the
> reference speaker's 6.65 syl/sec, indicating that human presenter rates are not
> directly achievable with current synthesis without loss.

That negative result, if it holds, is the most interesting thing in the report.

## 5. Ethics and licensing

Only aggregate timing statistics were extracted from the reference; no voice was
cloned and no audio redistributed. Analysis for research purposes falls under
fair dealing, Section 52(1)(a), Copyright Act 1957. The decision not to clone the
reference speaker was a design constraint from the outset, motivated by Indian
personality-rights case law on synthetic voice.

## 6. Limitations

1. Target pause distribution reconstructed as lognormal from median and p90 rather
   than the raw gap array — affects absolute w-dist, not condition ranking.
2. Independent per-chunk generation causes level and timbre drift; RMS
   normalisation only partly mitigates.
3. Syllable counting is an akshara approximation, not phonological syllabification.
4. Single reference recording, single register.
5. MOS N = [FILL]; differences between adjacent conditions likely not significant.

## 7. Future work

- Raw pause arrays instead of reconstructed distributions
- Crossfaded concatenation or single-pass generation with prosody conditioning
- Multiple reference registers (sports, weather, documentary)
- Closed-loop caption search: automatically adjust wording until error converges

---

## Figures to produce

1. Pipeline architecture
2. Reference vs synthesised pause histograms, overlaid
3. WER and MOS against speaking rate, with crossover marked
4. Waveform and energy envelope, condition A vs C, same sentence

Figure 3 is the one examiners will look at. Make it good.
