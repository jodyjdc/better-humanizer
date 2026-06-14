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


def test_new_post2023_entries_present():
    names = {e["name"] for e in LEX}
    for n in ("transitional_overuse", "era_framing", "structural_formulas",
              "hollow_affirmatives"):
        assert n in names, f"missing new entry: {n}"


def test_extended_ai_vocabulary_terms():
    flat = {t.lower() for e in LEX for t in e["terms"]}
    for w in ("shed light on", "pave the way for", "state-of-the-art",
              "game-changing", "cutting-edge", "unpack", "deep dive"):
        assert w in flat, f"missing extended vocab term: {w}"


def test_new_entry_regexes_fire():
    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "scripts"))
    import stylo
    hits = stylo.tell_hits(
        "Moreover, this matters. In today's world, first and foremost we adapt. "
        "Absolutely! It is a deep dive that will shed light on the topic.", LEX)
    assert hits["transitional_overuse"] >= 1
    assert hits["era_framing"] >= 1
    assert hits["structural_formulas"] >= 1
    assert hits["hollow_affirmatives"] >= 1
