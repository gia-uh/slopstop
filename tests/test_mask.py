import json

import pytest

from slopstop import cli, mask
from slopstop.cli import UsageError

DOC = "Intro.\n\n```python\nx = 1\n```\n\nMiddle.\n\n~~~\ny\n~~~\n"


def test_round_trip_is_byte_identical():
    m, blocks = mask.mask(DOC)
    assert "[CODE-1]" in m and "[CODE-2]" in m and "x = 1" not in m
    assert mask.unmask(m, blocks) == DOC


def test_missing_placeholder_raises():
    m, blocks = mask.mask(DOC)
    with pytest.raises(UsageError, match="CODE-2"):
        mask.unmask(m.replace("[CODE-2]", ""), blocks)


def test_cli_mask_unmask(tmp_path, capsys):
    f = tmp_path / "post.md"
    f.write_text(DOC)
    assert cli.main(["mask", str(f)]) == 0
    masked, code = tmp_path / "post.masked.md", tmp_path / "post.code.json"
    assert masked.exists() and json.loads(code.read_text())
    out = tmp_path / "final.md"
    assert cli.main(["unmask", str(masked), "--code", str(code), "-o", str(out)]) == 0
    assert out.read_text() == DOC
