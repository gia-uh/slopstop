# Task: split a dictation transcript

$file is a voice transcript of $words words in which an author dictates a piece of
writing. Mixed into it are things the author says about the writing. Label every
passage, in order, as exactly one of:

- content: what a reader should read: claims, opinions, examples, arguments,
  stories. In "I want to argue that X", X is content. An open question the author
  asks themself ("we still need to work out the basic concepts") is content.
- directive: an instruction about the surface of the text at that point: title,
  format, structure, length, tone, or keeping the author's wording. Examples:
  "the next part is a short paragraph", "make this a list of todos", "the title
  is X", "keep it short", "keep my swearing".
- request: asking someone to do work beyond rewriting what was said: research,
  add examples or citations from elsewhere, discuss, transcribe, review.

If one sentence mixes kinds, split it. Copy every passage verbatim from the
transcript, misspellings and all. Together the passages must cover the whole
transcript in order.

Write JSON to $out:

    {"segments": [{"kind": "content|directive|request", "text": "..."}]}

Then run: slopstop gate $file --split $out
