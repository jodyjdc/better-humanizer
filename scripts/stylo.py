#!/usr/bin/env python3
"""stylo.py - standard-library stylometric scorer for humanizer-pro.

Measures a text against the human distribution for a register (floor AND
ceiling) and flags both AI tells and over-correction (self-tells). No third
party dependencies: runs anywhere Python 3 runs.
"""
import math
import re
import statistics

WORD_RE = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?")
SENT_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
EMOJI_RE = re.compile(
    "[\U0001f000-\U0001faff\U00002600-\U000027bf\U0001f1e6-\U0001f1ff\U00002b00-\U00002bff]"
)
BOLD_RE = re.compile(r"\*\*[^*\n]+\*\*")
BULLET_RE = re.compile(r"^\s*(?:[-*+]|\d+\.)\s+\S", re.MULTILINE)
HEADING_RE = re.compile(r"^\s*#{1,6}\s+(.+)$", re.MULTILINE)
RULE_OF_THREE_RE = re.compile(r"\b[\w']+,\s+[\w']+,?\s+and\s+[\w']+\b", re.IGNORECASE)

# ~150 high-frequency English function words: the stylistic "fingerprint" layer
# that authorship studies key on. Content words are deliberately excluded.
FUNCTION_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can", "can't", "cannot", "could",
    "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down",
    "during", "each", "few", "for", "from", "further", "had", "hadn't", "has",
    "hasn't", "have", "haven't", "having", "he", "her", "here", "hers", "herself",
    "him", "himself", "his", "how", "i", "if", "in", "into", "is", "isn't", "it",
    "it's", "its", "itself", "just", "me", "more", "most", "my", "myself", "no",
    "nor", "not", "now", "of", "off", "on", "once", "only", "or", "other", "our",
    "ours", "out", "over", "own", "she", "should", "so", "some", "such", "than",
    "that", "the", "their", "theirs", "them", "then", "there", "these", "they",
    "this", "those", "through", "to", "too", "under", "until", "up", "very", "was",
    "wasn't", "we", "were", "weren't", "what", "when", "where", "which", "while",
    "who", "whom", "why", "will", "with", "won't", "would", "you", "your", "yours",
    "yourself",
}


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


# --------------------------------------------------------------------------
# Punctuation, structure, contractions
# --------------------------------------------------------------------------
def _per_100_tokens(count, text):
    n = len(tokenize(text)) or 1
    return count / n * 100


def punctuation_rates(text):
    """Punctuation counts normalized per 100 tokens.

    em_dash counts the character and the ' -- ' ASCII stand-in; both are tells
    in *excess*, but a rate of exactly zero is itself a self-tell (see score()).
    """
    em = text.count("—") + text.count(" -- ")
    raw = {
        "comma": text.count(","),
        "period": text.count("."),
        "em_dash": em,
        "en_dash": text.count("–"),
        "semicolon": text.count(";"),
        "colon": text.count(":"),
        "paren": text.count("("),
        "question": text.count("?"),
        "exclaim": text.count("!"),
    }
    return {k: _per_100_tokens(v, text) for k, v in raw.items()}


def contraction_rate(text):
    """Tokens containing an apostrophe contraction, per 100 tokens."""
    toks = tokenize(text)
    n = len(toks) or 1
    return sum(1 for t in toks if "'" in t) / n * 100


def structural(text):
    """Counts of markdown/visual AI tells: bullets, bold, emoji, title-case headings."""
    titlecase = 0
    for head in HEADING_RE.findall(text):
        words = [w for w in re.findall(r"[A-Za-z]+", head)]
        if not words:
            continue
        capped = sum(1 for w in words if w[0].isupper())
        if capped / len(words) > 0.6 and len(words) > 1:
            titlecase += 1
    return {
        "bullet": len(BULLET_RE.findall(text)),
        "bold": len(BOLD_RE.findall(text)),
        "emoji": len(EMOJI_RE.findall(text)),
        "titlecase_heading": titlecase,
    }


# --------------------------------------------------------------------------
# Tell lexicon hits + rule of three
# --------------------------------------------------------------------------
def _term_pattern(term):
    return r"(?<!\w)" + re.escape(term.lower()) + r"(?!\w)"


def tell_hits(text, lexicon):
    """Count occurrences of each lexicon entry (terms + regexes) by entry name."""
    low = text.lower()
    out = {}
    for entry in lexicon:
        count = 0
        for term in entry.get("terms", []):
            count += len(re.findall(_term_pattern(term), low))
        for rx in entry.get("regexes", []):
            count += len(re.findall(rx, text, flags=re.IGNORECASE | re.MULTILINE))
        out[entry["name"]] = count
    return out


def rule_of_three(text):
    """Heuristic count of 'X, Y, and Z' triads (the AI rule-of-three tic)."""
    return len(RULE_OF_THREE_RE.findall(text))


# --------------------------------------------------------------------------
# Function-word fingerprint
# --------------------------------------------------------------------------
def function_word_vector(text, fw=FUNCTION_WORDS):
    """Normalized frequency (per token) of each function word that appears."""
    toks = tokenize(text)
    n = len(toks) or 1
    fwset = fw if isinstance(fw, (set, frozenset)) else set(fw)
    counts = {}
    for t in toks:
        if t in fwset:
            counts[t] = counts.get(t, 0) + 1
    return {k: v / n for k, v in counts.items()}


def cosine_distance(a, b):
    """1 - cosine similarity between two sparse frequency dicts. Disjoint -> 1."""
    keys = set(a) | set(b)
    dot = sum(a.get(k, 0.0) * b.get(k, 0.0) for k in keys)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    if na == 0 or nb == 0:
        return 1.0
    return 1 - dot / (na * nb)
