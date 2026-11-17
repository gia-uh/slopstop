# Calibration sets

`make calibrate SETS=<folder>` runs `slopstop calibrate` on four sets and writes
one JSON file per set here: how many files each rule flags, hits per 1000
words, and the threshold that would flag at most 5% of the set's files. The
texts themselves are private and never committed. Measured 2026-11-17.

| set | files | what it holds |
|---|---|---|
| en-human | 146 | one author's published blog posts, 2023 to 2026, before and during LLM use |
| en-agent | 110 | design and research documents written by Claude Code agents under a style guide |
| es-human | 56 | a 2021 doctoral thesis in Spanish split into 31 chunks of about 1500 words, and 25 Spanish journalism, essay and encyclopedia pages |
| es-agent | 11 | chapters of a children's encyclopedia written by agents |

The default thresholds of long-paragraph (134 words), flat-rhythm (9
sentences), triplet-habit (more than 3 per paragraph) and slash-pairs (2 per
paragraph) are the values calibrated on en-human. heading-spray keeps 80
words: en-human has no short sections at any threshold, so it gives no signal,
and the Spanish web pages flag at every threshold in range.

Known limits:

- es-human mixes registers, and the thesis came through PDF extraction, which
  merges paragraphs: its long-paragraph numbers say more about the extraction
  than the writing.
- es-agent is small. Spanish phrase lists were checked against es-human for
  false alarms, but not mined from Spanish model output: that needs Spanish
  model essays on the same topics as human ones, as the English control set
  has.
- Levels never follow these numbers. A phrase rule that flags 22% of en-human
  stays an error; a project lowers it in its own config.
