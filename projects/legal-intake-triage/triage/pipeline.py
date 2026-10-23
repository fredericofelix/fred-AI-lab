"""sanitize → extract → check (one retry) → decide, yielding a stage event per step for the UI."""

from __future__ import annotations

import dataclasses
import time
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Literal

from triage.checks import apply_floor, check_values, injection_markers
from triage.decide import DESIGN_REASONS, Decision, decide, fallback
from triage.extract import Extractor, build_prompt, build_retry_prompt
from triage.extraction import Extraction
from triage.rubric import Rubric
from triage.sanitize import TAG_PT, Sanitized, sanitize
from triage.validate import ExtractionInvalid, parse_extraction

MAX_CHARS = 3000
MAX_ATTEMPTS = 2

Stage = Literal["sanitize", "extract", "check", "decide"]


@dataclass(frozen=True)
class StageEvent:
    stage: Stage
    done: bool
    detail: str


@dataclass(frozen=True)
class TriageRun:
    input_text: str
    truncated: bool
    sanitized: Sanitized
    extraction: Extraction | None
    decision: Decision
    attempts: int
    seconds: float


def _masked_detail(masked: dict[str, int]) -> str:
    if not masked:
        return "nenhum identificador encontrado"
    parts = ", ".join(f"{n} {TAG_PT.get(tag, tag)}" for tag, n in masked.items())
    return f"{parts} {'mascarado' if sum(masked.values()) == 1 else 'mascarados'}"


def triage(text: str, rubric: Rubric, extractor: Extractor) -> Iterator[StageEvent | TriageRun]:
    # Never log or store the text: it may be a visitor's request.
    start = time.perf_counter()
    truncated = len(text) > MAX_CHARS
    text = text[:MAX_CHARS]

    yield StageEvent("sanitize", False, "")
    sanitized = sanitize(text)
    yield StageEvent("sanitize", True, _masked_detail(sanitized.masked))

    yield StageEvent("extract", False, "")
    extraction: Extraction | None = None
    prompt = build_prompt(sanitized.text, rubric)
    attempts = 0
    while attempts < MAX_ATTEMPTS and extraction is None:
        attempts += 1
        try:
            raw = extractor(prompt)
        except Exception:  # a crashed or slow model is an invalid attempt, never a stack trace
            raw, problems = "", ["model error"]
        else:
            try:
                extraction = parse_extraction(raw, rubric, sanitized.text)
                break
            except ExtractionInvalid as e:
                problems = e.problems
        prompt = build_retry_prompt(sanitized.text, rubric, raw, problems)
    yield StageEvent("extract", True, f"{attempts} tentativa(s)")

    yield StageEvent("check", False, "")
    notes: list[str] = []
    if extraction is not None:
        extraction, dropped = check_values(extraction, rubric)
        if dropped:
            notes.append("sinal descartado: " + "; ".join(dropped))
        extraction, added = apply_floor(extraction, sanitized.text, rubric)
        decision = decide(extraction, rubric)
    else:
        notes.append("saída inválida: vai para revisão humana")
        empty = Extraction("other", "", None, (), "low", ())
        floored, added = apply_floor(empty, sanitized.text, rubric)
        decision = fallback(rubric)
        if added:
            raised = decide(floored, rubric)
            design = tuple(r for r in raised.review_reasons if r in DESIGN_REASONS)
            decision = dataclasses.replace(raised, review_reasons=("invalid_output", *design))
    if added:
        notes.append("sinal adicionado pela regra fixa: " + ", ".join(added))
    if injection_markers(sanitized.text):
        notes.append("possível tentativa de manipulação do texto: vai para revisão humana")
        decision = dataclasses.replace(decision, review_reasons=(*decision.review_reasons, "suspected_injection"))
    yield StageEvent("check", True, "; ".join(notes) or "regras e trechos conferidos")

    yield StageEvent("decide", False, "")
    yield StageEvent("decide", True, "")

    yield TriageRun(
        input_text=text,
        truncated=truncated,
        sanitized=sanitized,
        extraction=extraction,
        decision=decision,
        attempts=attempts,
        seconds=time.perf_counter() - start,
    )


def run_triage(text: str, rubric: Rubric, extractor: Extractor) -> TriageRun:
    *_, run = triage(text, rubric, extractor)
    return run
