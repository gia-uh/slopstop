import re
from pathlib import Path

from slopstop import cli

SKILL = Path(__file__).parent.parent / "skills" / "slopstop" / "SKILL.md"


def test_skill_has_frontmatter():
    head = SKILL.read_text().split("---")[1]
    assert "name: slopstop" in head and "description:" in head


def test_every_command_in_the_skill_exists():
    subs = cli.build_parser()._subparsers._group_actions[0].choices
    used = set(re.findall(r"slopstop ([a-z-]+)", SKILL.read_text()))
    assert used, "the skill names no commands"
    assert used <= set(subs), used - set(subs)
