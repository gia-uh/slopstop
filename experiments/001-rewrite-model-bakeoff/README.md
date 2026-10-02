# 001: which cheap models rewrite well

Status: complete, 2026-10-01. One run, three texts per cell: enough to rule a
model out, not to rank two close ones.

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
  words; and a fidelity check (`judge.py`) in which DeepSeek V4 Pro lists the
  claims each rewrite dropped or invented, each with a verbatim quote that is
  verified against the texts before it counts. All 230 quotes it produced
  matched. The plan also had a detector column; the calibration below is why
  it was dropped.

## Results

Columns: em dashes, contracted correctives, abstract metaphor nouns and
mid-sentence colons per 1000 words; mean and standard deviation of sentence
length in words; mean claims dropped and invented per text; dollars per 1000
output words. For reference, Alex's 147 published posts run at 3.68 em
dashes, 0.25 correctives, 0.30 metaphor nouns and 2.01 colons per 1000 words,
with sentences of 17.5 words and a standard deviation of 9.9.

### Rewriting uninstructed Claude essays

| model | n | words | em | corr | nouns | colon | slen | sd | drop | inv | cost |
|---|---|---|---|---|---|---|---|---|---|---|---|
| anthropic/claude-sonnet-5.5 | 1 |    653 |  0.00 |  3.06 |  0.00 |  4.59 | 10.53 |  6.42 |   0.0 |   0.0 |  0.0400 |
| cohere/command-a-plus | 1 |   1245 | 11.24 |  1.61 |  0.00 |  6.43 | 14.65 | 10.75 |   0.0 |   1.0 |  0.0029 |
| deepseek/deepseek-v4-flash | 3 |   1002 |  5.65 |  1.86 |  0.00 |  3.21 | 12.94 |  8.19 |   0.7 |   1.3 |  0.0018 |
| deepseek/deepseek-v4-pro | 3 |    991 |  6.24 |  0.89 |  0.00 |  3.14 | 12.43 |  7.87 |   0.5 |   0.0 |  0.0009 |
| deepseek/deepseek-v4.1-flash | 3 |    988 |  6.89 |  3.84 |  0.00 |  4.12 | 12.64 |  8.55 |   0.3 |   0.0 |  0.0013 |
| google/gemma-4-31b-it | 3 |    934 |  5.84 |  2.62 |  0.00 |  4.29 | 14.12 |  7.56 |   5.0 |   0.7 |  0.0007 |
| minimax/minimax-m3 | 3 |   1151 |  5.78 |  3.64 |  0.00 |  3.88 | 12.99 |  8.33 |   0.0 |   3.3 |  0.0016 |
| mistralai/mistral-medium-3.1 | 3 |    996 |  9.54 |  0.00 |  0.00 |  4.20 | 13.79 |  9.25 |   0.3 |   0.0 |  0.0036 |
| mistralai/mistral-small-2603 | 3 |    969 | 12.06 |  0.57 |  0.25 |  2.56 | 11.51 |  7.53 |   2.7 |   1.3 |  0.0011 |
| moonshotai/kimi-k2.6 | 3 |   1265 |  7.29 |  3.37 |  0.00 |  4.32 | 12.90 |  8.55 |   0.3 |  10.7 |  0.0031 |
| nousresearch/hermes-4-405b | 3 |   1060 |  7.43 |  2.10 |  0.00 |  3.76 | 13.70 |  8.92 |   1.0 |   2.3 |  0.0056 |
| openai/gpt-oss-120b | 3 |   1059 |  8.86 |  0.74 |  0.43 |  5.33 | 14.75 |  9.18 |   0.0 |   2.7 |  0.0003 |
| qwen/qwen3-235b-a22b-2507 | 3 |    997 | 10.38 |  0.39 |  0.31 |  3.04 |  7.76 |  4.60 |   6.0 |   4.3 |  0.0007 |
| qwen/qwen3.7-flash | 3 |   1008 |  6.25 |  0.31 |  0.00 |  4.03 | 13.68 |  8.96 |   0.0 |   0.0 |  0.0002 |
| qwen/qwen3.8-flash | 3 |   1014 |  4.30 |  0.86 |  0.00 |  3.00 | 11.85 |  6.97 |   0.3 |   0.3 |  0.0009 |
| thedrummer/cydonia-24b-v4.1 | 3 |   1031 |  9.02 |  3.38 |  0.00 |  4.04 | 15.25 |  9.53 |   1.0 |   1.3 |  0.0012 |
| thinkingmachines/inkling-small | 3 |   1064 |  8.15 |  3.11 |  0.00 |  8.00 | 13.40 |  9.98 |   1.0 |   1.7 |  0.0022 |
| xiaomi/mimo-v2.6-flash | 3 |   1082 |  8.83 |  4.18 |  0.00 |  5.67 | 14.18 |  9.88 |   0.0 |   0.0 |  0.0005 |
| z-ai/glm-5.3-flash | 2 |    694 |  5.89 |  1.36 |  0.45 |  1.81 | 12.66 |  7.62 |  10.5 |   0.0 |  0.0059 |
| **input** | 3 |    992 |  8.36 |  3.82 |  0.00 |  5.25 | 13.49 |  9.55 |   – | – | – |

### Dictation to English prose

| model | n | words | em | corr | nouns | colon | slen | sd | drop | inv | cost |
|---|---|---|---|---|---|---|---|---|---|---|---|
| cohere/command-a-plus | 2 |   1158 |  4.35 |  0.00 |  3.60 |  3.83 | 17.65 |  8.90 |   0.0 |   0.0 |  0.0021 |
| deepseek/deepseek-v4-flash | 3 |    997 |  8.86 |  2.07 |  2.71 |  4.12 | 19.94 | 12.81 |   1.7 |   0.0 |  0.0016 |
| deepseek/deepseek-v4-pro | 3 |   1052 |  8.95 |  0.00 |  3.18 |  3.26 | 19.48 | 12.92 |   2.5 |   0.0 |  0.0008 |
| deepseek/deepseek-v4.1-flash | 3 |   1080 |  6.43 |  3.46 |  2.63 |  1.93 | 20.85 | 14.46 |   0.5 |   0.0 |  0.0012 |
| google/gemma-4-31b-it | 3 |    745 |  7.34 |  2.49 |  3.13 |  4.88 | 19.56 |  9.87 |   0.5 |   0.0 |  0.0013 |
| minimax/minimax-m3 | 3 |   1048 | 12.14 |  2.94 |  2.82 |  3.56 | 20.09 | 14.76 |   0.5 |   0.0 |  0.0015 |
| mistralai/mistral-medium-3.1 | 3 |    767 | 13.59 |  0.00 |  3.50 |  5.48 | 16.28 |  8.86 |   1.0 |   0.0 |  0.0033 |
| mistralai/mistral-small-2603 | 3 |    611 | 15.18 |  0.00 |  3.88 |  6.93 | 16.74 |  8.94 |   5.7 |   1.0 |  0.0011 |
| moonshotai/kimi-k2.6 | 3 |   1029 |  5.57 |  3.65 |  2.76 |  3.08 | 20.89 | 14.48 |   1.0 |   0.0 |  0.0025 |
| nousresearch/hermes-4-405b | 2 |    762 |  0.00 |  3.66 |  0.00 |  1.53 | 16.11 |  9.38 |   2.0 |   0.0 |  0.0057 |
| openai/gpt-oss-120b | 3 |    711 |  8.68 |  0.00 |  4.26 |  6.94 | 20.83 |  9.33 |   5.3 |   2.0 |  0.0004 |
| qwen/qwen3-235b-a22b-2507 | 3 |    872 | 20.73 |  0.00 |  3.09 | 10.10 | 13.99 |  9.29 |   1.0 |   1.0 |  0.0006 |
| qwen/qwen3.7-flash | 3 |    981 |  4.42 |  0.00 |  2.76 |  5.01 | 19.47 | 12.39 |   3.5 |   0.0 |  0.0002 |
| qwen/qwen3.8-flash | 3 |    736 |  6.94 |  0.00 |  3.70 |  3.11 | 17.82 |  9.20 |   5.0 |   3.0 |  0.0009 |
| thedrummer/cydonia-24b-v4.1 | 3 |   1092 |  1.60 |  2.74 |  2.55 |  1.83 | 21.57 | 14.46 |   1.0 |   0.0 |  0.0011 |
| thinkingmachines/inkling-small | 3 |   1049 |  9.63 |  0.00 |  2.83 |  6.50 | 22.25 | 16.19 |   0.7 |   0.0 |  0.0021 |
| xiaomi/mimo-v2.6-flash | 3 |    960 |  9.17 |  3.55 |  2.60 |  5.49 | 22.29 | 15.34 |   1.0 |   0.0 |  0.0005 |
| z-ai/glm-5.3-flash | 1 |    167 |  0.00 |  5.99 |  0.00 |  0.00 | 11.93 |  8.35 |  15.0 |   0.0 |  0.0188 |
| **input** | 3 |   1158 |  1.52 |  1.82 |  0.00 |  1.22 | 24.82 | 20.56 |   – | – | – |

The judge failed on 12 of 102 pairs even after a rerun (six empty responses,
three timeouts, two dropped connections, one malformed JSON reply), ten of
them on the 1649-word Spanish transcript, so some cells average fewer texts
than `n`. On the dictation task
it also counts the author's meta-statements ("I want to title it...") as
dropped even though the prompt asked models to turn them into the post, so
dictation drop counts run high for every model alike. The metaphor-noun rate on
dictation measures the topic: the transcripts are about software agents and use
words like "harness" themselves.

### The open detectors fail on essays

The plan was to score every output with `Oxidane/tmr-ai-text-detector`, the top
open model on the RAID leaderboard (AUROC 0.997). Calibrated first on 29 of
Alex's posts, 36 model essays and three reference texts, it inverted:

| text | TMR P(AI) | ModernBERT P(AI) |
|---|---|---|
| an obvious 2023-style AI paragraph | 0.987 | 0.987 |
| Alex's published posts, mean of 29 | 0.870 | 0.505 |
| Paul Graham, "What You'll Wish You'd Known" (2005) | 0.763 | 0.490 |
| Paul Graham, "How to Make Wealth" (2004) | 0.509 | 0.257 |
| Claude Opus 5 essays, no system prompt, mean of 12 | 0.565 | 0.205 |
| Claude Sonnet via `claude -p` with a style prompt, mean of 12 | 0.508 | 0.192 |
| DeepSeek essays from an outline, mean of 12 | 0.450 | 0.142 |

The second-ranked open model, `GeorgeDrayson/modernbert-ai-detection-raid-mage`,
fails the same way. Both catch the 2023 register of AI slop and score 2026
frontier essays as more human than pre-LLM human essays. On this register they
are worse than useless, which is why the design admits a classifier only after
it separates a register's human texts from model text at a measured rate.

### Blind read: dictation

Alex read four versions of his English voice note on the term "AI slop", in
random order with the models hidden, and ranked them
`deepseek-v4-pro` > `qwen3.7-flash` > `inkling-small` > `command-a-plus`.

- **`deepseek/deepseek-v4-pro`** fixed every transcription error ("Slap" to
  slop, "cloud" to Claude, "Charge EPT" to ChatGPT, "sentence" to sentience)
  and kept every claim. Its first paragraph kept the author's framing ("I have
  this idea for a blog post I want to title...") instead of writing the post.
- **`qwen/qwen3.7-flash`** wrote the post from the first sentence, but kept all
  four transcription errors, which the prompt asked it to fix. Removing the
  framing paragraph also removed the claims inside it: slop passes on a quick
  glance, and it comes from someone who chose not to put in the effort.
- **`thinkingmachines/inkling-small`** stayed close to a raw transcript, with
  the false starts and the errors left in.
- **`cohere/command-a-plus`** printed the whole post twice and kept the
  closing instructions to the model ("First transcribe this and then let's
  discuss...") as prose. None of the table's columns caught the duplication.

Alex was first undecided between the top two because the voice note mixed
instructions for the model with the content of the post, and he was unsure
those should count against a model. They affect only deepseek's first
paragraph, while qwen's two failures have nothing to do with them, so the order holds either
way. The question itself belongs to the design: whether a dictation mode
should pull spoken instructions out into a separate brief before rewriting,
so they never reach the prose.

## Conclusion

- **Default rewrite model for essays: `qwen/qwen3.7-flash`.** On Claude essays
  it cut correctives from 3.82 to 0.31 per 1000 words with no claims dropped
  or invented. It costs $0.0002 per 1000 words. A blind read of essay
  rewrites is pending.
- **Default for dictation: `deepseek/deepseek-v4-pro`**, at $0.0009 per 1000
  words. It ranked first in the blind read, invented nothing on either task,
  wrote no correctives on dictation and fixed the transcription errors.
  `qwen/qwen3.7-flash` is second on dictation.
- **Worth a blind read on rewriting:** `mistralai/mistral-medium-3.1`, which
  removed every corrective.
- **Ruled out:** `moonshotai/kimi-k2.6` invented 10.7 claims per essay;
  `qwen/qwen3-235b-a22b-2507` cut sentences to 7.8 words and dropped six
  claims per essay; `z-ai/glm-5.3-flash` returned empty or truncated text;
  `openai/gpt-oss-120b` and `qwen/qwen3.8-flash` dropped five or more points
  per dictation.
- **A generic rewrite prompt does not fix punctuation.** Every model left em
  dashes at 4 to 15 per 1000 words, above Alex's 3.68, because the prompt
  never mentioned them. That supports the design's detect-then-fix loop over a
  single rewrite pass.
- **Dictation keeps rhythm.** The transcripts have a sentence-length standard
  deviation of 20.6. The best dictation outputs land between 12 and 16, above
  Alex's published 9.9, which no model reached when writing from an outline in
  the 2026-09-13 experiment.
- **No model reached Alex's sentence length on rewrites.** All stayed between
  11.5 and 15.3 words against his 17.5.

Each blind read is one text and one reader, so it can overturn a ranking by
the numbers but not establish one. The essay-rewrite packet is still with
Alex.

## Running it

`gen.py` needs `OPENROUTER_API_KEY` or `OPENROUTER_KEY_FILE` and writes to
`outputs/`. `judge.py` needs `JUDGE_API_KEY` for any OpenAI-compatible
endpoint (`JUDGE_URL`, `JUDGE_MODEL`). `detect.py` runs with `uv run` and
pulls CPU torch. `table.py` needs the workspace's `bin/slopcheck` and Alex's
published-post corpus, which live outside this repo until the detector work
ports them.
