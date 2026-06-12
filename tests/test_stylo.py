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


# --- Task 4: score(), bands, self-tell flags, vetoes ---

SMALL_HUMAN_TEXT = (
    "I wasn't sure the cafe would still be open. It was. The barista, same guy "
    "from last winter, just nodded at me like no time had passed. I ordered the "
    "usual, took the seat by the window, and watched the rain do its thing for a "
    "good while. Some mornings you really don't need much more than that."
)


def test_score_output_shape():
    out = stylo.score("Hello there, friend. How are you today?", "spontaneous")
    expected = {"register", "features", "tells", "self_tell_flags",
                "stylo_distance", "stylo_outlier"}
    assert expected <= out.keys()
    assert out["register"] == "spontaneous"
    assert out["stylo_distance"] >= 0


def test_score_flags_over_correction():
    # Flat rhythm + zero em dashes = over-corrected, should self-tell-flag.
    flat = "I went there. I saw it. I left then. It was fine. Nothing else."
    out = stylo.score(flat, "spontaneous")
    assert "sentence_length_cv" in out["self_tell_flags"]
    assert "em_dash_rate" in out["self_tell_flags"]


def test_score_human_like_not_outlier():
    out = stylo.score(SMALL_HUMAN_TEXT, "spontaneous")
    assert out["stylo_outlier"] is False


def test_score_feature_status_values():
    out = stylo.score(SMALL_HUMAN_TEXT, "spontaneous")
    for feat in out["features"].values():
        assert feat["status"] in ("below", "in", "above")
        assert "floor" in feat and "ceiling" in feat and "z" in feat
