# humanizer-pro — design spec

Date: 2026-06-12
Status: approved (brainstorming complete)
Author: Jody + Claude

## Problem

`blader/humanizer` is a single 621-line prompt: a static checklist of 33 AI "tells" to delete, plus a draft -> audit -> final loop. It works as a surface cleaner but is not state of the art:

1. **No measurement.** It claims to humanize but never verifies the result. There is no score, no feedback loop, no way to know if a rewrite is actually more human or just different.
2. **One voice.** It has a single default register (opinionated blog voice) plus shallow "match a sample" calibration. Human writing differs hard by register: a paper *must* use passive voice, hedging, nominalizations; a personal post lives on fragments, asides, and uneven rhythm. The original would "fix" the paper into something less human.
3. **It self-betrays.** Hard bans (zero em dashes, never use rule-of-three, etc.) create a *new* tell: the absence. Real human text uses em dashes and triads at nonzero rates. The original only ever penalizes the presence of a tell, never the over-correction.

## Goal

A measured, self-improving rewriter whose target is **the real human distribution for a given register**, not "fool a detector." Output that lands inside the human band for its register while preserving the source meaning. v1 proves the machinery on one register and beats the original in a blind head-to-head.

### Non-goals (explicit)

- **No optimization against commercial detectors** (GPTZero, Turnitin, etc.). No calls to their APIs, no watermark removal, no perplexity-gaming a named classifier. Target is the human reference distribution. This is more honest and more durable (classifiers change monthly; human prose statistics do not).
- v1 covers **one register only**: spontaneous / colloquial (blog, post, email, opinion). Scientific and literary are phase 2: same machinery, new register profile + corpus.
- No model-based perplexity in v1 (reference n-gram surprisal proxy instead). Optional later.
- No web UI, no hosted service. Deliverable is a Claude Code skill + support scripts.

## Success criterion

A blind A/B eval harness: the same set of AI-generated spontaneous texts, each rewritten by (a) the original humanizer and (b) humanizer-pro. An **independent** judge panel (different prompts/personas from the loop's judges, so we do not grade our own homework) picks which output is (1) more human and (2) more faithful to source meaning. humanizer-pro succeeds when it:

- wins the blind "more human" head-to-head at a clear margin, AND
- lands inside the human stylometric band more often, AND
- does not lose source meaning (meaning-fidelity floor must hold).

Numbers, not vibes.

## Architecture

The loop:

```
input text + register
   |
   |-- GENERATE K diverse candidate rewrites (different strategies / temperature)
   |
   '-- for each candidate:
         |- stylo.py     -> objective scorecard (distance to human distribution)
         '- judge panel  -> semantic scorecard (meaning / register / residual tells)
              |
              v
         COMPOSITE score + hard vetoes  ->  select best
              |
         if best < threshold and budget remains:
              critique -> targeted rewrite -> re-score   (max k iterations)
              |
              v
         final text + scorecard (tells removed, self-tells avoided, iterations used)
```

The LLM judge is **primary**; stylometrics act as **veto / guardrail**. The judge panel's critique is the gradient that steers the next iteration. That feedback loop is the "self-improvement."

## Components

### 1. `SKILL.md` — orchestrator

The `/humanizer-pro` entry point. Defines the loop, loads the register profile, drives generation of K candidates, calls `stylo.py`, runs the judge panel (as sub-agents or inline lenses), reads scores, applies vetoes, selects, iterates, emits the final text + scorecard. Where the `Workflow` tool is available it MAY orchestrate the fan-out (K candidates + parallel judges); otherwise it runs sequentially. Scripts stay the deterministic core so the skill is portable.

### 2. `registers/spontaneous.md` — register profile

Describes what "human spontaneous" looks like, and is the single source of register truth:

- **Stylometric target bands** (floor + ceiling, not just ceiling): sentence-length mean and coefficient of variation (burstiness), paragraph-length variance, TTR/MTLD range, function-word ratios, contraction rate, and punctuation rates *including human-rate em dash / comma / parenthetical use*.
- **Generation guidance**: allow contractions, fragments, asides, mild redundancy, a personal stance, uneven rhythm.
- **Tell priority**: which of the 33 patterns matter most in this register (and which are *fine* here, e.g., a stray em dash, one triad).

### 3. `scripts/stylo.py` — stylometric scorer

**Python standard library only** (no pip; runs anywhere). Input: text + register. Output: JSON.

Features computed (all pure-Python feasible):

- sentence + token segmentation
- sentence-length mean, SD, coefficient of variation (burstiness); paragraph-length variance
- lexical diversity: TTR + MTLD; hapax ratio; mean word length
- function-word frequency vector -> cosine distance to the register reference vector
- punctuation rates: comma, period, em dash, en dash, semicolon, colon, parentheses, `?`, `!`
- contraction rate
- structural tells: title-case headings, boldface count, emoji count, bullet count
- AI tell-lexicon hit rate (shared `lexicons/ai_tells.json`) + a rule-of-three heuristic
- perplexity proxy: n-gram surprisal vs the reference corpus (true model perplexity is phase 2)

Output JSON contains, per feature: value, human-band target (min/max), z-distance; plus a **composite stylometric distance** and a list of **self-tell flags**.

**Self-tell flags are the key novelty.** The human band has a floor *and* a ceiling. So `em_dash_rate == 0` when the human floor is > 0, or `sentence_length_cv` below the human floor, are flagged as non-human. Anti-over-correction becomes a measurable signal. The original cannot do this.

### 4. `scripts/build_reference.py` — reference builder

Ingests `corpus/spontaneous/*.txt`, computes per-feature distribution (mean, SD -> bands), writes `corpus/spontaneous/reference-stats.json`. Precomputed so runtime scoring is fast and offline.

Until a real corpus is populated, `reference-stats.json` ships with **clearly-labeled heuristic starting bands** for English spontaneous register. They are marked `"calibrated": false` and are meant to be overwritten by `build_reference.py` on real data. No fabricated citations; they are explicit heuristics.

### 5. `corpus/spontaneous/` — reference corpus

~30-50 genuinely human, license-clean spontaneous texts, biased toward pre-2022 (pre-ChatGPT = guaranteed human). `CORPUS.md` documents sourcing rules and safe sources. The user's own writing can populate the corpus, which doubles as voice personalization: the "human" target becomes *them*.

This is the main work/risk item. v1 ships the machinery + heuristic defaults + the protocol; the corpus grows over time.

### 6. `judges/` — LLM judge panel

Three independent lenses (distinct personas to fight correlated blind spots):

- `detector.md` (adversarial): "You are an expert AI-text detector. List concrete tells. Give P(AI) 0-100 with reasons." This is the gradient.
- `register.md`: "Does this read like genuine human *spontaneous* writing? Score 0-100. What breaks the register?"
- `meaning.md`: "Compare to source. List dropped / added / distorted information." Guards against fluent-but-infidelity.

Aggregate -> judge score + a concrete critique list (the feedback for the next iteration).

### 7. `lexicons/ai_tells.json` — shared tell pack

The 33 Wikipedia patterns as a machine-readable lexicon / regex pack, consumed by both `stylo.py` (counting) and the judges (reference). Single source of truth ported from the original SKILL.md.

### 8. `eval/` — proof harness

- `ai_samples/*.txt`: holdout AI-generated spontaneous texts.
- `run_eval`: runs baseline (original humanizer) vs humanizer-pro on each, then a blind independent judge panel + stylometric distance pick the winner.
- `REPORT.md`: win-rate, mean stylo-distance-to-human, tell reduction, meaning-fidelity.

The eval judges are independent of the loop judges so the system cannot win by gaming its own scorer.

## Data flow

```
input + register
  -> generate K candidates
  -> each candidate -> { stylo.py -> stylo scorecard, judge panel -> judge scorecard }
  -> composite + vetoes (meaning floor; self-tell penalty; stylo-outlier reject)
  -> select best
  -> if best < threshold: critique -> targeted rewrite -> re-score (<= k iterations)
  -> final text + scorecard
```

## Scoring detail

- `composite = w_judge * judge_score + w_stylo * (1 - normalized_stylo_distance)`
- **Hard vetoes** (reject candidate regardless of composite):
  - meaning-fidelity below floor (information lost or distorted)
  - stylometric outlier vs human band (any feature far outside floor/ceiling)
- **Self-tell penalty**: each self-tell flag (over-correction) subtracts from composite.
- Weights `w_judge > w_stylo` (judge primary). Exact weights tuned during build; defaults documented in `SKILL.md`.

## File layout

```
Better Humanizer/
  SKILL.md
  README.md
  registers/spontaneous.md
  corpus/spontaneous/
    *.txt
    reference-stats.json
    CORPUS.md
  scripts/
    stylo.py
    build_reference.py
  judges/{detector,register,meaning}.md
  lexicons/ai_tells.json
  eval/
    ai_samples/*.txt
    run_eval
    REPORT.md
  tests/
    test_stylo.py
  docs/superpowers/specs/2026-06-12-humanizer-pro-design.md
```

## Testing

- `tests/test_stylo.py`: unit tests for `stylo.py` — segmentation, each feature on known inputs, tell counting, and self-tell flag logic (floor/ceiling). Golden fixtures for a couple of full texts.
- The eval harness is the integration test for "is it better."
- Build `stylo.py` test-first (TDD): the deterministic core deserves it.

## Build order (for the plan)

1. `lexicons/ai_tells.json` (port the 33 patterns).
2. `scripts/stylo.py` + `tests/test_stylo.py` (TDD), with heuristic default bands.
3. `scripts/build_reference.py` + `corpus/spontaneous/CORPUS.md` + default `reference-stats.json`.
4. `registers/spontaneous.md`.
5. `judges/{detector,register,meaning}.md`.
6. `SKILL.md` (the orchestrator that ties it together).
7. `eval/` harness + a small `ai_samples` set + first `REPORT.md`.
8. `README.md`.

## Open risks

- **Corpus quality** dominates calibration accuracy. Mitigated by shipping heuristic defaults + a clear protocol, and by allowing the user's own writing as reference.
- **Judge correlation**: the loop model judging its own output. Mitigated by adversarial detector persona, independent eval judges, and the objective stylometric veto.
- **Over-fitting the scorer**: the loop could learn to satisfy stylo.py without being more human. Mitigated by the independent eval panel and meaning-fidelity floor.
