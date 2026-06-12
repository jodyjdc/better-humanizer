import json
import pathlib
import re

LEX = json.loads(
    (pathlib.Path(__file__).parent.parent / "lexicons/ai_tells.json").read_text()
)


def test_lexicon_shape():
    assert len(LEX) >= 10
    ids = set()
    for e in LEX:
        assert {"id", "name", "category", "terms", "regexes"} <= e.keys()
        assert isinstance(e["terms"], list) and isinstance(e["regexes"], list)
        assert e["id"] not in ids, f"duplicate id {e['id']}"
        ids.add(e["id"])
        for rx in e["regexes"]:
            re.compile(rx)  # must compile


def test_known_terms_present():
    flat = {t.lower() for e in LEX for t in e["terms"]}
    for w in ("delve", "tapestry", "underscore", "pivotal", "nestled"):
        assert w in flat, f"missing expected term: {w}"


def test_names_unique():
    names = [e["name"] for e in LEX]
    assert len(names) == len(set(names))
