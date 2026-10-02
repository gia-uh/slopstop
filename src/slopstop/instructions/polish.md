# Task: propose light edits to the author's draft

Below is the author's own draft ($words words, from $file). Fix errors and
unclear sentences. Keep the author's words wherever they work: at most
$budget_pct of the words may change. Do not raise the number of adjectives or
change what any sentence claims. The author will accept or reject each change.

Write the whole revised text, and nothing else, to $file.

TEXT:

$text

Then run: slopstop gate $orig $file --allow polish --budget $budget
