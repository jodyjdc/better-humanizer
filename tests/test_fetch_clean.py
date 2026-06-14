import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "scripts"))
import fetch_corpus as fc  # noqa: E402


def test_clean_strips_markdown_link_keeps_anchor():
    assert "Java Web Start" in fc.clean("look to [Java Web Start](https://x.com/a/b).")
    assert "http" not in fc.clean("see [docs](https://example.com/page).")


def test_clean_removes_blockquote_markers_and_rules():
    out = fc.clean("> quoted line\n\n---\n\nreal text here.")
    assert ">" not in out
    assert "---" not in out
    assert "real text here" in out


def test_clean_strips_inline_code_and_bare_urls():
    out = fc.clean("use the `printf` call; ref https://example.com/x now.")
    assert "printf" in out          # keep the word, drop the backticks
    assert "`" not in out
    assert "http" not in out


def test_clean_preserves_plain_prose():
    s = "A normal sentence, with a comma — and an em dash. Nothing to strip!"
    assert fc.clean(s) == s
