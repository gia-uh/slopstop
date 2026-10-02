from slopstop import gate

T = ("I want to argue that slop is a human failure and not a machine one. "
     "First transcribe this and then let's discuss how we improve this blog post. "
     "Keep it short. Nobody is behind the model, there is nothing it is like to be it.")
SEGS = [
    {"kind": "content", "text": "I want to argue that slop is a human failure and not a machine one."},
    {"kind": "request", "text": "First transcribe this and then let's discuss how we improve this blog post."},
    {"kind": "directive", "text": "Keep it short."},
    {"kind": "content", "text": "Nobody is behind the model, there is nothing it is like to be it."},
]


def test_good_split_passes():
    assert gate.check_split(T, SEGS).ok


def test_missing_passage_fails_coverage():
    r = gate.check_split(T, SEGS[:1] + SEGS[2:])
    assert any("missing" in f for f in r.failures)


def test_paraphrased_passage_fails_verbatim():
    segs = [dict(s) for s in SEGS]
    segs[0]["text"] = "The author argues slop comes from people rather than machines entirely."
    assert any("verbatim" in f for f in gate.check_split(T, segs).failures)


def test_unknown_kind_fails():
    segs = [dict(s) for s in SEGS]
    segs[2]["kind"] = "note"
    assert any("kind" in f for f in gate.check_split(T, segs).failures)


def test_leaked_request_fails_output():
    out = ("Slop is a human failure, not a machine one. Nobody is behind the model. " * 2 +
           "First transcribe this and then let's discuss how we improve this blog post.")
    r = gate.check_output(T, out, "rewrite", ratio=(0.1, 9), split=SEGS)
    assert any("request" in f for f in r.failures)


LONG_A = " ".join(f"The {w} problem is not using AI to solve a task." for w in "first second third fourth fifth sixth seventh eighth".split())
LONG_B = " ".join(f"People use AI for {w} things every single day now." for w in "small large odd new old good bad strange".split())


def test_deleting_one_word_in_a_long_passage_fails():
    t = LONG_A + " " + LONG_B
    segs = [{"kind": "content", "text": LONG_A}, {"kind": "content", "text": LONG_B}]
    assert gate.check_split(t, segs).ok
    segs[0] = {"kind": "content", "text": LONG_A.replace("fifth problem is not", "fifth problem is")}
    assert any("verbatim" in f for f in gate.check_split(t, segs).failures)


def test_dropping_a_short_passage_from_a_long_transcript_fails():
    long_t = " ".join(f"Sentence number {w} goes here." for w in "one two three four five six seven eight nine ten".split() * 30)
    parts = long_t.split(". ")
    segs = [{"kind": "content", "text": p + ("." if not p.endswith(".") else "")} for p in parts]
    assert gate.check_split(long_t, segs).ok
    assert not gate.check_split(long_t, segs[:100] + segs[101:]).ok


def test_reordered_long_passages_fail():
    t = LONG_A + " " + LONG_B
    segs = [{"kind": "content", "text": LONG_B}, {"kind": "content", "text": LONG_A}]
    assert not gate.check_split(t, segs).ok
