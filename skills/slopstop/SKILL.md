---
name: slopstop
description: Use when writing, rewriting, dictating or reviewing prose that a model helped produce and that someone will read, such as blog posts, books, papers, talks, literature reviews or READMEs. Classifies the text, runs the right workflow with the slopstop CLI, loops detect-and-fix until no required finding is left, and writes the AI-use disclosure. Never use Claude to write the final sentences of published prose.
---

# slopstop

The `slopstop` CLI measures and instructs; it calls no model. You do the work,
or hand it to a model that applies no watermark, and you run the check each
instruction names. Install the CLI with
`uv tool install git+https://github.com/gia-uh/slopstop`.

## 1. Classify

Put the text in one class and tell the author your choice in one line. Ask
when the text could be published or the path gives no clear signal.

| class | examples | final sentences written by | disclosure |
|---|---|---|---|
| authored | posts, books, papers, talks | the author, or a non-watermarking model from the author's dictation or draft | yes |
| generated | literature reviews published as AI-made | a non-watermarking model, reviewed by the author | yes |
| docs | READMEs, comments, commit messages | anyone | no |

## 2. Choose the rewriting model

Every Claude model and Gemini's consumer apps watermark their text. In the
authored and generated classes they may split, critique and check, never write
a published sentence. Experiment 001 recommends `deepseek-v4-pro`, with
`qwen3.7-flash` as the fallback. Reach it through whatever is available:

- OpenRouter: `deepseek/deepseek-v4-pro` on any OpenAI-compatible client;
- OpenCode with Zen: model `deepseek-v4-pro`;
- aegis: enqueue the task on a queue whose agent runs that model.

Send the model the task text `slopstop instruct` prints, verbatim.

## 3. Run the workflow

Every rewrite and every fix is followed by the check its instruction names. A
failed check gets one retry with the failure added to the task; a second
failure stops the workflow and goes to the author.

### Dictation (authored)

1. `slopstop gate note.md --transcript` warns if the transcript is cut off.
2. `slopstop instruct split note.md`: do this task yourself (any model may
   split), then run the check it prints.
3. Show the author the passages labelled directive and request, one line each.
4. `slopstop instruct dictation note.md --split note.split.json`: send it to
   the rewriting model, save its answer as `note.draft.md`, run the check.
5. `slopstop instruct judge note.md note.draft.md --split note.split.json`: do
   it yourself, run `slopstop check-quotes` as printed, and show the author
   every verified item.
6. Detect and fix (section 4) on `note.draft.md`.

### Restyle (generated)

1. `slopstop gate draft.md`, then `slopstop mask draft.md`.
2. `slopstop instruct restyle draft.masked.md`: send it to the rewriting model,
   save `draft.masked.restyled.md`, run the check.
3. `slopstop unmask draft.masked.restyled.md --code draft.code.json -o draft.restyled.md`.
4. `slopstop instruct judge draft.md draft.restyled.md`, check the quotes, show
   the author the items.
5. Detect and fix on `draft.restyled.md`.

### Polish (authored)

1. `slopstop instruct polish post.md`: send it to the rewriting model, run the
   check.
2. Show the author `git diff --no-index --word-diff post.orig.md post.md` hunk
   by hunk and keep only the hunks they accept.

### Clean (docs)

Detect and fix, applying every required fix without asking.

## 4. Detect and fix

1. `slopstop detect post.md --register <register>`. Exit 1 means required
   findings remain. Read the notes at the top: they say which tells were
   skipped and why.
2. `cp post.md post.orig.md`, then carry out every required instruction. Fixes
   that change words in authored or generated text go to the rewriting model.
   You may make `breaks` and `punctuation` fixes yourself, because the gate
   proves no word changed.
3. Run each finding's check. If it fails, undo that fix and retry once.
4. Optional findings: in the docs class apply them; otherwise list them for
   the author in one line each and apply the ones they pick.
5. Repeat from step 1 until no required finding is left or after three rounds,
   and tell the author which.
6. `slopstop instruct critic post.md` for a last read: do it yourself, run the
   check, and show the author the verified quotes. Never fix critic items
   without the author.

If no register fits the text, build one from a folder of the author's
human-written texts: `slopstop profile <folder> --name <name>`.

## 5. Disclose

For authored and generated text, end with a disclosure written from what
actually happened in this session: which model did which step, and what the
author did. Start from the template for the class and let the author rewrite
it in their own words:

> I wrote this with AI assistance. I dictated the draft in {language};
> {model} translated it and cleaned it up, and I edited and reviewed the
> result. The ideas, structure, claims and voice are mine.

> This review was generated with AI. {model} drafted it from sources that
> {research model} gathered, and I reviewed and edited it. I am responsible
> for its claims.

Never write a disclosure for a step that did not happen, and never omit one
that did. If a watermarking model wrote any final sentence after the author's
last edit, say so and stop: the text needs another pass first.
