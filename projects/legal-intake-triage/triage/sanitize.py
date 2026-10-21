"""Step 1: mask identifiers with the Privacy Seed detector before any model reads the text."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from privacyseed_lgpd import Detector
from privacyseed_lgpd.recognizers.regex import RegexRecognizer
from privacyseed_lgpd.taxonomy import load_taxonomy

# Light core only (regex + check digits): no [ml] extra, so no names or addresses.
_DETECTOR = Detector(recognizers=[RegexRecognizer()])
_TAXONOMY = load_taxonomy()


@dataclass(frozen=True)
class Sanitized:
    text: str
    masked: dict[str, int]
    flagged: dict[str, int]


def _count(entities) -> dict[str, int]:
    return dict(Counter(_TAXONOMY.tag(e.label) for e in entities))


def sanitize(text: str) -> Sanitized:
    result = _DETECTOR.analyze(text)
    return Sanitized(text=result.anonymized, masked=_count(result.entities), flagged=_count(result.flagged))
