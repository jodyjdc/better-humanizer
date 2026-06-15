# humanizer-pro

A measured, self-improving rewriter. It turns AI-sounding text into prose that sits
inside the **real human distribution** for its register, and proves it with a score
instead of trusting vibes.

It is the successor to [`blader/humanizer`](https://github.com/blader/humanizer) — a
single static prompt that deletes 33 known AI "tells". humanizer-pro keeps that
pattern knowledge but adds the three things a static checklist can't do.

**Runs on both Claude Code and Codex.** Claude Code loads `SKILL.md` as the
`/humanizer-pro` skill; Codex enters through `AGENTS.md`. Same loop, same
deterministic Python scorer — identical results either way.

## The core idea

1. **Measurement, not vibes.** A hybrid scorer rates every rewrite:
   - `scripts/stylo.py` — standard-library stylometrics (sentence-length
     burstiness, lexical diversity/MTLD, function-word fingerprint, punctuation
     rates, tell counts, and document-level discourse structure — transition
     overuse, thesis/summary openers, paragraph uniformity) measured against a
     human reference band.
   - an LLM **judge panel** (`judges/`) — an adversarial detector lens, a
     register-fidelity lens, and a meaning-fidelity lens.
2. **Register awareness.** "Human" is register-specific. Seven registers ship:
   **spontaneous**, **scientific**, **literary**, **business**, **journalism**,
   **social-media**, and **technical-docs**, each with its own `registers/<name>.md`
   + calibrated `corpus/<name>/`. They differ sharply: scientific treats passive
   voice and zero contractions as human; social-media and Enron business email run
   the *highest* contraction rates; journalism is the unexcitable register
   (near-zero exclamation, almost no "Moreover"-style openers); literary tolerates
   ~13x the em dashes of casual prose. Same machinery, recalibrated per register.
3. **Anti-over-correction.** Every human band has a floor **and** a ceiling. Zero
   em dashes, flat sentence rhythm, or zero contractions get flagged as
   `self_tell_flags` — because over-laundered prose is its own tell. The original
   only ever penalized the *presence* of a tell, never the over-correction.

A loop generates several candidate rewrites, scores them, vetoes any that lose
meaning or fall outside the human band, keeps the best, and iterates on the judges'
critique. That feedback loop is the "self-improvement".

## Aim at a specific writer (optional)

Beyond "the average human in register X", you can target a *specific* writer — all
optional, all measured:

- **Expertise** — `--expertise novice|practitioner|expert`. Each register is split
  into readability terciles (Flesch-Kincaid grade); `expert` tolerates longer,
  denser prose, `novice` keeps it simple. Default `practitioner` = the full register
  (unchanged).
- **Voice** — calibrate your own bands from your writing and target *you*:
  `python3 scripts/build_reference.py --voice-sample mydir/ --label me`, then
  `python3 scripts/stylo.py text.txt --voice me`.
- **Personas** — `--persona reddit-power-user` (or `seasoned-journalist`,
  `startup-founder`, `academic-humanist`): a register + expertise tier + a curated
  lexicon of what to allow or forbid for that voice.

## Run it

```bash
# Score any text against the human band for a register:
python3 scripts/stylo.py path/to/text.txt --register spontaneous

# Or target an expertise level / persona / your own voice:
python3 scripts/stylo.py path/to/text.txt --register scientific --expertise expert
python3 scripts/stylo.py path/to/text.txt --persona reddit-power-user

# (Re)calibrate the human bands. The shipped reference-stats.json is already
# calibrated from 120 real human texts; rebuild or extend it with:
python3 scripts/fetch_corpus.py                       # pull IMDB+Yelp (pre-2022, human)
python3 scripts/build_reference.py --register spontaneous
#   or drop your own *.txt under corpus/spontaneous/ and rerun build_reference.

# Rewrite with the full loop:
#   Claude Code / OpenCode:  /humanizer-pro   (loads SKILL.md)
#   Codex:                   open the repo and ask to humanize  (AGENTS.md routes it)
# Both follow the same loop; the scoring is a deterministic Python subprocess.

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
human distribution on every sample across seven registers — **5/5** spontaneous,
**4/4** scientific, **4/4** literary, and **3/3** each for business, journalism,
social-media, and technical-docs (**25/25** total), same machinery throughout. The
contraction ceiling alone runs from 0.00 (scientific — zero is human there) to 5.78
(business email), and the em-dash ceiling from 0.00 to 1.71, which is why a one-size
humanizer damages most registers. See [`eval/REPORT.md`](eval/REPORT.md).

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
