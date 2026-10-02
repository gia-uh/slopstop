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
    assert any("coverage" in f for f in r.failures)


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
