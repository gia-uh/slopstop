import json

import pytest

from slopstop import cli, quotes
from slopstop.cli import UsageError

SRC = "The model dropped this claim. It’s here."
OUT = "The rewrite invented a fact about Paris."


def test_verifies_against_the_right_text():
    data = {"dropped": [{"what": "a", "quote": "dropped this claim"}, {"what": "b", "quote": "not present"}],
            "invented": [{"what": "c", "quote": "a fact about Paris"}]}
    r = quotes.check(data, SRC, OUT, None)
    assert [i["what"] for i in r["verified"]["dropped"]] == ["a"]
    assert [i["what"] for i in r["verified"]["invented"]] == ["c"]
    assert r["unverified"] == 1


def test_curly_apostrophe_and_punctuation_tolerant():
    r = quotes.check({"items": [{"quote": "It's here"}]}, None, None, SRC)
    assert len(r["verified"]["items"]) == 1


def test_missing_text_is_usage_error():
    with pytest.raises(UsageError):
        quotes.check({"invented": [{"quote": "x"}]}, SRC, None, None)


def test_cli(tmp_path, capsys):
    j, s = tmp_path / "c.json", tmp_path / "s.md"
    j.write_text(json.dumps({"items": [{"quote": "dropped this claim"}]}))
    s.write_text(SRC)
    assert cli.main(["check-quotes", str(j), "--text", str(s)]) == 0
    assert json.loads(capsys.readouterr().out)["unverified"] == 0
