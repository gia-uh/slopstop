"""slopstop command line. Each subcommand lives in its own module; this file only wires them."""
import argparse
import sys

from slopstop import __version__


class UsageError(Exception):
    """A user error: print the message and exit 2."""


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="slopstop", description="Mechanical AI-slop detection with instructions for the agent that fixes it.")
    p.add_argument("--version", action="version", version=f"slopstop {__version__}")
    p.add_subparsers(dest="command")
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
