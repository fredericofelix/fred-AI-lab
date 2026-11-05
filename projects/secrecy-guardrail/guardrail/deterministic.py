"""Fixed rules the model can never override: CNJ numbers, markings, negotiation amounts, NDA cues."""

from __future__ import annotations

import re

from guardrail.flags import Flag, fold, term_pattern
from guardrail.rubric import Rubric

_CNJ_FORMATTED = re.compile(r"(?<!\d)(\d{7})-(\d{2})\.(\d{4})\.(\d)\.(\d{2})\.(\d{4})(?!\d)")
# Any other separator mix (spaces, dots, dashes, none): trusted only when the check digit validates.
_CNJ_LOOSE = re.compile(r"(?<!\d)(\d{7})[-.\s]?(\d{2})[-.\s]?(\d{4})[-.\s]?(\d)[-.\s]?(\d{2})[-.\s]?(\d{4})(?!\d)")
_PRECEDENT_WINDOW = 80
_NEGOTIATION_WINDOW = 60

NOTE_INVALID = "possível nº de processo"
NOTE_PRECEDENT = "se for precedente público, pode manter"

# "R$ 240 mil", "R$ 18.000,00", "R$ 1,2 milhão", "2 milhões" (same rule as the triage's amounts())
_MONEY = re.compile(r"(?:R\$\s*)?(\d{1,3}(?:\.\d{3})+|\d+)(?:,(\d+))?\s*(mil\b|milh(?:ão|ões|ao|oes)\b)?", re.I)

_INJECTION = re.compile(
    r"ignor[ea]\w*\s+(?:\w+\s+){0,3}instru[çc][õo]es"
    r"|desconsider\w*\s+(?:\w+\s+){0,3}(?:instru[çc][õo]es|regras)"
    r"|instru[çc][ãa]o (?:ao|para o) (?:modelo|sistema|assistente)"
    r"|n[ãa]o\s+(?:marque|sinalize)"
    r"|ignor[ea]\w*\s+o\s+guardrail"
    r"|</?\s*texto\s*>"
    r"|(?-i:\bSISTEMA\s*:)",  # an all-caps fake system turn, not the ordinary word "Sistema:"
    re.I,
)


def check_digit(number: str, year: str, segment: str, court: str, origin: str) -> int:
    """CNJ check digit (Res. CNJ 65/2008, ISO 7064 mod 97-10)."""
    return 98 - int(number + year + segment + court + origin + "00") % 97


def _valid(m: re.Match[str]) -> bool:
    number, digits, year, segment, court, origin = m.groups()
    return check_digit(number, year, segment, court, origin) == int(digits)


def _after_cue(folded: str, start: int, cues: tuple[str, ...], window: int) -> bool:
    before = folded[max(0, start - window) : start]
    return any(term_pattern(c).search(before) for c in cues)


def cnj_flags(text: str, rubric: Rubric) -> list[Flag]:
    folded = fold(text)
    flags = []
    seen: set[tuple[int, int]] = set()
    for pattern, loose in ((_CNJ_FORMATTED, False), (_CNJ_LOOSE, True)):
        for m in pattern.finditer(text):
            valid = _valid(m)
            if (m.start(), m.end()) in seen or (loose and not valid):
                continue  # loose digits are a case number only when the check digit says so
            seen.add((m.start(), m.end()))
            note = None if valid else NOTE_INVALID
            if _after_cue(folded, m.start(), rubric.precedent_cues, _PRECEDENT_WINDOW):
                note = NOTE_PRECEDENT
            flags.append(Flag(2, "cnj", m.start(), m.end(), m.group(0), "regex", note=note))
    return flags


def _lexicon_flags(text: str, terms: tuple[str, ...], group: int, kind: str) -> list[Flag]:
    folded = fold(text)
    flags = {}
    for term in terms:
        for m in term_pattern(term).finditer(folded):
            flags[(m.start(), m.end())] = Flag(group, kind, m.start(), m.end(), text[m.start() : m.end()], "lexicon")
    # a longer term ("estritamente confidencial") swallows a shorter one inside it ("confidencial")
    found = list(flags.values())
    kept = [f for f in found if not any(o != f and o.start <= f.start and f.end <= o.end for o in found)]
    return sorted(kept, key=lambda f: f.start)


def marking_flags(text: str, rubric: Rubric) -> list[Flag]:
    return _lexicon_flags(text, rubric.markings, 4, "marking")


def nda_cue_flags(text: str, rubric: Rubric) -> list[Flag]:
    return _lexicon_flags(text, rubric.nda_cues, 5, "third_party")


def amount_flags(text: str, rubric: Rubric) -> list[Flag]:
    folded = fold(text)
    flags = []
    for m in _MONEY.finditer(text):
        if not m.group(3) and not m.group(0).upper().startswith("R$"):
            continue  # a bare number (dates, percentages, counts) is not an amount
        around = folded[max(0, m.start() - _NEGOTIATION_WINDOW) : m.end() + _NEGOTIATION_WINDOW]
        if any(term_pattern(c).search(around) for c in rubric.negotiation_cues):
            span = m.group(0).rstrip()
            flags.append(Flag(3, "amount", m.start(), m.start() + len(span), span, "regex"))
    return flags


def injection_markers(text: str) -> list[str]:
    return [m.group(0) for m in _INJECTION.finditer(text)]


def deterministic_flags(text: str, rubric: Rubric) -> list[Flag]:
    return [
        *cnj_flags(text, rubric),
        *marking_flags(text, rubric),
        *amount_flags(text, rubric),
        *nda_cue_flags(text, rubric),
    ]
