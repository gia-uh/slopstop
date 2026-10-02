# Task: check a rewrite's fidelity

Compare the SOURCE ($source) with the REWRITE ($output). List:

1. dropped: ideas, claims, examples or opinions in the SOURCE missing from the
   REWRITE. Ignore filler, repetition and false starts.$set_aside_rule
2. invented: claims, facts, examples or opinions in the REWRITE that are not in
   the SOURCE. Translation, rephrasing and merging do not count.

For each item give a short description and a verbatim quote of 5 to 25 words:
from the SOURCE for dropped items, from the REWRITE for invented ones. Report;
never score.

Write JSON to $out:

    {"dropped": [{"what": "...", "quote": "..."}], "invented": [{"what": "...", "quote": "..."}]}
$set_aside
SOURCE:

$source_text

REWRITE:

$output_text

Then run: slopstop check-quotes $out --source $source --output $output
