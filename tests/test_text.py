from slopstop import text

DOC = """---
title: x
---

# A heading

First paragraph has five words.

```python
code = "not prose"
```

- a list item
| a | table |

Second paragraph, with it’s curly apostrophe.
Still the second paragraph.
"""


def test_paragraphs_skip_apparatus_and_keep_line_numbers():
    ps = text.paragraphs(DOC)
    assert [p.line for p in ps] == [7, 16]
    assert ps[0].words == 5
    assert ps[1].text.startswith("Second paragraph")
    assert ps[1].words == 10


def test_tokenize_normalizes_curly_apostrophe():
    assert text.tokenize("It’s not") == ["it's", "not"]


def test_strip_markdown_drops_code_and_frontmatter():
    s = text.strip_markdown(DOC)
    assert "code" not in s and "title" not in s and "A heading" in s


def test_split_sentences():
    assert text.split_sentences("One. Two? Three!") == ["One.", "Two?", "Three!"]


def test_fences_balanced():
    assert text.fences_balanced("```\nx\n```\n")
    assert not text.fences_balanced("```\nx\n")


def test_detect_lang():
    assert text.detect_lang(text.tokenize("el perro de la casa que es")) == "es"
    assert text.detect_lang(text.tokenize("the dog of the house that is")) == "en"


def test_prose_lines_numbers_match_file():
    lines = dict(text.prose_lines(DOC))
    assert lines[7] == "First paragraph has five words."
    assert 10 not in lines  # inside the code fence
