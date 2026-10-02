# Task: rewrite a model's draft

Below is a draft of $words words from $file. Rewrite it so it reads like a
thoughtful human author wrote it: plain words, sentences of varied length,
concrete statements, a direct tone. Keep every claim, example and step of the
argument, in the same order. Add no facts, examples or anecdotes. Keep every
placeholder such as [CODE-1] exactly once and where it was.

Write only the rewritten text to $out.

TEXT:

$text

Then run: slopstop gate $file $out --allow rewrite
