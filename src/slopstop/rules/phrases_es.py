"""Spanish phrase rules, written from Spanish model output rather than translated."""
import re

from slopstop.rules import Rule, add, phrases, sentence_from

add(Rule(
    "opener-filler", "es", "error", "auto",
    why="A warm-up sentence delays the first real one.",
    todo="Delete the sentence.",
    pattern=sentence_from(phrases(
        "¡excelente pregunta", "excelente pregunta", "¡buena pregunta", "vamos a sumergirnos",
        "sumerjámonos", "en el mundo actual", "en la era digital", "en un mundo cada vez más")),
    replace="",
    fires=("¡Excelente pregunta! La caché es difícil.",),
    quiet=("La pregunta fue excelente.",),
    fixes=(("¡Excelente pregunta! La caché es difícil.", "La caché es difícil."),),
))

add(Rule(
    "user-address", "es", "error", "auto",
    why="A line meant for whoever asked for the text, left inside it.",
    todo="Delete the sentence.",
    pattern=sentence_from(phrases(
        "espero que te sirva", "espero que esto te ayude", "espero que te ayude", "si quieres, puedo",
        "si lo deseas", "no dudes en", "¡claro!", "¡por supuesto!", "aquí tienes")),
    replace="",
    fires=("La caché es compartida. Espero que te sirva.",),
    quiet=("Esperamos que el servidor responda.",),
    fixes=(("La caché es compartida. Espero que te sirva.", "La caché es compartida."),),
))

add(Rule(
    "meta-commentary", "es", "error", "auto",
    why="Announcing that a point matters delays the point.",
    todo="Delete the announcement and start with the point.",
    pattern=re.compile(r"(?:^|(?<=[.!?]\s)|(?<=^[-*+]\s))(?:" + phrases(
        "cabe destacar que", "es importante señalar que", "es importante destacar que",
        "vale la pena mencionar que", "cabe mencionar que", "cabe señalar que",
        "es importante mencionar que") + r")\s+(\w)", re.I),
    replace=lambda m, ln: m.group(1).upper(),
    fires=("Cabe destacar que la caché es compartida.",),
    quiet=("La nota cabe en la página.",),
    fixes=(("Cabe destacar que la caché es compartida.", "La caché es compartida."),),
))

add(Rule(
    "corrective", "es", "error", "rewrite",
    why="Denying a reading nobody offered makes the reader process two claims to get one.",
    todo="Say what it is, without the denial.",
    pattern=re.compile(
        r"\bno se trata (?:solo |solamente )?de [^.;:!?\n]{1,60}?,? sino\b"
        r"|\bno es (?:solo|solamente|simplemente|únicamente) [^.;:!?\n]{1,60}?[,;—.]\s*es\b", re.I),
    fires=("No se trata de velocidad, sino de confianza.", "No es solo un truco, es una decisión."),
    quiet=("No solo es rápido, sino también barato.", "No es rápido."),
))

add(Rule(
    "hype", "es", "error", "rewrite",
    why="Marketing vocabulary that promises without claiming anything.",
    todo="Say what the thing does, with a number if there is one.",
    pattern=re.compile(r"\b(?:" + phrases(
        "revolucionario", "revolucionaria", "al siguiente nivel", "potenciar al máximo",
        "sin precedentes", "de vanguardia", "cambia las reglas del juego") + r")\b", re.I),
    fires=("Una herramienta revolucionaria para equipos.",),
    quiet=("La revolución de 1959.",),
))

add(Rule(
    "metaphor-noun", "es", "warn", "rewrite",
    why="An abstract noun standing in for the concrete thing it names.",
    todo="Use the concrete word.",
    pattern=re.compile(r"\b(?:" + phrases("panorama", "paradigma", "hoja de ruta", "piedra angular")
                       + r")s?\b", re.I),
    fires=("El panorama de la IA cambia.",),
    quiet=("El plan tiene tres pasos.",),
))

add(Rule(
    "signposting", "es", "error", "rewrite",
    why="A sentence that announces what the text will do, instead of doing it.",
    todo="Delete the announcement or replace it with its content.",
    pattern=re.compile(r"(?:^|(?<=[.!?]\s))(?:" + phrases(
        "en este artículo exploraremos", "en este artículo, exploraremos", "en este artículo veremos",
        "en esta sección exploraremos", "en esta sección veremos", "a continuación exploraremos",
        "a continuación, exploraremos", "profundicemos en", "exploremos", "veamos más de cerca",
        "echemos un vistazo") + r")[^.!?\n]*[.!?]", re.I),
    fires=("En este artículo exploraremos cómo funciona la caché.", "Echemos un vistazo a los números."),
    quiet=("El artículo explora poco.", "Vimos los números."),
))
