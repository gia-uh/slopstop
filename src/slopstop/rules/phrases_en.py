"""English phrase rules: literal habits that cost the reader time, matched per line."""
import re

from slopstop.rules import SENT_START, Rule, add, phrases, sentence_from

add(Rule(
    "opener-filler", "en", "error", "auto",
    why="A warm-up sentence delays the first real one.",
    todo="Delete the sentence.",
    pattern=sentence_from(phrases(
        "great question", "good question", "excellent question", "let's dive in", "let's dive into",
        "let's dig in", "let's break it down", "let's break this down", "in today's fast-paced world",
        "in today's digital age", "in an era where", "in the ever-evolving", "buckle up")),
    replace="",
    fires=("Great question! Caching is hard.", "Buckle up. This one is long."),
    quiet=("The question was great.", "We broke the model down into parts."),
    fixes=(("Great question! Caching is hard.", "Caching is hard."),),
))

add(Rule(
    "user-address", "en", "error", "auto",
    why="A line meant for whoever asked for the text, left inside it.",
    todo="Delete the sentence.",
    pattern=sentence_from(phrases(
        "i hope this helps", "hope this helps", "let me know if", "feel free to", "happy to help",
        "i'd be happy to", "if you'd like, i can", "would you like me to", "sure!", "certainly!",
        "absolutely!", "here's the rewritten", "here is the rewritten", "here's a revised",
        "here is a revised")),
    replace="",
    fires=("The cache is shared. I hope this helps!", "Let me know if you want more examples."),
    quiet=("Hope is not a plan.", "We let the model know if a test fails."),
    fixes=(("The cache is shared. I hope this helps!", "The cache is shared."),),
))

add(Rule(
    "meta-commentary", "en", "error", "auto",
    why="Announcing that a point matters delays the point.",
    todo="Delete the announcement and start with the point.",
    pattern=re.compile(r"(?:^|(?<=[.!?]\s)|(?<=^[-*+]\s))(?:" + phrases(
        "it's worth noting that", "it is worth noting that", "it's important to note that",
        "it is important to note that", "it should be noted that", "it's worth mentioning that",
        "notably,", "interestingly,", "importantly,") + r")\s+(\w)", re.I),
    replace=lambda m, ln: m.group(1).upper(),
    fires=("It's worth noting that the cache is shared.", "Interestingly, nobody noticed."),
    quiet=("The note is worth keeping.", "It is worth the cost."),
    fixes=(("It's worth noting that the cache is shared.", "The cache is shared."),
           ("Writes are slow. Notably, reads are fast.", "Writes are slow. Reads are fast.")),
))

add(Rule(
    "signposting", "en", "error", "rewrite",
    why="A sentence that announces what the text will do, instead of doing it.",
    todo="Delete the announcement or replace it with its content.",
    pattern=re.compile(SENT_START + r"(?:" + phrases(
        "in this section, we", "in this article, we", "in this post, we", "in this post, i will",
        "in this article, i will", "let's take a look at", "let's explore", "let's look at",
        "let's unpack", "we will explore", "this section explores", "this article explores")
        + r")[^.!?\n]*[.!?]", re.I),
    fires=("In this article, I will argue that caching is hard.", "Let's take a look at the numbers."),
    quiet=("The article explores nothing new.", "We looked at the numbers."),
))

add(Rule(
    "hype", "en", "error", "rewrite",
    why="Marketing vocabulary that promises without claiming anything.",
    todo="Say what the thing does, with a number if there is one.",
    pattern=re.compile(r"\b(?:" + phrases(
        "game-changer", "game changer", "game-changing", "unlock the power", "unlock new levels",
        "unleash the power", "supercharge", "supercharges", "seamlessly", "revolutionize", "revolutionizes",
        "cutting-edge", "transformative power", "a testament to") + r")\b", re.I),
    fires=("This library is a game-changer.", "It integrates seamlessly with Git."),
    quiet=("The change was small.", "The seams of the bag held."),
))

add(Rule(
    "corrective", "en", "error", "rewrite",
    why="Denying a reading nobody offered makes the reader process two claims to get one.",
    todo="Say what it is, without the denial.",
    pattern=re.compile(
        r"\b(?:(?:it|this|that|these|they|which)(?:'s|'re) not|isn't|aren't|wasn't) "
        r"(?:just |only |merely |simply |about )?[^.;:—!?\n]{1,60}?[,;—.]\s*"
        r"(?:it|this|that|they)(?:'s|'re| is| are)\b", re.I),
    fires=("Caching isn't just a trick, it's a design decision.",
           "It's not about speed. It's about trust.",
           "This isn't a bug — it's the spec."),
    quiet=("Caching is not only a trick, but a design decision.",
           "It isn't fast.", "Not only is it fast, it is cheap."),
))

add(Rule(
    "rhetorical-qa", "en", "error", "rewrite",
    why="A question the next few words answer makes the reader wait for a statement.",
    todo="State the answer as a sentence.",
    pattern=re.compile(
        r"(?:^|(?<=[.!?]\s))[^.!?\n]{2,60}\?\s+(?:simple|easy|the answer|it's simple|short answer|"
        r"spoiler|not quite|exactly)\b[^.!?\n]{0,60}[.!?]", re.I),
    fires=("So what's the fix? Simple: invalidate on write.",),
    quiet=("What is the fix? We do not know yet.", "Is it fast? Benchmarks say yes."),
))

add(Rule(
    "colon-reveal", "en", "warn", "suggest",
    why="A drumroll before the point: two words, a colon, then the claim.",
    todo="Write it as one sentence.",
    pattern=re.compile(
        r"(?:^|(?<=[.!?]\s))(The (?:result|catch|answer|problem|twist|kicker|takeaway|lesson|fix|trick|truth|upshot)"
        r"|The bottom line|The short version)\s?:\s+(\w)"),
    replace=lambda m, ln: f"{m.group(1)} is " + (
        m.group(2) if re.match(r"\w+", ln.scan[m.start(2):]).group(0).isupper() else m.group(2).lower()),
    fires=("The result: a faster build.",),
    quiet=("The result was a faster build.", "Results: see the table."),
    fixes=(("The result: a faster build.", "The result is a faster build."),),
))

add(Rule(
    "hedge-stack", "en", "error", "auto",
    why="Two hedges where one does the job.",
    todo="Keep one hedge.",
    pattern=re.compile(r"\b(may|might|could|can) (?:potentially|possibly|perhaps|conceivably)\b", re.I),
    replace=lambda m, ln: m.group(1),
    fires=("It may potentially fail.",),
    quiet=("It may fail.", "It could, perhaps, fail."),
    fixes=(("It may potentially fail.", "It may fail."),),
))

add(Rule(
    "metaphor-noun", "en", "warn", "rewrite",
    why="An abstract noun standing in for the concrete thing it names.",
    todo="Use the concrete word.",
    pattern=re.compile(r"\b(?:" + phrases(
        "landscape", "tapestry", "realm", "substrate", "surface area", "north star", "flywheel",
        "bedrock", "linchpin", "cornerstone", "nexus", "locus", "vantage point") + r")s?\b", re.I),
    fires=("The AI landscape is changing.", "Tests are the bedrock of the project."),
    quiet=("The land is flat.", "We changed the surface of the table."),
))
