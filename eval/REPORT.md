# Eval report — humanizer-pro vs original humanizer

Blind A/B on `eval/ai_samples/` (5 AI-generated spontaneous passages). Each is
rewritten two ways and scored against the human band calibrated from 120 real
human texts (see `corpus/spontaneous/PROVENANCE.md`):

- **baseline** = original-humanizer style: tells deleted, but scrubbed flat (no
  contractions, no em dash, even rhythm). `eval/out/<name>.baseline.txt`
- **pro** = humanizer-pro, register-faithful. `eval/out/<name>.pro.txt`

Success = pro is closer to the human band, less over-corrected, and keeps meaning.

## Reproduce

```bash
python3 eval/run_eval.py --register spontaneous   # objective stylometric table
# then, for the independent semantic half, run eval/judge_blind.md per sample
# (X/Y in random order) with a model not in the loop.
```

## Stylometric result (objective, from run_eval.py)

| sample | base_dist | pro_dist | base self-tells | pro self-tells | closer-to-human |
|--------|-----------|----------|-----------------|----------------|-----------------|
| 01-tech-opinion | 0.832 | **0.438** | 2 | 0 | **pro** |
| 02-travel | 0.715 | **0.452** | 2 | 1 | **pro** |
| 03-productivity | 0.574 | **0.452** | 1 | 0 | **pro** |
| 04-food | 0.731 | **0.373** | 2 | 0 | **pro** |
| 05-personal | 0.767 | **0.386** | 2 | 0 | **pro** |
| **mean** | **0.724** | **0.420** | **1.8** | **0.2** | **pro 5/5** |

`dist` = distance to the human band (lower is better). `self-tells` =
over-correction flags (lower is better). Pro wins every sample on the objective
score, and is far less over-corrected: the baseline's tell-scrubbing pushes it
*out* of the human band (flat rhythm, missing contractions), exactly the failure
mode humanizer-pro is built to avoid.

## Blind human-ness verdict (semantic half)

The blind panel (`eval/judge_blind.md`) is wired and runnable. It must be run with
a model **outside the loop** to count as independent — grading rewrites with the
same model that wrote them is not a real test. That run is the remaining step to
fill this section. Indicative read (same-family, not independent): the pro
rewrites carry a first-person point of view and uneven rhythm the baseline
versions lack, and both preserve the source's core claims.

## Verdict

- closer-to-human (objective stylometric): **pro 5/5**, mean distance 0.420 vs 0.724
- over-correction: pro 0.2 self-tells/sample vs baseline 1.8
- meaning: preserved in both (no claims dropped or invented)
- independent blind human-ness vote: pending an out-of-loop model run

## Scientific register (phase 2)

Same machinery, recalibrated on 120 PubMed + arXiv abstracts. The bands invert the
spontaneous ones (longer and more uniform sentences, zero contractions, ~3x AI-tell
tolerance), so the tool no longer treats passive voice or formality as a defect.

| sample | base_dist | pro_dist | closer-to-human |
|--------|-----------|----------|-----------------|
| 01-ml-health | 0.582 | **0.281** | **pro** |
| 02-climate | 0.952 | **0.312** | **pro** |
| 03-crispr | 0.747 | **0.208** | **pro** |
| 04-quantum | 0.739 | **0.184** | **pro** |
| **mean** | **0.755** | **0.246** | **pro 4/4** |

baseline = original-style rewrite (tells removed but register-flattened: shorter,
active, hedges stripped). pro = tells removed while preserving the scientific
register. Pro wins 4/4.

### Register-awareness (the phase-2 proof)

One scientific passage, scored under both registers:

- under **scientific**: dist 0.332, **0** self-tells (in-band, recognized as human)
- under **spontaneous**: dist 0.512, **2** self-tells (its uniform rhythm and zero
  contractions are wrongly flagged as over-correction)

A single-register humanizer would "fix" the paper's passive voice and add
contractions, damaging it. humanizer-pro adapts to the register instead.

## Literary register (phase 3)

Calibrated on 120 human short stories (r/WritingPrompts). Highest tolerance for the
devices other registers flag (em dashes, fragments, varied rhythm).

| sample | base_dist | pro_dist | closer-to-human |
|--------|-----------|----------|-----------------|
| 01-rain | 0.845 | **0.516** | **pro** |
| 02-forest | 0.823 | **0.496** | **pro** |
| 03-love | 0.753 | **0.477** | **pro** |
| 04-noir | 0.815 | **0.385** | **pro** |
| **mean** | **0.809** | **0.469** | **pro 4/4** |

baseline = original-style rewrite (flattened: dashes removed, rhythm evened, imagery
stripped). pro = tells removed while keeping voice, varied rhythm, and specific
imagery. Pro wins 4/4. Notably the flattened baseline (0.81 mean) scores **worse**
than the original AI purple prose (0.66 mean): flattening fiction is the maximal
failure mode, not a fix.

## Three-register fingerprint (the whole thesis in one table)

Bands from real human corpora; same scorer, three calibrations:

| feature | spontaneous | scientific | literary |
|---------|-------------|------------|----------|
| sentence length (mean) | 10–26 | 16–33 | 8–20 |
| rhythm variation (cv) | 0.38–0.76 | 0.23–0.72 | 0.45–0.95 |
| contractions | yes | ~0 | yes |
| em-dash ceiling | 0.13 | 0.00 | **1.71** |
| AI-tell tolerance | 0.21 | 0.61 | 0.19 |

The em-dash row alone refutes a blanket ban: near-zero in science, ~13x higher in
fiction. "Human" is not one thing, and a tool that pretends it is will damage two of
these three registers.
