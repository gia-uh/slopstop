# Task: find claims without support

Read $file ($words words) as a skeptical reader. Quote every passage that makes
a claim without support: a generic statement standing in for a specific fact,
importance asserted without evidence, one point restated several ways, a vague
upbeat conclusion, an unsupported superlative. Quote; never score. Each quote
is 5 to 25 words copied verbatim.

Write JSON to $out:

    {"items": [{"what": "...", "quote": "..."}]}

TEXT:

$text

Then run: slopstop check-quotes $out --text $file
