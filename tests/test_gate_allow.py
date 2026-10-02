from slopstop import gate

SRC = "One idea here. Another idea there, and a third.\nSecond line stays.\nThird line too.\n"


def test_every_kind_passes_unchanged():
    for kind in ("rewrite", "breaks", "punctuation", "span", "polish"):
        assert gate.check_output(SRC, SRC, kind, lines=[1]).ok, kind


def test_breaks_only():
    ok = "One idea here.\n\nAnother idea there, and a third.\nSecond line stays.\nThird line too.\n"
    assert gate.check_output(SRC, ok, "breaks").ok
    bad = ok.replace("Another", "A different")
    assert any("breaks" in f for f in gate.check_output(SRC, bad, "breaks").failures)


def test_punctuation_only():
    ok = SRC.replace(", and", ". And")
    assert gate.check_output(SRC, ok, "punctuation").ok
    bad = SRC.replace("idea there", "thought there")
    assert any("punctuation" in f for f in gate.check_output(SRC, bad, "punctuation").failures)


def test_span_only_listed_lines():
    ok = SRC.replace("Third line too.", "Third line, rewritten.")
    assert gate.check_output(SRC, ok, "span", lines=[3]).ok
    r = gate.check_output(SRC, ok, "span", lines=[1])
    assert any("line 3" in f for f in r.failures)


def test_polish_budget():
    small = SRC.replace("idea there", "idea over there")
    assert gate.check_output(SRC, small, "polish", budget=0.15).ok
    big = "Totally new words replace everything here now.\nSecond line stays.\nThird line too.\n"
    assert any("budget" in f for f in gate.check_output(SRC, big, "polish", budget=0.15).failures)
