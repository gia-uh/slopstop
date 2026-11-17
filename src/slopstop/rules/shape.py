"""Rules that read the shape of the document: paragraphs, sentences, lists and sections."""
import re

from slopstop import text
from slopstop.rules import Doc, Rule, add, phrases

CLOSER = {
    "en": re.compile(r"(?:in short|in sum|in summary|all in all|the bottom line is|in conclusion|"
                     r"at the end of the day|to sum up|in a nutshell)\b", re.I),
    "es": re.compile(r"(?:en resumen|en definitiva|en conclusión|en pocas palabras|al final del día|"
                     r"en síntesis)\b", re.I),
}
UPBEAT = {
    "en": re.compile(r"\b(?:" + phrases(
        "the future is bright", "the possibilities are endless", "endless possibilities", "only time will tell",
        "the journey is just beginning", "exciting times ahead", "the future looks bright",
        "an exciting future", "the road ahead", "exciting journey") + r")\b", re.I),
    "es": re.compile(r"\b(?:" + phrases(
        "el futuro es prometedor", "las posibilidades son infinitas", "solo el tiempo dirá",
        "un futuro brillante", "el camino por delante") + r")\b", re.I),
}


def _summary_closer(doc: Doc, rule: Rule, threshold) -> list:
    pat = CLOSER.get(doc.lang)
    out = []
    if not pat:
        return out
    ss = doc.sentences
    for i, s in enumerate(ss):
        last = i + 1 == len(ss) or ss[i + 1].par != s.par
        first = i == 0 or ss[i - 1].par != s.par
        if not last or first or not pat.match(text.normalize(s.text)):
            continue
        ln = None
        for n in range(s.line, s.line + 3):
            cand = doc.line(n)
            hits = list(pat.finditer(cand.scan)) if cand else []
            if hits:
                ln, start = cand, hits[-1].start()
                break
        if ln is None:
            continue
        end = re.search(r"[.!?](?=\s|$)", ln.scan[start:])
        rep = "" if end and not ln.scan[start + end.end():].strip() else None
        stop = start + end.end() if end else len(ln.raw)
        # take the space before the sentence with it
        lead = len(ln.raw[:start]) - len(ln.raw[:start].rstrip())
        out.append(rule.finding(ln.n, start - lead, stop, ln.raw[start:stop], rep))
    return out


add(Rule(
    "summary-closer", "any", "error", "suggest",
    why="The paragraph's last sentence restates what the reader just read.",
    todo="Delete the sentence, or replace it with something the paragraph has not said.",
    scan=_summary_closer,
    fires=("Writes go to the database. Then the cache entry is dropped. In short, the cache never lies.",),
    quiet=("In short, the cache never lies. Writes go to the database.",
           "In the end, I aim to convince you. Writes go first."),
    fixes=(("Writes go to the database. In short, the cache never lies.", "Writes go to the database."),),
))


def _upbeat(doc: Doc, rule: Rule, threshold) -> list:
    pat = UPBEAT.get(doc.lang)
    if not pat or not doc.paragraphs:
        return []
    tail = doc.paragraphs[-2:] if len(doc.paragraphs) > 1 else doc.paragraphs
    first = tail[0].line
    return [rule.finding(ln.n, m.start(), m.end(), ln.raw[m.start():m.end()])
            for ln in doc.lines if ln.n >= first for m in pat.finditer(ln.scan)]


add(Rule(
    "upbeat-ending", "any", "error", "rewrite",
    why="A closing line of vague optimism ends the text on nothing.",
    todo="End on the last concrete point.",
    scan=_upbeat,
    fires=("Caching is hard.\n\nWe shipped it anyway, and the future is bright.",),
    quiet=("The future is bright, they said.\n\nThen the build broke.\n\nWe fixed it on Monday.",),
))


def _long_paragraph(doc: Doc, rule: Rule, threshold: int) -> list:
    return [rule.finding(p.line, 0, 0, p.text.split("\n")[0][:80], note=f"{p.words} words")
            for p in doc.paragraphs if p.words > threshold]


add(Rule(
    "long-paragraph", "any", "warn", "rewrite",
    why="A very long paragraph hides where the argument turns.",
    todo="Break it where the argument moves on. Insert paragraph breaks only.",
    scan=_long_paragraph, threshold=180,
    fires=(" ".join(["The cache holds the value."] * 50),),
    quiet=("The cache holds the value. " * 5,),
))


def _flat_rhythm(doc: Doc, rule: Rule, threshold: int) -> list:
    out, run = [], 1
    lens = [(s, len(text.tokenize(s.text))) for s in doc.sentences]
    for i in range(1, len(lens)):
        if abs(lens[i][1] - lens[i - 1][1]) <= 4 and lens[i][1] > 4:
            run += 1
            if run == threshold:
                s = lens[i - threshold + 1][0]
                out.append(rule.finding(s.line, 0, 0, s.text[:80],
                                        note=f"{threshold} sentences in a row within 4 words of each other"))
        else:
            run = 1
    return out


add(Rule(
    "flat-rhythm", "any", "warn", "rewrite",
    why="Sentences of the same length, one after another, read as a drone.",
    todo="Join two of them or split one, so the lengths vary.",
    scan=_flat_rhythm, threshold=8,
    fires=(" ".join(f"The cache number {w} holds one value." for w in "one two three four five six seven eight".split()),),
    quiet=("The cache holds a value. It is fast. When a write arrives, the entry is dropped and the next "
           "read goes to the database, which is slow. Then it is fast again.",),
))


def _repeated_opener(doc: Doc, rule: Rule, threshold) -> list:
    ss, out = doc.sentences, []
    for i in range(2, len(ss)):
        firsts = [text.tokenize(ss[j].text)[:1] for j in (i - 2, i - 1, i)]
        if firsts[0] and firsts[0] == firsts[1] == firsts[2] and ss[i - 2].par == ss[i].par:
            out.append(rule.finding(ss[i].line, 0, 0, ss[i].text[:80],
                                    note=f"three sentences in a row open with '{firsts[0][0]}'"))
    return out


add(Rule(
    "repeated-opener", "any", "warn", "rewrite",
    why="Three sentences in a row opening with the same word read as a list pretending to be prose.",
    todo="Vary the openings, or merge the sentences.",
    scan=_repeated_opener,
    fires=("This means speed. This shows care. This is the point.",),
    quiet=("This means speed. It shows care. The point stands.",),
))

TRIPLET = re.compile(r"\b[\w'-]+(?: [\w'-]+){0,2}, [\w'-]+(?: [\w'-]+){0,2},? (?:and|or|y|o) [\w'-]+", re.I)


def _triplets(doc: Doc, rule: Rule, threshold: int) -> list:
    out = []
    for p in doc.paragraphs:
        k = len(TRIPLET.findall(text.strip_markdown(doc.para_scan(p))))
        if k > threshold:
            out.append(rule.finding(p.line, 0, 0, p.text.split("\n")[0][:80], note=f"{k} lists of three"))
    return out


add(Rule(
    "triplet-habit", "any", "warn", "rewrite",
    why="List after list of three items reads as rhythm, not content.",
    todo="Keep the items that are real; two or four are fine.",
    scan=_triplets, threshold=2,
    fires=("It is fast, cheap, and safe. Teams want clear, concise, and actionable docs. "
           "We need speed, focus, and care.",),
    quiet=("It is fast, cheap, and safe. Teams want docs.",),
))

LIST_ITEM = re.compile(r"^\s*(?:[-*+]|\d+\.)\s+")
LABEL_REST = re.compile(r"^\s*(?:[-*+]|\d+\.)\s+\*\*[^*]+\*\*\s*[:.—-]?\s*(.*)$")


def _label_bullets(doc: Doc, rule: Rule, threshold) -> list:
    out, i, lines = [], 0, doc.lines
    while i < len(lines):
        if not lines[i].item:
            i += 1
            continue
        j, items = i, []
        while j < len(lines) and (lines[j].item or lines[j].raw.startswith((" ", "\t"))) \
                and (j == i or lines[j].n == lines[j - 1].n + 1):
            if lines[j].item:
                items.append(lines[j])
            j += 1
        def sentence_label(ln) -> bool:
            m = LABEL_REST.match(ln.raw)
            return bool(m and ln.label and len(text.tokenize(m.group(1))) >= 8)
        if len(items) >= 3 and all(sentence_label(ln) for ln in items):
            out.append(rule.finding(items[0].n, 0, 0, items[0].raw[:80], note=f"{len(items)} labelled items"))
        i = max(j, i + 1)
    return out


add(Rule(
    "label-bullets", "any", "warn", "rewrite",
    why="A list of bold labels, each followed by a full sentence, is a paragraph chopped into slides.",
    todo="Write it as a paragraph, or as a plain list without labels.",
    scan=_label_bullets,
    fires=("- **Speed**: The cache makes every read about ten times faster.\n"
           "- **Cost**: The cache needs memory that we would otherwise give to workers.\n"
           "- **Risk**: The cache can serve stale data when a write is lost.",),
    quiet=("- **Section**: §2.1\n- **Lines**: 40-52\n- **Type**: claim",),
))

HEADING = re.compile(r"^#{2,6}\s")


def _heading_spray(doc: Doc, rule: Rule, threshold: int) -> list:
    raw = doc.raw.split("\n")
    heads = [ln.n for ln in doc.lines if HEADING.match(ln.raw)]
    short = []
    for k, h in enumerate(heads):
        end = heads[k + 1] - 1 if k + 1 < len(heads) else len(raw)
        if text.word_count("\n".join(raw[h:end])) < threshold:
            short.append(h)
    if len(short) < 3:
        return []
    return [rule.finding(short[0], 0, 0, raw[short[0] - 1][:80],
                         note=f"{len(short)} sections under {threshold} words")]


add(Rule(
    "heading-spray", "any", "warn", "rewrite",
    why="Headings over sections of a few sentences break a short text into fragments.",
    todo="Merge the short sections and drop their headings.",
    scan=_heading_spray, threshold=80,
    fires=("## One\n\nShort text.\n\n## Two\n\nShort text.\n\n## Three\n\nShort text.",),
    quiet=("## One\n\n" + "Long text here. " * 30 + "\n\n## Two\n\n" + "Long text here. " * 30,),
))
