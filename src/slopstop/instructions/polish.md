# Task: propose light edits to the author's draft

$file is the author's own draft ($words words). Propose edits that fix errors
and unclear sentences. Keep the author's words wherever they work: at most
$budget_pct of the words may change. Do not raise the number of adjectives or
change what any sentence claims. The author will accept or reject each change.

First keep the original: cp $file $orig
Then edit $file in place.

Then run: slopstop gate $orig $file --allow polish --budget $budget
