#!/usr/bin/env python3
"""Fetch a genuinely-human, pre-2022, license-clean reference corpus for the
spontaneous register, using the HuggingFace datasets rows API (JSON over HTTP,
no third-party deps).

Sources are standard public research datasets of human opinion writing produced
well before ChatGPT (2022), so they are human with very high confidence:
  - IMDB movie reviews (Maas et al. 2011)
  - Yelp reviews (Zhang et al. 2015)

Raw texts are written to corpus/<register>/raw/ (gitignored: licensed / not ours
to redistribute). Only the derived statistics (reference-stats.json) and this
reproducible script are committed. Run, then `build_reference.py`.
"""
import argparse
import html
import json
import os
import pathlib
import re
import ssl
import sys
import urllib.parse
import urllib.request

ROWS_API = "https://datasets-server.huggingface.co/rows"


def _ssl_context():
    """Some Python builds (e.g. python.org framework) ship without a usable CA
    bundle. Fall back to the system/OpenSSL bundle so HTTPS verification works."""
    for cafile in (os.environ.get("SSL_CERT_FILE"), "/etc/ssl/cert.pem",
                   "/usr/local/etc/openssl@3/cert.pem", "/opt/homebrew/etc/openssl@3/cert.pem"):
        if cafile and os.path.exists(cafile):
            try:
                return ssl.create_default_context(cafile=cafile)
            except Exception:  # noqa: BLE001
                continue
    return ssl.create_default_context()


CTX = _ssl_context()
TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")
SENT_RE = re.compile(r"[.!?]")

# Human, pre-2022, license-clean sources per register. Only derived statistics
# are committed; raw texts (corpus/<register>/raw/) are gitignored.
SOURCES = {
    # Opinion prose: IMDB (2011) + Yelp (2015) reviews.
    "spontaneous": [
        {"name": "imdb", "dataset": "stanfordnlp/imdb", "config": "plain_text",
         "split": "train", "field": "text", "offsets": [0, 12500], "target": 60},
        {"name": "yelp", "dataset": "Yelp/yelp_review_full", "config": "yelp_review_full",
         "split": "train", "field": "text", "offsets": [0, 60000], "target": 60},
    ],
    # Scientific prose: PubMed + arXiv paper abstracts (Cohan et al. 2018, pre-LLM).
    # The 'abstract' field is dense, self-contained scientific writing.
    "scientific": [
        {"name": "pubmed", "dataset": "ccdv/pubmed-summarization", "config": "document",
         "split": "train", "field": "abstract", "offsets": [0, 5000], "target": 60},
        {"name": "arxiv", "dataset": "ccdv/arxiv-summarization", "config": "document",
         "split": "train", "field": "abstract", "offsets": [0, 5000], "target": 60},
    ],
}


def fetch_rows(dataset, config, split, offset, length):
    qs = urllib.parse.urlencode(
        {"dataset": dataset, "config": config, "split": split,
         "offset": offset, "length": length}
    )
    req = urllib.request.Request(
        f"{ROWS_API}?{qs}", headers={"User-Agent": "humanizer-pro-corpus/0.1"}
    )
    with urllib.request.urlopen(req, timeout=40, context=CTX) as resp:
        return json.loads(resp.read()).get("rows", [])


def clean(text):
    text = html.unescape(text)
    text = TAG_RE.sub(" ", text)
    text = text.replace("\\n", " ").replace("\\'", "'")
    text = WS_RE.sub(" ", text)
    # Some research dumps are pre-tokenized ("iran , shiraz . "); re-attach
    # punctuation so sentence/word stats are not skewed by the spacing.
    text = re.sub(r"\s+([.,;:!?])", r"\1", text)
    return text.strip()


def usable(text, min_chars, max_chars, min_sents):
    return (min_chars <= len(text) <= max_chars
            and len(SENT_RE.findall(text)) >= min_sents)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--register", default="spontaneous")
    ap.add_argument("--min-chars", type=int, default=300)
    ap.add_argument("--max-chars", type=int, default=2400)
    ap.add_argument("--min-sents", type=int, default=4)
    args = ap.parse_args(argv)

    root = pathlib.Path(__file__).resolve().parent.parent
    raw_dir = root / "corpus" / args.register / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    srcs = SOURCES.get(args.register)
    if not srcs:
        print(f"no sources defined for register '{args.register}' "
              f"(have: {', '.join(SOURCES)})", file=sys.stderr)
        return 1

    seen = set()
    total = 0
    for src in srcs:
        kept = 0
        try:
            for off in src["offsets"]:
                if kept >= src["target"]:
                    break
                rows = fetch_rows(src["dataset"], src["config"], src["split"], off, 100)
                for r in rows:
                    if kept >= src["target"]:
                        break
                    raw = r.get("row", {}).get(src["field"], "")
                    if not isinstance(raw, str):
                        continue
                    text = clean(raw)
                    key = text[:120]
                    if key in seen or not usable(text, args.min_chars, args.max_chars, args.min_sents):
                        continue
                    seen.add(key)
                    (raw_dir / f"{src['name']}-{kept:03d}.txt").write_text(
                        text + "\n", encoding="utf-8"
                    )
                    kept += 1
            print(f"{src['name']:6} kept {kept}")
            total += kept
        except Exception as exc:  # noqa: BLE001 - one bad source must not abort the rest
            print(f"{src['name']:6} FAILED: {exc}", file=sys.stderr)

    print(f"total {total} texts -> {raw_dir}")
    return 0 if total else 1


if __name__ == "__main__":
    raise SystemExit(main())
