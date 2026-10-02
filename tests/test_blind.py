import json

import pytest

from slopstop import blind, cli
from slopstop.cli import UsageError


@pytest.fixture
def versions(tmp_path):
    a = tmp_path / "a.md"
    a.write_text("Version A ends inside code:\n\n```python\nx = 1\n")
    b = tmp_path / "b.md"
    b.write_text("Version B is plain.\n")
    c = tmp_path / "c.md"
    c.write_text("Version C is plain too.\n")
    return [str(a), str(b), str(c)]


def test_unclosed_fence_does_not_swallow_next_version(versions):
    md, key = blind.packet(versions, seed=1, title="t")
    assert md.count("## V") == 3
    fence_lines = [ln for ln in md.splitlines() if ln.strip().startswith("```")]
    assert len(fence_lines) % 2 == 0
    assert sorted(key["versions"].values()) == sorted(versions)


def test_same_seed_same_order(versions):
    assert blind.packet(versions, 7, "t") == blind.packet(versions, 7, "t")


def test_record_ranking_with_ties(versions):
    _, key = blind.packet(versions, 1, "t")
    r = blind.record(key, "V3>V1=V2")
    assert r["ranking"][0] == [key["versions"]["V3"]]
    assert sorted(r["ranking"][1]) == sorted([key["versions"]["V1"], key["versions"]["V2"]])
    with pytest.raises(UsageError):
        blind.record(key, "V1>V1")
    with pytest.raises(UsageError):
        blind.record(key, "V9>V1")


def test_cli(versions, tmp_path):
    p, k = tmp_path / "p.md", tmp_path / "k.json"
    assert cli.main(["blind", "make", *versions, "--seed", "3", "--out", str(p), "--key", str(k)]) == 0
    assert cli.main(["blind", "record", str(k), "V1>V2>V3"]) == 0
    assert len(json.loads(k.read_text())["ranking"]) == 3
