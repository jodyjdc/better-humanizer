# Eval report — humanizer-pro (objective, reproducible)

Deterministic stylometric benchmark over `eval/ai_samples/` (25 AI-generated
passages across 7 registers). Each passage is rewritten two ways and scored
against the human band calibrated from real human texts (see `corpus/<reg>/PROVENANCE.md`):

- **AI** — the original AI-generated source (the starting point).
- **baseline** — original-humanizer style: tells deleted, but scrubbed flat.
- **pro** — humanizer-pro, register-faithful with a floor AND a ceiling.

`distance` = composite stylometric distance to the human band (lower = more human).
`self-tells` = over-correction flags (scrubbed below a human floor; lower = better) —
the failure mode the original humanizer causes and humanizer-pro is built to avoid.

## Result

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

**Headline:** across all 25 samples, humanizer-pro cuts the distance to the
human band by **76%** vs the raw AI text (1.26 → 0.30),
beats the original humanizer (0.73 → 0.30), and does it with
**1.4 → 0.1** over-correction self-tells — because the
baseline's tell-scrubbing pushes text *out* of the human band (flat rhythm, no
contractions), exactly what the floor-and-ceiling design prevents.

## Reproduce

```bash
python3 eval/benchmark.py           # this table, deterministic
python3 eval/benchmark.py --check   # regression gate (exit 1 if pro stops winning)
python3 eval/run_eval.py --register literary   # per-register, per-sample detail
```

The semantic half (does it keep meaning and read human?) is the blind judge panel in
`eval/judge_blind.md`, run with a model that was not in the rewrite loop.
