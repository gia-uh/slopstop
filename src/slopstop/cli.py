"""slopstop command line. Each subcommand lives in its own module; this file only wires them."""
import argparse
import json
import sys
from pathlib import Path

from slopstop import __version__


class UsageError(Exception):
    """A user error: print the message and exit 2."""


def read(path: str) -> str:
    p = Path(path)
    if not p.is_file():
        raise UsageError(f"no such file: {path}")
    return p.read_text(encoding="utf-8", errors="replace")


def cmd_profile(args) -> int:
    from slopstop import phrases, register
    folder = Path(args.folder)
    if not folder.is_dir():
        raise UsageError(f"no such folder: {args.folder}")
    plist = phrases.build(folder, [Path(m) for m in args.model]) if args.model else None
    reg = register.build(folder, args.name, args.holdout, plist)
    out = Path(args.out or f"registers/{args.name}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(reg, indent=1, ensure_ascii=False) + "\n")
    fp = reg["false_positive_rate"]
    print(f"{out}: {reg['texts']} texts, {reg['words']} words, {len(reg['phrases'])} phrases, "
          f"false-positive rate {fp if fp is not None else 'n/a'} on {reg['holdout']} held-out texts")
    return 0


def cmd_detect(args) -> int:
    from slopstop import detect, register
    raw = read(args.file)
    rep = detect.detect(raw, register.load(args.register), args.file)
    print(detect.to_json(rep) if args.json else detect.render_text(rep), end="" if not args.json else "\n")
    return 1 if any(f["severity"] == "required" for f in rep["findings"]) else 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="slopstop", description="Mechanical AI-slop detection with instructions for the agent that fixes it.")
    p.add_argument("--version", action="version", version=f"slopstop {__version__}")
    sub = p.add_subparsers(dest="command")

    s = sub.add_parser("profile", help="count a register from a folder of human-written texts")
    s.add_argument("folder")
    s.add_argument("--name", required=True)
    s.add_argument("--out")
    s.add_argument("--model", action="append", default=[], help="folder of model text on the same topics, for the phrase list")
    s.add_argument("--holdout", type=float, default=0.2)
    s.set_defaults(func=cmd_profile)

    s = sub.add_parser("detect", help="findings and fix instructions for one text")
    s.add_argument("file")
    s.add_argument("--register", required=True)
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_detect)
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        return int(e.code or 0)
    if not getattr(args, "func", None):
        parser.print_usage(sys.stderr)
        return 2
    try:
        return args.func(args)
    except UsageError as e:
        print(f"slopstop: {e}", file=sys.stderr)
        return 2
