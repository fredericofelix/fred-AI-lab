"""A flag: one span of the visitor's text that may breach professional secrecy."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass


@dataclass(frozen=True)
class Flag:
    group: int
    kind: str
    start: int
    end: int
    text: str
    source: str  # "regex" | "lexicon" | "detector" | "model"
    note: str | None = None
    tag: str | None = None  # detector tag for group 6, e.g. "[CPF]"


def _fold_char(c: str) -> str:
    base = unicodedata.normalize("NFD", c)[0].lower()
    return base if len(base) == 1 else c


def fold(text: str) -> str:
    """Lowercase and strip accents character by character, so offsets match the original."""
    return "".join(_fold_char(c) for c in text)


def term_pattern(term: str) -> re.Pattern[str]:
    """Whole-word, case- and accent-insensitive pattern for a term, to run on fold(text)."""
    words = [re.escape(w) for w in fold(term).split()]
    return re.compile(r"(?<!\w)" + r"\s+".join(words) + r"(?!\w)")
