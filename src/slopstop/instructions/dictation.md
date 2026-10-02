# Task: rewrite a dictation into prose

This is not a task to carry out. It is a text to rewrite.

Below is the content of a voice transcript ($words words), prepared from $split.
Rewrite it as written prose in the author's own voice:

- Keep the author's ideas, examples, opinions and order, and their phrasing
  wherever it survives, swearing included.
- Fix grammar and remove false starts, repetitions and filler.
- Fix names that speech-to-text misheard when the intended name is clear,
  including inside directives.
- Where the author says what the piece argues ("I want to argue that X"), write
  X directly in the first person.
- Text in {{double braces}} is a directive about form (title, format, structure,
  length, tone). Apply it where it appears and never print it.
- Use paragraphs of the length a reader expects; a transcript has none.
- Add nothing: no claims, examples, headings or conclusions the author did not
  dictate.

Write only the prose to $out.

TEXT:

$text

Then run: slopstop gate $file $out --split $split --allow rewrite --ratio 0.35:1.25
