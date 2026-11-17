# slopstop

slopstop is a linter for prose. It finds the habits that make model-written
text annoying to read, says where each one is and why it costs the reader
something, and fixes it: by itself when the fix needs no judgment, or with a
precise instruction for the agent when it does. An agent runs it in a loop over
its own draft until nothing is left.

It flags a habit because of what the habit does to a reader, whoever wrote it.
Whether a text "reads as AI" is not the question.

## Use it

```bash
uv tool install git+https://github.com/gia-uh/slopstop

slopstop check draft.md          # findings; exit 1 while an error remains
slopstop fix draft.md            # apply the mechanical fixes, keep draft.orig.md
slopstop fix --suggested draft.md
slopstop rules                   # the catalog; `slopstop rules corrective` for one rule
```

A finding looks like this:

```text
draft.md:5:9  error  corrective       "isn't just a performance trick, it's"
  why: Denying a reading nobody offered makes the reader process two claims to get one.
  fix: rewrite: Say what it is, without the denial.
  check: slopstop gate draft.orig.md draft.md --allow span --lines 5
```

Each rule fixes in one of three ways:

- `auto`: an edit that cannot change the meaning, such as deleting "I hope
  this helps!", removing bold from running prose, or turning "may potentially"
  into "may". `fix` applies these.
- `suggest`: a replacement that is right most of the time, such as an em dash
  turned into a period. `fix --suggested` applies these.
- `rewrite`: a habit that needs judgment, such as a corrective ("it isn't X,
  it's Y") or a question the next sentence answers. The finding says what to
  do, and `gate` checks that the edit stayed on the lines it names.

The catalog has rules in English and Spanish for filler openings, lines
addressed to the reader of a chat, announcements, hype, correctives, recaps,
stacked hedges, em dashes, bold, emoji, label-bullet lists, heading spray,
semicolon and colon chains, and sentence rhythm. [docs/rules.md](docs/rules.md)
lists every rule with how often it fires on human and agent writing.

## For agents

Copy [skills/slopstop/](skills/slopstop/) into `.claude/skills/` (or your
agent's skills folder) and the clause in
[skills/agent-clause.md](skills/agent-clause.md) into your CLAUDE.md or
AGENTS.md. The skill runs the loop: check, fix, rewrite the named lines, gate,
check again, until `check` exits 0.

## Configure it

A `slopstop.toml` next to the text, or `[tool.slopstop]` in `pyproject.toml`,
turns rules off, changes their level and sets thresholds:

```toml
disable = ["em-dash"]

[levels]
signposting = "warn"

[thresholds]
long-paragraph = 200
```

`<!-- slopstop: allow corrective -->` on its own line keeps one paragraph's
habit on purpose; `<!-- slopstop: off -->` and `<!-- slopstop: on -->` skip a
region. `slopstop calibrate <folder>` measures every rule on writing you
consider good and `--write slopstop.toml` sets the thresholds from it.

## Not for hiding

Nothing here helps anyone pass AI-assisted text off as unassisted, and nothing
is designed to defeat AI detectors. Removing a habit because it annoys readers
is the point; looking human is not. If you publish writing a model helped with,
say so.

## What the research found

The project started as research into why AI-assisted prose reads badly. The
reports are in [docs/research](docs/research/), starting with the
[synthesis](docs/research/2026-10-01-synthesis.md); they predate the linter and
are kept as they were.

- Commercial "humanizers" make prose worse
  ([humanizers](docs/research/2026-10-01-01-humanizers.md)).
- Readers who use LLMs daily point to model vocabulary, formulaic structure and
  vague, upbeat conclusions
  ([reader perception](docs/research/2026-10-01-03-human-perception.md)).
- Forbid lists backfire: handed a list of banned words, a weaker model used them
  39 times as often
  ([style-prompt experiment](docs/research/2026-09-13-style-prompt-arms-experiment.md)).
  slopstop checks the output instead of telling the model what not to write.
- Current models no longer write the classic openers ("Let's dive in", "I hope
  this helps"); their habits are formatting and punctuation, such as bold in
  running prose, heading spray and em dashes ([docs/rules.md](docs/rules.md)).

## AI use in this repository

The maintainer set the project's goals and scope and makes its decisions.
DeepSeek V4 Pro agents ran the literature research, and a separate agent
checked the key claims against their primary sources. Claude (Opus 5.5) wrote
the linter, its tests and this documentation, which the maintainer reviews.

## License

MIT. See [LICENSE](LICENSE).
