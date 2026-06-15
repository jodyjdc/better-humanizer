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

    # Discourse structure: one-tailed, so calibrated asymmetrically here and stored
    # under `bands` but consumed by score()'s dedicated discourse block (like
    # tell_rate), NOT by the symmetric FEATURE_KEYS loop above.
    disc_rows = [stylo.discourse(t) for t in texts]
    for key in ("transition_density", "structural_opener_rate"):
        vals = [r[key] for r in disc_rows]
        m = statistics.fmean(vals)
        sd = statistics.pstdev(vals) if len(vals) > 1 else 0.0
        bands[key] = {"floor": 0.0, "ceiling": round(m + 1.5 * sd, 4)}
    # paragraph_cv: low tail is the tell; floor only, over multi-paragraph texts.
    pcv = [r["paragraph_cv"] for r in disc_rows if r["paragraph_cv"] is not None]
    if pcv:
        m = statistics.fmean(pcv)
        sd = statistics.pstdev(pcv) if len(pcv) > 1 else 0.0
        bands["paragraph_cv"] = {"floor": round(max(0.0, m - 1.5 * sd), 4),
                                 "ceiling": None}
    else:
        bands["paragraph_cv"] = {"floor": 0.0, "ceiling": None}

    fw_rows = [stylo.function_word_vector(t) for t in texts]
    keys = set().union(*fw_rows) if fw_rows else set()
    fw = {
        k: round(statistics.fmean([r.get(k, 0.0) for r in fw_rows]), 6)
        for k in sorted(keys)
    }
    return bands, fw


def expertise_tiers(texts):
    """Split texts into novice (lowest-FK third) and expert (highest-FK third) by
    Flesch-Kincaid grade. The middle third is unused: 'practitioner' is the full
    register band-set. Returns (novice_texts, expert_texts)."""
    graded = sorted(texts, key=stylo.flesch_kincaid_grade)
    third = max(1, len(graded) // 3)
    return graded[:third], graded[-third:]


def _blend(voice_bands, voice_fw, reg_bands, reg_fw, w):
    """Per-feature weighted blend of two band-sets: w*voice + (1-w)*register.
    None edges (e.g. paragraph_cv ceiling) are preserved, not averaged."""
    bands = {}
    for key in set(voice_bands) | set(reg_bands):
        v, r = voice_bands.get(key), reg_bands.get(key)
        if v is None:
            bands[key] = r
        elif r is None:
            bands[key] = v
        else:
            out = {}
            for edge in ("floor", "ceiling"):
                a, b = v.get(edge), r.get(edge)
                out[edge] = a if (a is None or b is None) else round(w * a + (1 - w) * b, 4)
            bands[key] = out
    keys = set(voice_fw) | set(reg_fw)
    fw = {k: round(w * voice_fw.get(k, 0.0) + (1 - w) * reg_fw.get(k, 0.0), 6)
          for k in sorted(keys)}
    return bands, fw


def _build_voice(args):
    """Calibrate a personal voice band-set, blending with a register fallback when
    the sample is too small to stand on its own."""
    vdir = pathlib.Path(args.voice_sample)
    files = sorted(vdir.glob("*.txt"))
    if not files:
        print(f"no .txt in {vdir}", file=sys.stderr)
        return 1
    texts = [f.read_text(encoding="utf-8") for f in files]
    words = sum(len(stylo.tokenize(t)) for t in texts)
    v_bands, v_fw = aggregate(texts)
    w = min(1.0, words / 1500)
    if w < 1.0:
        reg = stylo.load_reference(args.register)
        v_bands, v_fw = _blend(v_bands, v_fw, reg["bands"],
                               reg.get("function_word_vector", {}), w)
        print(f"warning: voice sample is {words} words (< 1500); blended with "
              f"'{args.register}' at weight {round(w, 3)} (bands will be approximate)",
              file=sys.stderr)
    out_root = pathlib.Path(args.out_root) if args.out_root else (stylo.ROOT / "voices")
    out_path = out_root / args.label / "reference-stats.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    stats = {
        "register": f"voice:{args.label}",
        "calibrated": True,
        "n_texts": len(files),
        "voice_blend_weight": round(w, 4),
        "note": f"Voice '{args.label}' from {len(files)} texts ({words} words).",
        "bands": v_bands,
        "function_word_vector": v_fw,
    }
    out_path.write_text(json.dumps(stats, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {out_path} (weight {round(w, 3)})")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--register", default="spontaneous")
    ap.add_argument("--corpus-root", default=str(stylo.ROOT / "corpus"))
    ap.add_argument("--out", default=None)
    ap.add_argument("--voice-sample", default=None, help="dir of *.txt to calibrate a voice")
    ap.add_argument("--label", default="me", help="voice label (output subdir)")
    ap.add_argument("--out-root", default=None, help="root dir for voice output (test hook)")
    args = ap.parse_args(argv)

    if args.voice_sample:
        return _build_voice(args)

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

    # Expertise tiers: novice (low-FK) and expert (high-FK) band-sets. practitioner
    # is the full reference-stats.json above (so the default flag stays backward-compatible).
    novice, expert = expertise_tiers(texts)
    for level, tier_texts in (("novice", novice), ("expert", expert)):
        t_bands, t_fw = aggregate(tier_texts)
        fks = sorted(stylo.flesch_kincaid_grade(t) for t in tier_texts)
        tier_stats = {
            "register": args.register,
            "expertise": level,
            "calibrated": True,
            "n_texts": len(tier_texts),
            "fk_grade_range": [round(fks[0], 2), round(fks[-1], 2)],
            "note": f"{level} tier (FK-grade tercile) of {args.register}, {len(tier_texts)} texts.",
            "bands": t_bands,
            "function_word_vector": t_fw,
        }
        tier_path = out_path.parent / f"expertise-{level}.json"
        tier_path.write_text(json.dumps(tier_stats, indent=2, ensure_ascii=False) + "\n")
        print(f"wrote {tier_path} ({len(tier_texts)} texts, FK {tier_stats['fk_grade_range']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
