# Eval report — humanizer-pro vs original humanizer

Blind A/B on `eval/ai_samples/`. Success = pro wins the blind "more human" vote at
a clear margin AND lands closer to the human band more often AND never loses
meaning (`more_faithful` not worse than baseline).

## How to reproduce

```bash
# 1. For each sample, save two rewrites:
#      eval/out/<name>.baseline.txt   (original humanizer)
#      eval/out/<name>.pro.txt        (/humanizer-pro)
# 2. Stylometric table:
python3 eval/run_eval.py --register spontaneous
# 3. Blind verdict per sample via eval/judge_blind.md (X/Y in random order)
```

## Stylometric result (from run_eval.py)

| sample | base_dist | pro_dist | base_self-tells | pro_self-tells | closer-to-human |
|--------|-----------|----------|-----------------|----------------|-----------------|
| 01-tech-opinion | 0.363 | 0.171 | 3 | 1 | **pro** |
| 02-travel | _pending_ | | | | |
| 03-productivity | _pending_ | | | | |
| 04-food | _pending_ | | | | |
| 05-personal | _pending_ | | | | |

Worked example (sample 01): the AI original scores `dist=1.373` (14 tell hits).
The baseline-style scrubbed rewrite drops the tells but over-corrects (flat
rhythm, no contractions, no em dash) -> `dist=0.363`, 3 self-tells. The
register-faithful pro rewrite -> `dist=0.171`, 1 self-tell. Pro is closer to the
human band precisely because it does not scrub the text flat.

`dist` = stylometric distance to the human band (lower is better). `self-tells` =
over-correction flags (lower is better).

## Blind judge result (from judge_blind.md)

| sample | more_human | more_faithful |
|--------|-----------|---------------|
| _pending_ | | |

## Verdict

- more-human win rate (pro): _pending_
- closer-to-human (stylometric): _pending_
- meaning preserved: _pending_

> Status: harness in place; rewrites not yet generated. Fill this in after the
> first run.
