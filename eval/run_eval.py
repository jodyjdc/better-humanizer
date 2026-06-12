#!/usr/bin/env python3
"""Blind A/B eval: original humanizer vs humanizer-pro on the same AI samples.

Deterministic part (this script): stylometric distance-to-human for each
system's rewrite of each sample. Semantic part: a blind judge
(eval/judge_blind.md), run by the agent, decides which rewrite is more human and
more faithful WITHOUT knowing which system produced it. This script handles
discovery + the stylometric table; it does not call an LLM.

Workflow:
  1. For each eval/ai_samples/<name>.txt, generate two rewrites:
       - baseline (original humanizer)  -> eval/out/<name>.baseline.txt
       - pro      (/humanizer-pro)      -> eval/out/<name>.pro.txt
  2. python3 eval/run_eval.py            # stylometric table
  3. Run eval/judge_blind.md per sample  # blind human-ness + fidelity verdict
  4. Fill eval/REPORT.md
"""
import argparse
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "scripts"))
import stylo  # noqa: E402


def samples():
    return sorted((HERE / "ai_samples").glob("*.txt"))


def out_paths(stem):
    return HERE / "out" / f"{stem}.baseline.txt", HERE / "out" / f"{stem}.pro.txt"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--register", default="spontaneous")
    ap.add_argument("--dry-run", action="store_true",
                    help="list samples + rewrite status, then exit")
    args = ap.parse_args(argv)

    ss = samples()
    if not ss:
        print("no samples in eval/ai_samples/", file=sys.stderr)
        return 1

    if args.dry_run:
        print(f"{len(ss)} sample(s):")
        for s in ss:
            b, p = out_paths(s.stem)
            print(f"  {s.name:22} baseline={'ok' if b.exists() else 'missing':7} "
                  f"pro={'ok' if p.exists() else 'missing'}")
        return 0

    print(f"{'sample':22} {'base_dist':>9} {'pro_dist':>9} "
          f"{'base_self':>9} {'pro_self':>9}  winner")
    rows, pending = [], 0
    for s in ss:
        b, p = out_paths(s.stem)
        if not (b.exists() and p.exists()):
            pending += 1
            print(f"{s.name:22} {'--':>9} {'--':>9}  (rewrites pending)")
            continue
        sb = stylo.score(b.read_text(encoding="utf-8"), args.register)
        sp = stylo.score(p.read_text(encoding="utf-8"), args.register)
        winner = "pro" if sp["stylo_distance"] < sb["stylo_distance"] else "baseline"
        rows.append(winner)
        print(f"{s.name:22} {sb['stylo_distance']:>9.3f} {sp['stylo_distance']:>9.3f} "
              f"{len(sb['self_tell_flags']):>9} {len(sp['self_tell_flags']):>9}  {winner}")

    if rows:
        pro_wins = rows.count("pro")
        print(f"\nstylometric: pro closer-to-human on {pro_wins}/{len(rows)} samples")
    if pending:
        print(f"{pending} sample(s) pending rewrites (save to eval/out/).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
