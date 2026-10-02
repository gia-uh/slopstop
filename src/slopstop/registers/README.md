# Shipped registers

A register holds counts measured on a folder of human-written texts, never the
texts. `slopstop profile` writes one; `make register` regenerates the file
below from the private corpus.

## apiad-blog-en

| field | value |
|---|---|
| source | the author's 147 published Substack posts, 2023 to 2026, converted from HTML |
| training texts | 118 (229,234 words) |
| held-out texts | 29, chosen by a hash of the file name |
| phrase list | 200 phrases, from uninstructed essays by Claude, DeepSeek, Gemini and Mistral on 12 shared topics, each phrase seen under at least 3 topics |
| false-positive rate | 0.207: 6 of 29 held-out posts get at least one required finding |

How often each tell gives a required finding (measured 2026-10-02; the three
model sets were not used to build the phrase list):

| texts | n | with a required finding | by tell |
|---|---|---|---|
| author, held out | 29 | 6 | long-paragraph 3, corrective 2, sentence-length 1 |
| Claude Opus, no style prompt | 12 | 12 | headings 12, overused-phrases 12, sentence-spread 1 |
| Claude Sonnet, no style prompt | 12 | 12 | headings 11, overused-phrases 12, long-paragraph 1, sentence-spread 1 |
| Qwen, from an outline | 12 | 12 | headings 12, long-paragraph 9, sentence-spread 9, overused-phrases 6, metaphor-nouns 6, sentence-length 6, repeated-openers 1 |

Known limits of this register:

- **bold** is not measurable. The HTML conversion dropped all bold, so every
  post scores 0 and `detect` skips the tell with a note.
- **headings** counts each post's `# Title`. A text with no title heading,
  such as a fresh dictation, falls below the band. Below the band is optional
  for every tell except sentence length and spread, so this only produces an
  optional finding.
- **long-paragraph** is judged per paragraph against the 99th percentile, and a
  post has about 45 paragraphs, so a human post often has one paragraph above
  the line. It accounts for half of the false positives.
- The model essays share their topics, and the author's posts cover some of
  them, so the phrase list may still hold topic words that the 3-topic rule
  did not catch.
