#!/usr/bin/env python3
"""Full benchmark: AI original -> original-humanizer -> humanizer-pro, all registers.

This is the objective, deterministic half of the eval. It scores three versions of
every sample with the same calibrated stylometric scorer and aggregates them, so the
claim "humanizer-pro moves AI text into the human band without over-correcting" is a
reproducible number, not a vibe.

  AI       eval/ai_samples/<reg>/<name>.txt        the AI-generated source
  baseline eval/out/<reg>/<name>.baseline.txt      original-humanizer rewrite
  pro      eval/out/<reg>/<name>.pro.txt           humanizer-pro rewrite

Metrics (per group, lower is better unless noted):
  distance     composite stylometric distance to the human band
  self-tells   over-correction flags (scrubbed below a human FLOOR) — the thing the
               original humanizer causes and humanizer-pro is built to avoid
  tells        raw AI tell-lexicon hits
  pro-best     share of samples where pro is the closest of the three to human (higher
               is better)

Run:    python3 eval/benchmark.py            # print tables, rewrite eval/REPORT.md
        python3 eval/benchmark.py --check    # also exit 1 on regression (CI gate)
        python3 eval/benchmark.py --md       # print only the README headline table
"""
import argparse
import pathlib
import statistics
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "scripts"))
import stylo  # noqa: E402


def _registers():
    return sorted(p.name for p in (HERE / "ai_samples").iterdir() if p.is_dir())


def _score(text, register):
    s = stylo.score(text, register)
    return {
        "dist": s["stylo_distance"],
        "self": len(s["self_tell_flags"]),
        "tells": sum(s["tells"].values()),
        "outlier": s["stylo_outlier"],
    }


def _collect():
    """Return per-register rows: each is (register, [per-sample dict])."""
    out = []
    for reg in _registers():
        rows = []
        for src in sorted((HERE / "ai_samples" / reg).glob("*.txt")):
            base = HERE / "out" / reg / f"{src.stem}.baseline.txt"
            pro = HERE / "out" / reg / f"{src.stem}.pro.txt"
            if not (base.exists() and pro.exists()):
                continue
            ai_s = _score(src.read_text(encoding="utf-8"), reg)
            ba_s = _score(base.read_text(encoding="utf-8"), reg)
            pr_s = _score(pro.read_text(encoding="utf-8"), reg)
            pro_best = pr_s["dist"] <= min(ai_s["dist"], ba_s["dist"])
            rows.append({"ai": ai_s, "base": ba_s, "pro": pr_s, "pro_best": pro_best})
        if rows:
            out.append((reg, rows))
    return out


def _mean(rows, group, field):
    return statistics.fmean(r[group][field] for r in rows)


def _aggregate(collected):
    per_reg = []
    allrows = []
    for reg, rows in collected:
        allrows.extend(rows)
        per_reg.append({
            "register": reg,
            "n": len(rows),
            "ai_dist": _mean(rows, "ai", "dist"),
            "base_dist": _mean(rows, "base", "dist"),
            "pro_dist": _mean(rows, "pro", "dist"),
            "base_self": _mean(rows, "base", "self"),
            "pro_self": _mean(rows, "pro", "self"),
            "ai_tells": _mean(rows, "ai", "tells"),
            "pro_tells": _mean(rows, "pro", "tells"),
            "pro_best": sum(r["pro_best"] for r in rows) / len(rows),
        })
    overall = {
        "n": len(allrows),
        "ai_dist": _mean(allrows, "ai", "dist"),
        "base_dist": _mean(allrows, "base", "dist"),
        "pro_dist": _mean(allrows, "pro", "dist"),
        "base_self": _mean(allrows, "base", "self"),
        "pro_self": _mean(allrows, "pro", "self"),
        "ai_tells": _mean(allrows, "ai", "tells"),
        "pro_tells": _mean(allrows, "pro", "tells"),
        "pro_best": sum(r["pro_best"] for r in allrows) / len(allrows),
    }
    return per_reg, overall


def _headline_md(per_reg, overall):
    lines = [
        "| register | n | dist: AI → base → **pro** | over-correction self-tells (base → **pro**) | pro closest |",
        "|---|--:|---|---|--:|",
    ]
    for r in per_reg:
        lines.append(
            f"| {r['register']} | {r['n']} | "
            f"{r['ai_dist']:.2f} → {r['base_dist']:.2f} → **{r['pro_dist']:.2f}** | "
            f"{r['base_self']:.1f} → **{r['pro_self']:.1f}** | {r['pro_best']*100:.0f}% |"
        )
    lines.append(
        f"| **all** | **{overall['n']}** | "
        f"**{overall['ai_dist']:.2f} → {overall['base_dist']:.2f} → {overall['pro_dist']:.2f}** | "
        f"**{overall['base_self']:.1f} → {overall['pro_self']:.1f}** | **{overall['pro_best']*100:.0f}%** |"
    )
    return "\n".join(lines)


def _report_md(per_reg, overall):
    drop_ai = (1 - overall["pro_dist"] / overall["ai_dist"]) * 100 if overall["ai_dist"] else 0
    return f"""# Eval report — humanizer-pro (objective, reproducible)

Deterministic stylometric benchmark over `eval/ai_samples/` ({overall['n']} AI-generated
passages across {len(per_reg)} registers). Each passage is rewritten two ways and scored
against the human band calibrated from real human texts (see `corpus/<reg>/PROVENANCE.md`):

- **AI** — the original AI-generated source (the starting point).
- **baseline** — original-humanizer style: tells deleted, but scrubbed flat.
- **pro** — humanizer-pro, register-faithful with a floor AND a ceiling.

`distance` = composite stylometric distance to the human band (lower = more human).
`self-tells` = over-correction flags (scrubbed below a human floor; lower = better) —
the failure mode the original humanizer causes and humanizer-pro is built to avoid.

## Result

{_headline_md(per_reg, overall)}

**Headline:** across all {overall['n']} samples, humanizer-pro cuts the distance to the
human band by **{drop_ai:.0f}%** vs the raw AI text ({overall['ai_dist']:.2f} → {overall['pro_dist']:.2f}),
beats the original humanizer ({overall['base_dist']:.2f} → {overall['pro_dist']:.2f}), and does it with
**{overall['base_self']:.1f} → {overall['pro_self']:.1f}** over-correction self-tells — because the
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
"""


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if pro is not the most-human on average (CI gate)")
    ap.add_argument("--md", action="store_true", help="print only the README headline table")
    ap.add_argument("--no-write", action="store_true", help="do not rewrite eval/REPORT.md")
    args = ap.parse_args(argv)

    collected = _collect()
    if not collected:
        print("no scored samples found (need eval/out/<reg>/*.{baseline,pro}.txt)", file=sys.stderr)
        return 1
    per_reg, overall = _aggregate(collected)

    if args.md:
        print(_headline_md(per_reg, overall))
        return 0

    print(_headline_md(per_reg, overall))
    print()
    drop = (1 - overall["pro_dist"] / overall["ai_dist"]) * 100 if overall["ai_dist"] else 0
    print(f"overall: {overall['n']} samples | AI {overall['ai_dist']:.3f} -> "
          f"base {overall['base_dist']:.3f} -> pro {overall['pro_dist']:.3f} "
          f"(-{drop:.0f}% vs AI) | self-tells {overall['base_self']:.2f} -> {overall['pro_self']:.2f} "
          f"| pro closest {overall['pro_best']*100:.0f}%")

    if not args.no_write:
        (HERE / "REPORT.md").write_text(_report_md(per_reg, overall), encoding="utf-8")
        print("wrote eval/REPORT.md")

    if args.check:
        regressed = (overall["pro_dist"] >= overall["ai_dist"]
                     or overall["pro_dist"] >= overall["base_dist"]
                     or overall["pro_self"] > overall["base_self"])
        if regressed:
            print("REGRESSION: humanizer-pro is no longer the most-human on average", file=sys.stderr)
            return 1
        print("check: pass (pro is most-human, least over-corrected)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
