"""Personal data and person names, found by the Privacy Seed detector (privacyseed-lgpd with [ml])."""

from __future__ import annotations

from functools import lru_cache
from typing import Protocol

from privacyseed_lgpd import Detector
from privacyseed_lgpd.entity import Result
from privacyseed_lgpd.taxonomy import load_taxonomy

from guardrail.flags import Flag

_TAXONOMY = load_taxonomy()


class Analyzer(Protocol):
    def analyze(self, text: str) -> Result: ...


@lru_cache(maxsize=1)
def default_detector() -> Detector:
    """Full detector (regex + GLiNER2 + sensitive data), built once per process."""
    return Detector()


def personal_flags(text: str, detector: Analyzer | None = None) -> tuple[list[Flag], list[str]]:
    result = (detector or default_detector()).analyze(text)
    flags = []
    for e in (*result.entities, *result.flagged):
        if e.label == "person_name":
            flags.append(Flag(1, "person", e.start, e.end, e.text, "detector"))
        else:
            flags.append(Flag(6, "personal", e.start, e.end, e.text, "detector", tag=_TAXONOMY.tag(e.label)))
    return sorted(flags, key=lambda f: f.start), list(result.warnings)
