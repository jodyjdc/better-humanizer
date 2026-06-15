---
name: humanizer-pro
version: 0.1.0
description: |
  Measured, self-improving rewriter. Generates several candidate rewrites,
  scores each with a hybrid scorer (std-lib stylometrics + an LLM judge panel)
  against the real human distribution for a register, applies vetoes, keeps the
  best, and iterates on the judges' critique. Targets the human band (floor AND
  ceiling) so it never over-corrects into a machine-laundered tell. v1 register:
  spontaneous. Explicit non-goal: defeating commercial AI detectors.
license: MIT
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - AskUserQuestion
---

# humanizer-pro

Rewrite AI-sounding text into prose that sits inside the human distribution for
its register, and **prove** it with a score instead of trusting vibes. This is the
measured successor to the original `humanizer` skill: same pattern knowledge (now
in `lexicons/ai_tells.json`), plus measurement, register awareness, and
anti-over-correction.

**Platform note.** Claude Code loads this file as the `/humanizer-pro` skill. Codex
users enter through [`AGENTS.md`](AGENTS.md), which maps the Claude Code tool names
below (`Bash`, `Read`/`Write`/`Edit`, `AskUserQuestion`, `Workflow`) to their Codex
equivalents. The loop itself is platform-agnostic and the scoring is a deterministic
Python subprocess, so the result is identical on both.

## Inputs

- `text`: the passage to humanize (the SOURCE).
- `register`: default `spontaneous`. Selects `registers/<register>.md` (the brief)
  and `corpus/<register>/reference-stats.json` (the numeric bands).
- optional **target overrides** (pass the matching flag to `scripts/stylo.py`):
  - `expertise` — `--expertise novice|practitioner|expert` (readability tier within
    the register; default practitioner = the full register).
  - `voice sample` — the user's own writing: run `scripts/build_reference.py
    --voice-sample <dir> --label <name>` first, then score with `--voice <name>` so
    the human target becomes *them*.
  - `persona` — `--persona <name>` (e.g. `reddit-power-user`, `seasoned-journalist`,
    `startup-founder`, `academic-humanist`): a register + tier + lexicon override.
  - Precedence if several are given: persona > voice > expertise > register.

## The loop

### 1. Generate K = 3 candidate rewrites

Read `registers/<register>.md` and follow it. Produce three candidates with
**distinct strategies** so the scorer has real variety to choose from:

- **A — minimal:** fix only the clear tells from `lexicons/ai_tells.json`, touch
  nothing else.
- **B — voice:** rework rhythm and add a point of view; vary sentence length hard;
  let one em dash or one triad stand if natural.
- **C — restructure:** rebuild paragraphs, reorder, cut padding, keep every fact.

Every candidate MUST preserve all source meaning (the meaning judge enforces it).

### 2. Score each candidate

For each candidate, gather two scorecards:

- **Stylometric** (objective): run the scorer over the candidate.
  ```bash
  python3 scripts/stylo.py <candidate-file> --register <register>
  ```
  Read back `stylo_distance`, `self_tell_flags`, `stylo_outlier`, `features`
  (now including the discourse features `transition_density`,
  `structural_opener_rate`, and `paragraph_cv` — high transition/opener rates and
  a low paragraph_cv are document-level AI tells).
- **Judge panel** (semantic): evaluate the candidate with all three lenses, filling
  the templates in `judges/`. In `detector.md` and `register.md`, substitute
  `{{REGISTER}}` and give the judge the register profile (`registers/<register>.md`)
  so formality is judged correctly (passive voice and zero contractions are human in
  scientific writing, not tells):
  - `judges/detector.md` -> `p_ai`, `tells`, `critique`
  - `judges/register.md` -> `register_fit`, `breaks`, `critique`
  - `judges/meaning.md` (needs SOURCE + candidate) -> `fidelity`, `dropped`, ...

### 3. Composite + vetoes

```
judge_score = mean(100 - p_ai, register_fit, fidelity)
composite   = 0.65 * judge_score
            + 0.35 * (100 * (1 - min(stylo_distance, 1)))
            - 5 * len(self_tell_flags)        # over-correction penalty
```

**Hard vetoes** (candidate is disqualified regardless of composite):
- `fidelity < 70` — it changed or dropped meaning.
- `stylo_outlier == true` — a feature is wildly outside the human band.

### 4. Select + iterate (k = 2)

Pick the highest composite among non-vetoed candidates. If the best `composite < 85`
and fewer than `k = 2` iterations have run: take that candidate, concatenate the
`critique` lists from all three judges, and do one **targeted** rewrite that fixes
exactly those points (without introducing new tells or over-correcting). Re-score.
Stop when `composite >= 85` or `k` is hit.

### 5. Output

Return:
1. The final rewrite.
2. A compact **scorecard**: `composite`, `judge_score` breakdown
   (`p_ai`/`register_fit`/`fidelity`), `stylo_distance`, tells removed vs. source,
   discourse status (transition/opener/paragraph_cv), `self_tell_flags` avoided,
   iterations used.

Do **not** run a "delete every em dash" post-pass. Over-correction is a tell; defer
to the bands. Trust the scorecard, not a blanket ban.

## Orchestration

When the `Workflow` tool is available, fan out the K candidates and the 3 judges in
parallel (generate -> score -> select is a clean pipeline). Otherwise run them
sequentially; the logic is identical. The deterministic work (`stylo.py`) always
runs as a subprocess so results are reproducible.

## Pattern reference

The tell catalog is `lexicons/ai_tells.json` (the Wikipedia "Signs of AI writing"
patterns + post-2023 LLMisms + phrase/structure patterns harvested from "Stop Slop"
by Hardik Pandya — throat-clearing, emphasis crutches, business jargon,
meta-commentary, binary contrasts, negative listing, rhetorical setups). It is the
single source of truth, shared by `stylo.py` and the judges. Do not re-list patterns
inline. NB: Stop Slop's register-blind blanket bans (no em dashes / adverbs / passive
/ triads) are deliberately NOT adopted — those are calibrated per-register bands here,
because the data shows a blanket ban is itself a register-specific tell.

## Scope

Registers available now (seven): **spontaneous**, **scientific**, **literary**,
**business**, **journalism**, **social-media**, and **technical-docs**, each with its
own `registers/<name>.md` + calibrated `corpus/<name>/`. They behave very differently
and that is the whole point ("human" is register-specific): scientific tolerates
passive voice, hedging, and zero contractions; business email and social-media run
the highest contraction rates; journalism is sober (near-zero exclamation and
sentence-opening connectives); technical-docs has the widest sentence-length range
and high domain-vocabulary tolerance; literary has ~13x the em-dash tolerance of
casual prose, where the main tell is *hollow* figuration, not its presence. Each new
register reuses this exact machinery. The target is always the human distribution for
the register, never a specific commercial detector.
