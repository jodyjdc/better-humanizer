import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "scripts"))
import stylo  # noqa: E402


def test_count_syllables():
    assert stylo._count_syllables("cat") == 1
    assert stylo._count_syllables("cake") == 1          # silent trailing e
    assert stylo._count_syllables("table") == 2         # -le keeps its syllable
    assert stylo._count_syllables("syllable") == 3
    assert stylo._count_syllables("running") == 2
    assert stylo._count_syllables("") == 0


def test_flesch_kincaid_grade_orders_by_complexity():
    simple = "The cat sat on the mat. The dog ran. We had fun all day."
    dense = ("The epistemological ramifications of phenomenological inquiry "
             "necessitate a reconsideration of foundational presuppositions "
             "underlying contemporary hermeneutic methodologies.")
    assert stylo.flesch_kincaid_grade(dense) > stylo.flesch_kincaid_grade(simple)


def test_flesch_kincaid_grade_empty_is_zero():
    assert stylo.flesch_kincaid_grade("") == 0.0
