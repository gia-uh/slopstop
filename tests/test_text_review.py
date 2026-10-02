"""Final-review fixes: fences, apparatus line by line, wrapped sentences."""
from slopstop import text

TILDE_WITH_BACKTICKS = "Intro.\n\n~~~\n```\nnot a fence\n```\n~~~\n\nAfter the block.\n"
FOUR = "Intro.\n\n````md\n```python\nx = 1\n```\n````\n\nAfter the block.\n"


def test_tilde_fence_with_backticks_inside_is_balanced():
    assert text.fences_balanced(TILDE_WITH_BACKTICKS)
    assert [p.text for p in text.paragraphs(TILDE_WITH_BACKTICKS)] == ["Intro.", "After the block."]


def test_four_backtick_fence_is_balanced():
    assert text.fences_balanced(FOUR)
    assert [p.text for p in text.paragraphs(FOUR)] == ["Intro.", "After the block."]


def test_open_fence_reports_its_closing_marker():
    assert text.open_fence("x\n\n~~~\ncode\n") == "~~~"
    assert text.open_fence("x\n\n````\ncode\n") == "````"
    assert text.open_fence("x\n") is None


def test_paragraph_directly_under_heading_is_prose():
    ps = text.paragraphs("# Title\nThis paragraph sits under the heading.\n")
    assert [(p.line, p.text) for p in ps] == [(2, "This paragraph sits under the heading.")]


def test_list_after_intro_line_is_not_prose():
    ps = text.paragraphs("Intro line:\n- item one\n- item two\n")
    assert [p.text for p in ps] == ["Intro line:"]


def test_sentences_ignore_hard_wraps_and_map_lines():
    flat = "One two three four five six. Seven eight nine ten eleven twelve.\n"
    wrapped = "One two three four\nfive six. Seven eight\nnine ten eleven twelve.\n"
    assert [s.text for s in text.sentences(flat)] == [s.text for s in text.sentences(wrapped)]
    assert [s.line for s in text.sentences(wrapped)] == [1, 2]
