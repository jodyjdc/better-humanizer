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
