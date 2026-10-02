# slopstop

slopstop is a research project and a toolkit for finding and fixing AI slop: the
patterns that make AI-assisted prose tiring to read, harder to follow, and easy
to dismiss.

The goal is better writing. A text that a model helped write should read as
clearly and as specifically as the author would write it at their best.
Hiding that a model was involved is a non-goal.

## Disclose your AI use

If you use AI to write something other people will read, say so. slopstop
exists to make AI-assisted writing better, and it will never help anyone pass
it off as unassisted. Nothing here is designed to defeat AI detectors, and we
treat a lower detector score as a symptom to investigate, never as a target.

Readers deserve to know how a text was made. The evidence also says that
disclosure and prose quality are separate problems. In 16 preregistered
experiments with 27,491 participants, readers rated the same text lower once
they were told AI had helped write it, and better prose did not remove that
penalty ([Raj, Berg and Seamans, 2026](https://doi.org/10.1037/xge0001889)).
Our answer to that finding is writing good enough to be worth reading anyway,
plus an honest account of who did what.

Every AI-assisted text that slopstop helps produce carries a disclosure that
says which steps a model performed and which were the author's. Some writing
needs no such clause, such as code comments, READMEs and software
documentation. Published work does: articles, books, papers and talks.

## What the project does

slopstop has two parts.

1. **A mechanical tool**, the `slopstop` command. It encodes the rules for
   finding AI slop and the human baselines they are measured against. It
   checks texts, and it tells an agent what to fix and how the fix will be
   checked. It calls no model.
   - `profile` counts a register from a folder of human-written texts. A new
     register, such as formal academic prose or one author's blog, is a folder
     of examples, with no model training involved.
   - `detect` reports the spans a reader would flag. Each finding carries the
     register's measured rate, an instruction, and the check that verifies the
     fix, and is marked required or optional.
   - `gate` checks a model's output against its input: duplicated blocks,
     unclosed code fences, truncation, lines addressed to the user, length, and
     whether a fix touched only what it was allowed to.
   - `mask` and `unmask` keep code blocks away from rewriting models.
   - `instruct` prints a task for the agent (split a dictation, rewrite it,
     judge a rewrite's fidelity, critique a text, polish a draft), and
     `check-quotes` verifies the quotes the agent returns.
   - `blind` builds anonymized packets for blind reads and records the
     ranking.
2. **Skills** for agents such as Claude Code, OpenCode or aegis, in
   [skills/](skills/). They classify the text, choose a rewriting model that
   applies no watermark, run the workflow, loop detect-and-fix until no
   required finding is left, and write the disclosure.

The research reports, the experiments and their numbers live here too, so every
rule can point to the measurement behind it. The findings are in
[docs/research](docs/research/), starting with the
[synthesis](docs/research/2026-10-01-synthesis.md), and the experiments are in
[experiments](experiments/).

## Use it

```bash
uv tool install git+https://github.com/gia-uh/slopstop
slopstop profile path/to/your/posts --name my-blog     # writes registers/my-blog.json
slopstop detect draft.md --register my-blog             # findings, instructions, checks
```

Version 0.1 ships one register, `apiad-blog-en`, counted on one author's 147
published posts; [its README](src/slopstop/registers/README.md) records how
often it flags that author's own held-out posts. To let an agent drive the
tool, copy `skills/slopstop/` into `.claude/skills/` and the clause in
[skills/agent-clause.md](skills/agent-clause.md) into your CLAUDE.md or
AGENTS.md.

## What we have found so far

- Commercial "humanizers" make prose worse. The ones that slip past detectors
  produce garbled text, and readers who use LLMs every day still catch their
  output almost every time
  ([humanizers](docs/research/2026-10-01-01-humanizers.md)).
- People who use LLMs daily for writing detect AI text with 92.7% accuracy and
  4% false alarms, while people who don't are at chance. The experts point to
  model vocabulary, formulaic structure and vague, upbeat conclusions
  ([reader perception](docs/research/2026-10-01-03-human-perception.md)).
- Editing a model's draft toward your own style still leaves it closer to the
  model than to you, so the order of work matters
  ([synthesis](docs/research/2026-10-01-synthesis.md)).
- Models asked to make only grammar edits still raise adjective use by 40% to
  87% and change the meaning of the text
  ([drafting workflows](docs/research/2026-10-01-08-drafting-workflows.md)).
- Forbid lists backfire. Handed a list of banned words, a weaker model used them
  39 times as often
  ([style-prompt experiment](docs/research/2026-09-13-style-prompt-arms-experiment.md)).

The reports link each claim to its primary source, and
[the verification pass](docs/research/2026-10-01-06-verification.md) records
which claims were checked and what it corrected.

## AI use in this repository

Alex Piad set the project's goals, scope and constraints and makes its
decisions. DeepSeek V4 Pro agents ran the literature research, and a separate
agent checked the key claims against their primary sources. Claude (Opus 5.5)
coordinated the research and wrote this README and the documentation, which
Alex reviews. The experiments report their own numbers.

## License

MIT. See [LICENSE](LICENSE).
