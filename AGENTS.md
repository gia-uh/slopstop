# slopstop

slopstop is a linter for prose: it finds the habits that make model-written
text annoying to read, explains each one, and fixes it, by itself when the fix
is mechanical and with a precise instruction for an agent when it needs
judgment. An agent runs it in a loop over a draft until no error is left. It
serves writers and agents who produce English and Spanish prose that people
read.

This file changes when the goals change. Nothing in it should be made false by
a commit that adds code, a rule or a measurement.

## The rules the project serves

- **Annoyance, not provenance.** A rule exists because a habit costs the reader
  something: time, the point, or trust. It flags the habit whoever wrote it.
  No rule exists only to separate model text from human text.
- **Never hiding.** No tool here optimizes against an AI detector, removes
  provenance, or helps pass AI-assisted text off as unassisted.
- **As mechanical as possible.** The tool calls no model. Every fix that can
  be an exact edit is one (`auto`); the rest carry an instruction and a `gate`
  check that bounds the edit to its lines.
- **Every rule carries its examples and its measurement.** A rule ships with
  examples that must fire, must stay quiet and, for a replacement, must fix to
  an exact text; `make test` runs them. Its fire rate on human and agent sets
  is recorded in `docs/rules.md`. Levels never follow fire rates: a project
  lowers a level in its own config.

## What done means

For a rule: its examples pass, it was broken on purpose once to confirm a test
fails, and `make calibrate` has recorded its fire rates.

For a tool: it runs on real texts the way an agent runs it, and a sweep over
real files shows its fixes leave code, quotes and links intact.

## Where everything lives

| tier | holds |
|---|---|
| `AGENTS.md` | goals, rules, what done means |
| `DESIGN.md` | architecture and the reason for each boundary (once the design is approved) |
| `docs/research/` | the research behind the project, frozen; it predates the linter |
| `docs/rules.md`, `docs/calibration/` | the generated rules table and the counts it is built from |
| `docs/superpowers/specs/`, `docs/superpowers/plans/` | design specs and implementation plans |
| `experiments/NNN-<slug>/` | one experiment per folder: code, method, results |
| `src/slopstop/` | the CLI: `check.py`, `fix.py`, `calibrate.py`, `gate.py`, `mask.py` |
| `src/slopstop/rules/` | the catalog: phrase rules per language, marks, document shape |
| `skills/` | agent skills and the agent-instructions clause, for users to copy |
| `tests/` | pytest, one file per module, run by `make test` |
| `know-how/` | one procedure per job, each opening with a `when:` line |
| `Makefile` | every mechanical check |

## Working here

- `make test` is the gate. Run it verbatim and read its exit code directly.
- `grep -m1 -H '^when:' know-how/*.md` prints the know-how menu.
- Changes land through issue, branch, PR and green CI. Trivial edits go
  straight to `main`.
