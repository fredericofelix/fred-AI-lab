"""Check the model output: known rule ids and spans that really appear in the request."""

from __future__ import annotations

import json
import re

from triage.extraction import Extraction, SignalHit
from triage.rubric import Rubric

_WS = re.compile(r"\s+")


class ExtractionInvalid(ValueError):
    def __init__(self, problems: list[str]):
        super().__init__("; ".join(problems))
        self.problems = problems


def span_in_text(span: str, text: str) -> bool:
    return _WS.sub(" ", span).strip() in _WS.sub(" ", text)


def _first_object(raw: str) -> dict | None:
    decoder = json.JSONDecoder()
    for match in re.finditer(r"\{", raw):
        try:
            obj, _ = decoder.raw_decode(raw, match.start())
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            return obj
    return None


def _check_span(span, where: str, text: str, problems: list[str]) -> str:
    if not isinstance(span, str) or not span.strip():
        problems.append(f"{where}: empty span")
        return ""
    if re.search(r"\bSIG-[A-Z-]+\b", span):
        problems.append(f"{where}: span quotes a rule id, not the request: {span!r}")
    if not span_in_text(span, text):
        problems.append(f"{where}: span not found verbatim in the request: {span!r}")
    return span


def parse_extraction(raw: str, rubric: Rubric, text: str) -> Extraction:
    data = _first_object(raw)
    if data is None:
        raise ExtractionInvalid(["output has no JSON object"])
    problems: list[str] = []

    for key in ("type", "type_span", "signals", "confidence"):
        if key not in data:
            problems.append(f"missing key {key!r}")

    type_id = data.get("type")
    if "type" in data and type_id not in rubric.types:
        problems.append(f"unknown type {type_id!r}")
    secondary = data.get("secondary_type")
    if secondary is not None and secondary not in rubric.types:
        problems.append(f"unknown secondary_type {secondary!r}")
    type_span = _check_span(data.get("type_span"), "type_span", text, problems) if "type_span" in data else ""

    confidence = data.get("confidence")
    if "confidence" in data and confidence not in ("high", "low"):
        problems.append(f"confidence must be 'high' or 'low', got {confidence!r}")

    hits: list[SignalHit] = []
    seen: set[str] = set()
    signals = data.get("signals", [])
    if not isinstance(signals, list):
        problems.append("signals must be a list")
        signals = []
    for item in signals:
        sid = item.get("id") if isinstance(item, dict) else None
        if sid not in rubric.signals:
            problems.append(f"unknown signal {sid!r}")
            continue
        span = _check_span(item.get("span"), f"signal {sid}", text, problems)
        if sid not in seen:
            seen.add(sid)
            hits.append(SignalHit(sid, span))

    missing = data.get("missing_info") or []
    if not isinstance(missing, list):
        problems.append("missing_info must be a list")
        missing = []

    if problems:
        raise ExtractionInvalid(problems)
    return Extraction(
        type=type_id,
        type_span=type_span,
        secondary_type=secondary,
        signals=tuple(hits),
        confidence=confidence,
        missing_info=tuple(str(m) for m in missing),
    )
