import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "scripts"))
import stylo  # noqa: E402


# --- Task 2: segmentation + structural metrics ---

def test_tokenize_and_sentences():
    t = "Hello world. I can't stop! Really?"
    assert stylo.tokenize(t) == ["hello", "world", "i", "can't", "stop", "really"]
    assert len(stylo.split_sentences(t)) == 3


def test_sentence_lengths_and_burstiness():
    t = "One two three. Four. Five six."
    assert stylo.sentence_lengths(t) == [3, 1, 2]
    b = stylo.burstiness(t)
    assert b["mean"] == 2 and b["sd"] > 0 and b["cv"] > 0


def test_lexical_basic():
    lx = stylo.lexical("the cat sat on the mat and the cat ran")
    assert 0 < lx["ttr"] <= 1
    assert lx["hapax_ratio"] > 0
    assert lx["mean_word_len"] > 0
    assert lx["mtld"] > 0


def test_burstiness_uniform_is_low_cv():
    uniform = stylo.burstiness("aa aa aa. bb bb bb. cc cc cc.")
    assert uniform["cv"] == 0  # AI-flat rhythm -> cv 0


# --- Task 3: punctuation, structural tells, lexicon hits, function words ---

def test_punctuation_em_dash():
    p = stylo.punctuation_rates("A - b, c; d -- e.")  # placeholder, see below
    # use real em/en dashes:
    p = stylo.punctuation_rates("A — b, c; d -- e.")
    assert p["em_dash"] > 0 and p["comma"] > 0 and p["semicolon"] > 0


def test_punctuation_zero_em_dash():
    p = stylo.punctuation_rates("Plain sentence with no dashes here.")
    assert p["em_dash"] == 0


def test_structural_tells():
    s = stylo.structural("## Big Title Here\n- one\n- two\n**bold** \U0001F680")
    assert s["bullet"] == 2 and s["bold"] == 1 and s["emoji"] == 1
    assert s["titlecase_heading"] == 1


def test_tell_hits_counts():
    lex = [{"id": 7, "name": "ai_vocabulary", "category": "language",
            "terms": ["delve", "tapestry"], "regexes": []}]
    h = stylo.tell_hits("We delve into the rich tapestry of delve.", lex)
    assert h["ai_vocabulary"] == 3


def test_tell_hits_regex():
    lex = [{"id": 9, "name": "negative_parallelism", "category": "language",
            "terms": [], "regexes": [r"\bnot just\b[^.?!]{1,60}\bbut\b"]}]
    h = stylo.tell_hits("It's not just a song but a statement.", lex)
    assert h["negative_parallelism"] >= 1


def test_rule_of_three():
    assert stylo.rule_of_three("speed, quality, and adoption matter") >= 1


def test_cosine_distance_identity():
    v = stylo.function_word_vector("the the of and to the", stylo.FUNCTION_WORDS)
    assert stylo.cosine_distance(v, v) < 1e-9


def test_cosine_distance_disjoint_is_one():
    a = {"the": 1.0}
    b = {"of": 1.0}
    assert abs(stylo.cosine_distance(a, b) - 1.0) < 1e-9
