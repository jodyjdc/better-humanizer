# humanizer-pro

A measured, self-improving rewriter. It turns AI-sounding text into prose that sits
inside the **real human distribution** for its register, and proves it with a score
instead of trusting vibes.

It is the successor to [`blader/humanizer`](https://github.com/blader/humanizer) — a
single static prompt that deletes 33 known AI "tells". humanizer-pro keeps that
pattern knowledge but adds the three things a static checklist can't do.

## The core idea

1. **Measurement, not vibes.** A hybrid scorer rates every rewrite:
   - `scripts/stylo.py` — standard-library stylometrics (sentence-length
     burstiness, lexical diversity/MTLD, function-word fingerprint, punctuation
     rates, tell counts) measured against a human reference band.
   - an LLM **judge panel** (`judges/`) — an adversarial detector lens, a
     register-fidelity lens, and a meaning-fidelity lens.
2. **Register awareness.** "Human" is register-specific. Three registers ship:
   **spontaneous**, **scientific**, and **literary**, each with its own
   `registers/<name>.md` + calibrated `corpus/<name>/`. They differ sharply:
   scientific treats passive voice and zero contractions as human; literary
   tolerates ~13x the em dashes of casual prose and the highest rhythm variation,
   where the tell is *hollow* figuration, not its presence. Same machinery,
   recalibrated per register.
3. **Anti-over-correction.** Every human band has a floor **and** a ceiling. Zero
   em dashes, flat sentence rhythm, or zero contractions get flagged as
   `self_tell_flags` — because over-laundered prose is its own tell. The original
   only ever penalized the *presence* of a tell, never the over-correction.

A loop generates several candidate rewrites, scores them, vetoes any that lose
meaning or fall outside the human band, keeps the best, and iterates on the judges'
critique. That feedback loop is the "self-improvement".

## Run it

```bash
# Score any text against the human band for a register:
python3 scripts/stylo.py path/to/text.txt --register spontaneous

# (Re)calibrate the human bands. The shipped reference-stats.json is already
# calibrated from 120 real human texts; rebuild or extend it with:
python3 scripts/fetch_corpus.py                       # pull IMDB+Yelp (pre-2022, human)
python3 scripts/build_reference.py --register spontaneous
#   or drop your own *.txt under corpus/spontaneous/ and rerun build_reference.

# Rewrite with the full loop (inside Claude Code / OpenCode):
/humanizer-pro    # then paste text; see SKILL.md for the loop

# Prove it beats the original (blind A/B):
python3 eval/run_eval.py --register spontaneous
python3 eval/run_eval.py --register scientific
python3 eval/run_eval.py --register literary
```

Run the tests (zero dependencies):

```bash
python3 tests/run.py
```

## How it differs from the original

| | blader/humanizer | humanizer-pro |
|---|---|---|
| Output check | none | stylometric distance + 3-judge panel |
| Voice | one default | register profiles + corpus calibration |
| Em dashes / triads | hard-banned | targeted to the human band (floor + ceiling) |
| Proof it works | trust | blind A/B eval harness |

Against bands calibrated from real human text, humanizer-pro lands closer to the
human distribution on **5/5** spontaneous, **4/4** scientific, and **4/4** literary
samples — three registers with very different norms, same machinery. The em-dash
ceiling alone runs from 0.00 (scientific) to 1.71 (literary), which is why a
one-size humanizer damages most registers. See [`eval/REPORT.md`](eval/REPORT.md).

## Explicit non-goal

humanizer-pro does **not** target commercial AI detectors (GPTZero, Turnitin, etc.).
No detector APIs, no watermark removal, no perplexity-gaming a named classifier. The
target is the human reference distribution — which is more honest and more durable
(classifiers change monthly; human prose statistics don't). The aim is genuinely
good, register-faithful writing, not deception.

## Design

Full spec: [`docs/superpowers/specs/2026-06-12-humanizer-pro-design.md`](docs/superpowers/specs/2026-06-12-humanizer-pro-design.md).
Build plan: [`docs/superpowers/plans/2026-06-12-humanizer-pro.md`](docs/superpowers/plans/2026-06-12-humanizer-pro.md).

Tell catalog adapted from [Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing).
