# humanizer-pro

A measured, self-improving rewriter. It turns AI-sounding text into prose that sits
inside the **real human distribution** for its register, and proves it with a score
instead of trusting vibes.

It is the successor to [`blader/humanizer`](https://github.com/blader/humanizer) — a
single static prompt that deletes 33 known AI "tells". humanizer-pro keeps that
pattern knowledge but adds the three things a static checklist can't do.

> **▶ Try it now, no install:** **[the human-band playground](https://jodyjdc.github.io/better-humanizer/web/playground.html)** —
> paste text, see how far it sits from the human band, per feature. It runs the *exact
> same* scorer as `scripts/stylo.py` (ported to JS and verified identical to 4 decimals),
> entirely in your browser. Nothing is uploaded.

**Built for Claude Code, compatible with any file-aware agent.** Claude Code loads
`SKILL.md` as the `/humanizer-pro` skill (first-class); Codex, Antigravity, OpenCode,
and other file-aware agents enter through `AGENTS.md`. Same loop, same deterministic
Python scorer — `scripts/stylo.py` returns identical numbers on every platform, so the
measurement is reproducible everywhere. Only the model doing the rewriting differs.

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

## Proof (reproducible, deterministic)

25 AI-generated passages across all 7 registers, each scored by the standard-library
stylometric scorer against human-calibrated bands. Three versions of every passage:
the **raw AI** text, the **original humanizer**, and **humanizer-pro**.

| register | n | dist: AI → base → **pro** | over-correction self-tells (base → **pro**) | pro closest |
|---|--:|---|---|--:|
| business | 3 | 0.37 → 0.40 → **0.23** | 1.0 → **0.0** | 67% |
| journalism | 3 | 3.82 → 1.62 → **0.10** | 1.3 → **0.0** | 100% |
| literary | 4 | 0.66 → 0.81 → **0.47** | 2.0 → **0.0** | 100% |
| scientific | 4 | 0.89 → 0.80 → **0.30** | 0.5 → **0.2** | 100% |
| social-media | 3 | 1.18 → 0.48 → **0.23** | 2.0 → **0.0** | 100% |
| spontaneous | 5 | 1.46 → 0.72 → **0.42** | 1.8 → **0.2** | 100% |
| technical-docs | 3 | 0.65 → 0.27 → **0.19** | 1.0 → **0.0** | 100% |
| **all** | **25** | **1.26 → 0.73 → 0.30** | **1.4 → 0.1** | **96%** |

`distance` = composite stylometric distance to the human band (lower = more human).
`self-tells` = over-correction flags (lower = better). Across all 25, humanizer-pro cuts
the distance to the human band by **76%** vs raw AI (1.26 → 0.30), beats the original
humanizer (0.73 → 0.30), and does it with near-zero over-correction (1.4 → 0.1). It is
the most-human of the three on **96%** of samples.

```bash
python3 eval/benchmark.py            # reproduce this exact table
python3 eval/benchmark.py --check    # regression gate: exit 1 if pro stops winning
```

> Honest read: `distance` is a stylometric measure, not a detector score (see the
> explicit non-goal below). The numbers are reproducible; **business** is the one
> register where pro is not always closest (three short emails where the AI text already
> sat near the band). The semantic half — does it keep meaning and read human? — is the
> blind judge panel in [`eval/judge_blind.md`](eval/judge_blind.md).

## Use it in CI — the `humanize-check` GitHub Action

Gate AI-slop out of your docs, blog, or release notes the same way you gate failing
tests. The action scores changed files against the human band and fails the build (or
just warns) on anything that reads synthetic — zero dependencies, the scorer and
corpora ship in the action.

```yaml
# .github/workflows/no-slop.yml
name: no-slop
on: [pull_request]
jobs:
  humanize-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: jodyjdc/better-humanizer@v1.2.0
        with:
          files: "docs/**/*.md, README.md"   # comma-separated globs
          register: spontaneous              # pick the register for your content
          max-distance: "0.6"                # calibrated default; raise to be lenient
          fail-on-flag: "true"               # "false" = annotate only, never fail
```

It writes a per-file verdict table to the PR's job summary and exposes `flagged` /
`checked` outputs. The default ceiling `0.6` is **calibrated, not guessed**:
`python3 eval/calibrate.py` measures an **AUC of 0.94** separating raw AI text from
humanizer-pro output, with ~0 false-flags on the eval set at that cutoff. (Honest
scope: that separates AI from *humanized* text — the operational question a gate
answers — not certified human-vs-AI on arbitrary prose.)

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

# Prove it (deterministic, all 7 registers):
python3 eval/benchmark.py                       # the headline table above
python3 eval/run_eval.py --register literary    # per-register, per-sample detail
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
| Proof it works | trust | reproducible benchmark (−76% distance) + blind A/B |

The per-register calibration is why a one-size humanizer damages most registers: the
contraction ceiling alone runs from 0.00 (scientific — zero contractions is human there)
to 5.78 (business email), and the em-dash ceiling from 0.00 to 1.71. Same machinery,
recalibrated per register — and the [Proof](#proof-reproducible-deterministic) table
above shows it lands closest to the human band on 96% of 25 samples across all seven.
Full numbers in [`eval/REPORT.md`](eval/REPORT.md).

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
