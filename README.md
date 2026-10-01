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

slopstop will hold three things.

1. **A slop detector** that flags the tells readers react to and points at the
   exact span. It combines mechanical checks measured against human baselines,
   an open classifier run locally, and a model critic that quotes the passages
   it objects to instead of giving them a score. A new register, such as formal
   academic prose or a personal essay, is a folder of human-written examples,
   with no model training involved.
2. **Writing workflows** that produce good AI-assisted prose. Examples include
   dictating a draft in your own language and having a model translate and
   clean it up under a strict edit budget, or rewriting a model's draft with a
   cheaper, different model and checking that no claim was dropped or invented.
   Each workflow is an experiment until the measurements say it works.
3. **What we learn**, written down with its evidence. The research reports,
   the experiments and their numbers live here, so every rule in the tools can
   point to the measurement behind it.

The project is in its research phase. The findings so far are in
[docs/research](docs/research/), starting with the
[synthesis](docs/research/2026-10-01-synthesis.md), and the experiments are in
[experiments](experiments/). The tools come next.

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
