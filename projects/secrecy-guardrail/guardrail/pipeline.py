"""The whole check, as a stream of stage events for the live step list, ending in a GuardrailRun."""

from __future__ import annotations

import re
import time
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Literal

from guardrail.deterministic import deterministic_flags, injection_markers
from guardrail.flags import Flag, fold, term_pattern
from guardrail.masking import mask_for_model
from guardrail.merge import assign_labels, merge, preview, verdict
from guardrail.model_pass import ModelPass, locate
from guardrail.personal import Analyzer, personal_flags
from guardrail.rubric import Rubric

MAX_CHARS = 3000

Stage = Literal["personal", "rules", "model", "merge"]
ModelStatus = Literal["ok", "timeout", "error"]


@dataclass(frozen=True)
class StageEvent:
    stage: Stage
    done: bool
    detail: str


@dataclass(frozen=True)
class GuardrailRun:
    flags: list[Flag]
    labels: dict[Flag, str | None]
    preview: str
    verdict: str
    model_status: ModelStatus
    dropped_spans: int
    injection: list[str]
    truncated: bool
    warnings: list[str]
    seconds: dict[str, float]


_PLACEHOLDER_NAME = re.compile(r"(?:empresa|companhia|parte|cliente|fornecedor|sociedade)\s+[a-z]")


def _generic(flag: Flag, text: str, rubric: Rubric) -> bool:
    """A company name from the model that identifies no one: placeholder, statute, court or generic public body."""
    if flag.group != 1 or flag.kind != "org":
        return False
    if text[flag.start - 1 : flag.start] == "[" and text[flag.end : flag.end + 1] == "]":
        return True
    name = " ".join(fold(flag.text).split())
    return bool(_PLACEHOLDER_NAME.fullmatch(name)) or any(term_pattern(g).fullmatch(name) for g in rubric.generic_names)


def _count(n: int, one: str, many: str) -> str:
    return f"{n} {one if n == 1 else many}"


def check(
    text: str, rubric: Rubric, model_pass: ModelPass, detector: Analyzer | None = None
) -> Iterator[StageEvent | GuardrailRun]:
    # Never log or store the text: it is what a lawyer was about to send to an AI tool.
    seconds: dict[str, float] = {}
    truncated = len(text) > MAX_CHARS
    text = text[:MAX_CHARS]

    yield StageEvent("personal", False, "")
    t = time.perf_counter()
    personal, warnings = personal_flags(text, detector)
    seconds["personal"] = time.perf_counter() - t
    names = sum(1 for f in personal if f.group == 1)
    yield StageEvent(
        "personal",
        True,
        f"{_count(len(personal) - names, 'dado pessoal', 'dados pessoais')}, {_count(names, 'nome', 'nomes')}",
    )

    yield StageEvent("rules", False, "")
    t = time.perf_counter()
    rules = deterministic_flags(text, rubric)
    injection = injection_markers(text)
    seconds["rules"] = time.perf_counter() - t
    yield StageEvent("rules", True, _count(len(rules), "ponto por regra fixa", "pontos por regra fixa"))

    yield StageEvent("model", False, "")
    t = time.perf_counter()
    fixed = [*personal, *rules]
    masked = mask_for_model(text, fixed)
    model_flags: list[Flag] = []
    dropped = 0
    status: ModelStatus = "ok"
    try:
        model_flags, dropped = locate(model_pass(masked.text), masked, text)
        model_flags = [f for f in model_flags if not _generic(f, text, rubric)]
    except TimeoutError:
        status = "timeout"
    except Exception:  # a crashed or confused model is reported, never shown as a stack trace
        status = "error"
    seconds["model"] = time.perf_counter() - t
    detail = {"ok": _count(len(model_flags), "ponto", "pontos"), "timeout": "tempo esgotado", "error": "falhou"}
    yield StageEvent("model", True, detail[status])

    yield StageEvent("merge", False, "")
    flags = merge(fixed, model_flags)
    labels = assign_labels(flags, rubric)
    result_verdict = verdict(flags, status)
    yield StageEvent("merge", True, _count(len(flags), "ponto de atenção", "pontos de atenção"))

    yield GuardrailRun(
        flags=flags,
        labels=labels,
        preview=preview(text, labels),
        verdict=result_verdict,
        model_status=status,
        dropped_spans=dropped,
        injection=injection,
        truncated=truncated,
        warnings=warnings,
        seconds=seconds,
    )


def run_check(text: str, rubric: Rubric, model_pass: ModelPass, detector: Analyzer | None = None) -> GuardrailRun:
    *_, run = check(text, rubric, model_pass, detector)
    return run
