#!/usr/bin/env python3
"""stylo.py - standard-library stylometric scorer for humanizer-pro.

Measures a text against the human distribution for a register (floor AND
ceiling) and flags both AI tells and over-correction (self-tells). No third
party dependencies: runs anywhere Python 3 runs.
"""
import re
import statistics

WORD_RE = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?")
SENT_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


# --------------------------------------------------------------------------
# Segmentation
# --------------------------------------------------------------------------
def tokenize(text):
    """Lowercased word tokens; keeps internal apostrophes (can't -> can't)."""
    return WORD_RE.findall(text.lower())


def split_sentences(text):
    """Split into sentences on .!? boundaries; drop tokenless fragments."""
    parts = SENT_SPLIT_RE.split(text.strip())
    return [p.strip() for p in parts if WORD_RE.search(p)]


def sentence_lengths(text):
    """Token count per sentence."""
    return [len(tokenize(s)) for s in split_sentences(text)]


# --------------------------------------------------------------------------
# Rhythm / burstiness
# --------------------------------------------------------------------------
def burstiness(text):
    """mean, population sd, and coefficient of variation of sentence lengths.

    Flat (AI-like) rhythm -> cv near 0. Human prose alternates short and long.
    """
    lengths = sentence_lengths(text)
    if not lengths:
        return {"mean": 0.0, "sd": 0.0, "cv": 0.0}
    mean = statistics.fmean(lengths)
    sd = statistics.pstdev(lengths) if len(lengths) > 1 else 0.0
    cv = (sd / mean) if mean else 0.0
    return {"mean": mean, "sd": sd, "cv": cv}


# --------------------------------------------------------------------------
# Lexical diversity
# --------------------------------------------------------------------------
def _mtld_one_dir(tokens, threshold=0.72):
    if not tokens:
        return 0.0
    factors = 0.0
    types = set()
    count = 0
    ttr = 1.0
    for tok in tokens:
        types.add(tok)
        count += 1
        ttr = len(types) / count
        if ttr <= threshold:
            factors += 1
            types = set()
            count = 0
            ttr = 1.0
    if count > 0:
        denom = 1 - threshold
        factors += (1 - ttr) / denom if denom else 0.0
    return len(tokens) / factors if factors > 0 else float(len(tokens))


def mtld(tokens, threshold=0.72):
    """Measure of Textual Lexical Diversity: mean of forward and backward MTLD.

    Length-robust unlike raw TTR. Short texts (<50 tokens) are noisy; the value
    is still positive and usable as a relative signal.
    """
    if not tokens:
        return 0.0
    fwd = _mtld_one_dir(tokens, threshold)
    bwd = _mtld_one_dir(list(reversed(tokens)), threshold)
    return (fwd + bwd) / 2


def lexical(text):
    """Type-token ratio, MTLD, hapax ratio, mean word length."""
    tokens = tokenize(text)
    if not tokens:
        return {"ttr": 0.0, "mtld": 0.0, "hapax_ratio": 0.0, "mean_word_len": 0.0}
    types = {}
    for tok in tokens:
        types[tok] = types.get(tok, 0) + 1
    n_types = len(types)
    hapax = sum(1 for c in types.values() if c == 1)
    return {
        "ttr": n_types / len(tokens),
        "mtld": mtld(tokens),
        "hapax_ratio": hapax / n_types if n_types else 0.0,
        "mean_word_len": statistics.fmean(len(t) for t in tokens),
    }
