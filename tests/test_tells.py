import pytest

from slopstop import tells

FILLER = " ".join(["The river runs by the stone house in the morning light."] * 20)


def one(name, raw, phrases=()):
    [m] = tells.CATALOG[name].measure(raw, list(phrases))
    return m


def per_k(count, raw):
    from slopstop import text
    return round(count * 1000 / text.word_count(raw), 2)


def test_em_dash_rate_and_lines():
    raw = FILLER + "\n\nA thought — and another — here.\n"
    m = one("em-dash", raw)
    assert m.value == per_k(2, raw) and [s.line for s in m.spans] == [3]


def test_em_dash_ignores_code():
    raw = FILLER + "\n\n```\na — b\n```\n"
    assert one("em-dash", raw).value == 0


def test_corrective_counts_curly_apostrophe():
    raw = FILLER + "\n\nIt’s not a bug. It's not a feature. That's the point.\n"
    assert one("corrective", raw).value == per_k(3, raw)


def test_mid_sentence_colon_only_lowercase_continuation():
    raw = FILLER + "\n\nOne thing: it works. A list:\n\n- item\n"
    assert one("mid-sentence-colon", raw).value == per_k(1, raw)


def test_metaphor_nouns():
    raw = FILLER + "\n\nThe substrate is a harness on a surface.\n"
    assert one("metaphor-nouns", raw).value == per_k(3, raw)


def test_headings_and_bold():
    raw = "# Title\n\n## Part\n\n" + FILLER + "\n\nSome **bold** and **more**.\n"
    assert one("headings", raw).value == per_k(2, raw)
    assert one("bold", raw).value == per_k(2, raw)


def test_sentence_length_and_spread():
    raw = "One two three. One two three four five six seven.\n"
    assert one("sentence-length", raw).value == 5.0
    assert one("sentence-spread", raw).value == 2.0


def test_repeated_openers_percent():
    raw = "The cat sat. The dog ran. A bird flew. The end came.\n"
    assert one("repeated-openers", raw).value == 25.0  # 1 of 4 sentences repeats its predecessor's opener


def test_triplets():
    raw = FILLER + "\n\nWe want speed, clarity, and joy.\n"
    assert one("triplets", raw).value == per_k(1, raw)


def test_summary_closers_and_signposts():
    raw = FILLER + "\n\nWe built it. In short, it works.\n\nLet's look at it. Here's why.\n"
    assert one("summary-closers", raw).value == per_k(1, raw)
    assert one("signposts", raw).value == per_k(2, raw)


def test_overused_phrases_uses_register_list():
    raw = FILLER + "\n\nAt its core the idea is simple. At its core it works.\n"
    assert one("overused-phrases", raw, ["at its core"]).value == per_k(2, raw)
    assert one("overused-phrases", raw, []).value == 0


@pytest.mark.parametrize("name", list(tells.CATALOG))
def test_every_tell_has_instructions_and_description(name):
    t = tells.CATALOG[name]
    assert t.high and t.describe
    assert (t.low is None) == (t.sided == "upper")
    assert t.allow in {"breaks", "punctuation", "span", "rewrite"}


def test_hard_wrapped_text_measures_like_unwrapped():
    import textwrap
    flat = ("The town was quiet that winter and nobody went out. We stayed in. "
            "Here's what we did instead of going out every night of the week. "
            "In short, we read books by the fire.\n\n") * 6
    wrapped = "\n\n".join(textwrap.fill(p, 40) for p in flat.split("\n\n") if p.strip()) + "\n"
    for name in ("sentence-length", "sentence-spread", "repeated-openers", "summary-closers", "signposts"):
        assert one(name, wrapped).value == one(name, flat).value, name


def test_summary_closer_reports_the_sentence_line():
    raw = "The town was quiet that winter\nand nobody went out.\nIn short, the town was quiet.\n"
    assert [s.line for s in one("summary-closers", raw).spans] == [3]
