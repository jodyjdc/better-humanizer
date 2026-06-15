#!/usr/bin/env python3
"""Empirically calibrate the human-band gate threshold.

The scorer returns a continuous distance; a *gate* needs a cutoff. Rather than
pick one by feel, this measures how well a distance threshold separates the two
groups we actually have scored data for:

  positive ("slop", should be flagged) = eval/ai_samples/   (raw AI text)
  negative ("ok",   should pass)        = eval/out/*.pro.txt (humanizer-pro output)

It reports the rank AUC, the Youden-optimal threshold, and accuracy at a few round
cutoffs, so the default gate (humanize-check / ubss humanize-score) rests on a
number, not a vibe.

Honest scope: this separates *raw AI* from *humanizer-pro output* — the operational
question a gate answers ("has this been humanized?"). It is NOT a certified
human-vs-AI classifier on published prose; the absolute numbers are optimistic
because the negatives were optimized toward the band. Run:  python3 eval/calibrate.py
"""
import glob
import pathlib
import statistics
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "scripts"))
import stylo  # noqa: E402


def _distances():
    slop, ok = [], []
    for reg_dir in sorted((HERE / "ai_samples").iterdir()):
        if not reg_dir.is_dir():
            continue
        reg = reg_dir.name
        for f in glob.glob(str(HERE / "ai_samples" / reg / "*.txt")):
            slop.append(stylo.score(pathlib.Path(f).read_text(encoding="utf-8"), reg)["stylo_distance"])
        for f in glob.glob(str(HERE / "out" / reg / "*.pro.txt")):
            ok.append(stylo.score(pathlib.Path(f).read_text(encoding="utf-8"), reg)["stylo_distance"])
    return slop, ok


def _auc(slop, ok):
    wins = sum((a > g) + 0.5 * (a == g) for a in slop for g in ok)
    return wins / (len(slop) * len(ok))


def _sweep(slop, ok):
    cands = sorted({round(x, 3) for x in slop + ok})
    best = None
    for c in cands:
        tau = c + 0.0005
        tp = sum(d > tau for d in slop)
        fp = sum(d > tau for d in ok)
        tpr = tp / len(slop)
        fpr = fp / len(ok)
        youden = tpr - fpr
        if best is None or youden > best["youden"]:
            best = {"tau": round(tau, 3), "youden": youden, "tpr": tpr, "fpr": fpr,
                    "acc": (tp + (len(ok) - fp)) / (len(slop) + len(ok))}
    return best


def main():
    slop, ok = _distances()
    if not slop or not ok:
        print("need eval/ai_samples/*/*.txt and eval/out/*/*.pro.txt", file=sys.stderr)
        return 1
    auc = _auc(slop, ok)
    best = _sweep(slop, ok)
    print(f"slop (raw AI)        n={len(slop):3d}  mean distance {statistics.fmean(slop):.3f}")
    print(f"ok   (humanizer-pro) n={len(ok):3d}  mean distance {statistics.fmean(ok):.3f}")
    print(f"separation AUC: {auc:.3f}")
    print(f"Youden-optimal threshold: {best['tau']:.3f}  "
          f"(accuracy {best['acc']*100:.0f}%, flags {best['tpr']*100:.0f}% of AI, "
          f"{best['fpr']*100:.0f}% false-flags)")
    print("accuracy at round cutoffs:")
    for tau in (0.5, 0.6, 0.75, 0.9):
        tp = sum(d > tau for d in slop)
        fp = sum(d > tau for d in ok)
        acc = (tp + (len(ok) - fp)) / (len(slop) + len(ok))
        print(f"  tau={tau:<4}  acc={acc*100:3.0f}%  (flags {tp}/{len(slop)} AI, {fp}/{len(ok)} pro)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
