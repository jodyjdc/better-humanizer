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
