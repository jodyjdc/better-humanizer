#!/usr/bin/env python3
"""Build reference-stats.json (human band set) for a register from a corpus.

Reads every corpus/<register>/*.txt, extracts stylometric features per text,
and writes per-feature bands: floor = max(0, mean - 1.0*sd), ceiling = mean +
1.5*sd. The asymmetric multipliers reflect that over-correction (dropping below
the human floor) is the failure mode we most want to catch.
"""
import argparse
import json
import pathlib
import statistics
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import stylo  # noqa: E402

FEATURE_KEYS = [
    "sentence_length_mean", "sentence_length_cv", "mtld", "ttr", "hapax_ratio",
    "em_dash_rate", "comma_rate", "contraction_rate", "rule_of_three",
    "exclaim", "bold", "emoji",
]


def aggregate(texts):
    rows = [stylo._extract_features(t) for t in texts]
    bands = {}
    for key in FEATURE_KEYS:
        vals = [r[key] for r in rows]
        mean = statistics.fmean(vals)
        sd = statistics.pstdev(vals) if len(vals) > 1 else 0.0
        bands[key] = {
            "floor": round(max(0.0, mean - 1.0 * sd), 4),
            "ceiling": round(mean + 1.5 * sd, 4),
        }
    # Register-specific AI-tell tolerance: how much of the lexicon the humans in
    # this register actually use (scientific >> spontaneous).
    tr_vals = [stylo.tell_rate(t) for t in texts]
    tr_mean = statistics.fmean(tr_vals)
    tr_sd = statistics.pstdev(tr_vals) if len(tr_vals) > 1 else 0.0
    bands["tell_rate"] = {"floor": 0.0, "ceiling": round(tr_mean + 1.5 * tr_sd, 4)}

    fw_rows = [stylo.function_word_vector(t) for t in texts]
    keys = set().union(*fw_rows) if fw_rows else set()
    fw = {
        k: round(statistics.fmean([r.get(k, 0.0) for r in fw_rows]), 6)
        for k in sorted(keys)
    }
    return bands, fw


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--register", default="spontaneous")
    ap.add_argument("--corpus-root", default=str(stylo.ROOT / "corpus"))
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)

    reg_dir = pathlib.Path(args.corpus_root) / args.register
    files = sorted(reg_dir.rglob("*.txt"))  # includes raw/ subdir of fetched texts
    out_path = (
        pathlib.Path(args.out)
        if args.out
        else stylo.ROOT / "corpus" / args.register / "reference-stats.json"
    )

    if not files:
        print(
            f"warning: no .txt files in {reg_dir}; leaving existing stats untouched",
            file=sys.stderr,
        )
        return 0

    texts = [f.read_text(encoding="utf-8") for f in files]
    bands, fw = aggregate(texts)
    stats = {
        "register": args.register,
        "calibrated": True,
        "n_texts": len(files),
        "note": f"Calibrated from {len(files)} human reference texts via build_reference.py.",
        "bands": bands,
        "function_word_vector": fw,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(stats, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {out_path} ({len(files)} texts)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
