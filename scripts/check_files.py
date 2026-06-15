#!/usr/bin/env python3
"""humanize-check — score files against the human band, flag AI-sounding ones.

The engine behind the `humanize-check` GitHub Action: given globs of text/markdown
files, it scores each with the same deterministic stylometric scorer as stylo.py and
flags any whose distance to the human band exceeds a threshold (or that is a hard
outlier). Zero dependencies; the corpora and lexicon ship in this repo, so the check
is fully self-contained.

Files are globbed relative to the current directory (the consumer repo's checkout);
the scorer + corpora are loaded from this repo (next to this script).

  python3 scripts/check_files.py --files "docs/**/*.md" --register spontaneous --max-distance 0.6
"""
import argparse
import glob
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import stylo  # noqa: E402


def _expand(globs):
    out = []
    for g in globs:
        # comma-separated globs (NOT whitespace — paths may contain spaces)
        for part in g.split(","):
            part = part.strip()
            if part:
                out.extend(sorted(glob.glob(part, recursive=True)))
    # de-dup, keep files only
    seen, files = set(), []
    for f in out:
        if f not in seen and os.path.isfile(f):
            seen.add(f)
            files.append(f)
    return files


def check(files, register, max_distance, expertise=None, persona=None):
    ref, reg, allow, deny = stylo._resolve_target(register, expertise, None, None, persona)
    rows = []
    for f in files:
        text = pathlib.Path(f).read_text(encoding="utf-8")
        s = stylo.score(text, reg, ref=ref, allow=allow, deny=deny)
        dist = s["stylo_distance"]
        flagged = s["stylo_outlier"] or dist > max_distance
        rows.append({
            "file": f, "distance": dist, "outlier": s["stylo_outlier"],
            "self_tells": len(s["self_tell_flags"]), "flagged": flagged,
        })
    return rows


def _summary_md(rows, register, max_distance):
    n_flag = sum(r["flagged"] for r in rows)
    lines = [
        "## humanize-check",
        "",
        f"Register `{register}` · distance ceiling `{max_distance}` · "
        f"**{n_flag}/{len(rows)} flagged**",
        "",
        "| file | distance | outlier | self-tells | verdict |",
        "|---|--:|:--:|--:|:--:|",
    ]
    for r in sorted(rows, key=lambda x: -x["distance"]):
        verdict = "⚠️ flag" if r["flagged"] else "✅ ok"
        lines.append(
            f"| `{r['file']}` | {r['distance']:.3f} | "
            f"{'yes' if r['outlier'] else 'no'} | {r['self_tells']} | {verdict} |"
        )
    lines += [
        "",
        "Distance = stylometric distance to the real human distribution for the register "
        "(lower = more human). Not a detector score; this measures human-band fit. "
        "See [better-humanizer](https://github.com/jodyjdc/better-humanizer).",
    ]
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--files", nargs="+", default=["**/*.md"],
                    help="globs (space/comma separated), relative to cwd")
    ap.add_argument("--register", default="spontaneous")
    ap.add_argument("--max-distance", type=float, default=0.6,
                    help="flag files above this distance (calibrated default 0.6)")
    ap.add_argument("--expertise", default=None, help="novice | practitioner | expert")
    ap.add_argument("--persona", default=None)
    ap.add_argument("--fail-on-flag", default="true",
                    help="exit 1 if any file is flagged (true/false)")
    args = ap.parse_args(argv)

    # empty strings come from optional GitHub Action inputs — treat as unset
    def _opt(v):
        return v if v not in (None, "", "none") else None
    expertise, persona = _opt(args.expertise), _opt(args.persona)
    if expertise and expertise not in ("novice", "practitioner", "expert"):
        print(f"humanize-check: invalid --expertise {expertise!r}", file=sys.stderr)
        return 2

    files = _expand(args.files)
    if not files:
        print(f"humanize-check: no files matched {args.files}", file=sys.stderr)
        return 0  # nothing to check is not a failure

    rows = check(files, args.register, args.max_distance, expertise, persona)
    n_flag = sum(r["flagged"] for r in rows)

    for r in sorted(rows, key=lambda x: -x["distance"]):
        mark = "FLAG" if r["flagged"] else "ok  "
        print(f"[{mark}] {r['distance']:.3f}  {r['file']}")
    print(f"\nhumanize-check: {n_flag}/{len(rows)} flagged "
          f"(register={args.register}, max-distance={args.max_distance})")

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as fh:
            fh.write(_summary_md(rows, args.register, args.max_distance) + "\n")

    out_path = os.environ.get("GITHUB_OUTPUT")
    if out_path:
        with open(out_path, "a", encoding="utf-8") as fh:
            fh.write(f"flagged={n_flag}\n")
            fh.write(f"checked={len(rows)}\n")

    if args.fail_on_flag.lower() == "true" and n_flag:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
