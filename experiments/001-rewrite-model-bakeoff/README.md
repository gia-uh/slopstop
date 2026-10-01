# 001: which cheap models rewrite well

Status: running. Results and conclusion land in this file when the fidelity
check and the detector pass finish.

## Question

Which inexpensive, non-watermarking models turn two kinds of input into good
English prose? The inputs are a model's draft, which needs its AI tells
removed, and an author's voice transcript, which needs translating and
cleaning up. Good means few tells, sentence rhythm close to human writing, no
dropped or invented claims, and a low cost per thousand words.

## Method

- **Inputs, six texts.** Three essays written by Claude Opus 5 with no system
  prompt, taken from the September control corpus (AI winter, automating your
  writing, binary search). Three of Alex's voice notes: one in English, the
  idea for a post on whether AI slop exists, and two in Spanish, on a semantic
  layer for rift and on the sindri project. The voice notes are private and
  are not in this repository.
- **Models, twenty, through OpenRouter.** DeepSeek V4 Flash, V4 Pro and V4.1
  Flash; Qwen 3.7 Flash, 3.8 Flash and Qwen3-235B-A22B-2507; Mistral Small
  2603, Medium 3.1 and Large 2512; Gemma 4 31B; Kimi K2.6; GLM 5.3 Flash;
  MiniMax M3; gpt-oss-120b; MiMo v2.6 Flash; Command A Plus; Inkling Small;
  Hermes 4 405B; Cydonia 24B; and Claude Sonnet 5.5 as a reference only,
  because its output is watermarked.
- **One zero-shot prompt per task, temperature 0.7, reasoning disabled.** The
  prompts are in `gen.py`. They ask for plain, varied, concrete prose, forbid
  adding claims, and name no banned words, because forbid lists backfired in
  the September experiments.
- **Measurements.** Em dashes, mid-sentence colons, contracted correctives and
  abstract metaphor nouns per 1000 words; mean and standard deviation of
  sentence length, against Alex's 147 published posts; cost per 1000 output
  words; a fidelity check by DeepSeek V4 Pro agents that lists dropped and
  invented claims with verbatim quotes, which are verified against the texts
  before they count (`judge-agent.txt`); and the probability of AI authorship
  per paragraph from `Oxidane/tmr-ai-text-detector`, the top open model on the
  RAID leaderboard, calibrated first on Alex's posts against model essays
  (`detect.py`).

## Running it

`gen.py` needs `OPENROUTER_API_KEY` or `OPENROUTER_KEY_FILE` and writes to
`outputs/`. `table.py` needs the workspace's `bin/slopcheck` and Alex's
published-post corpus, which live outside this repo until the detector work
ports them.
