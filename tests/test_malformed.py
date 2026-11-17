"""Agent-written JSON that is valid JSON but the wrong shape exits 2 with a message."""
import json

import pytest

from slopstop import cli


@pytest.fixture
def note(tmp_path):
    t = tmp_path / "t.md"
    t.write_text("A transcript with a few words in it for the test to use.\n")
    return t


def run(capsys, argv):
    rc = cli.main(argv)
    return rc, capsys.readouterr().err


def test_unmask_with_a_list(tmp_path, note, capsys):
    c = tmp_path / "c.json"
    c.write_text(json.dumps(["[CODE-1]"]))
    assert run(capsys, ["unmask", str(note), "--code", str(c)])[0] == 2
