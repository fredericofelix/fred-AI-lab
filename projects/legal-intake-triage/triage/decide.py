"""Deterministic decision: the rubric, not the model, sets urgency, risk, priority and deadlines."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from triage.extraction import Extraction
from triage.rubric import LEVELS, Level, Priority, Rubric

ReviewReason = Literal[
    "high_risk",
    "override",
    "invalid_output",
    "timeout",
    "suspected_injection",
    "low_confidence",
    "missing_info",
    "type_other",
    "two_types",
]
DESIGN_REASONS = frozenset({"high_risk", "override"})

URGENCY_PT = {"low": "baixa", "medium": "média", "high": "alta"}
RISK_PT = {"low": "baixo", "medium": "médio", "high": "alto"}
PRIORITY_PT = {"critical": "crítica", "high": "alta", "normal": "normal", "low": "baixa"}


@dataclass(frozen=True)
class Fired:
    rule_id: str
    span: str
    effect: str


@dataclass(frozen=True)
class Decision:
    type: str
    urgency: Level
    risk: Level
    priority: Priority
    internal_deadline_days: int
    legal_deadline_days: int | None
    legal_basis: str | None
    fired: tuple[Fired, ...]
    review_reasons: tuple[ReviewReason, ...]

    @property
    def human_review(self) -> bool:
        return bool(self.review_reasons)

    @property
    def review_by_design(self) -> bool:
        return any(r in DESIGN_REASONS for r in self.review_reasons)

    @property
    def review_by_uncertainty(self) -> bool:
        return any(r not in DESIGN_REASONS for r in self.review_reasons)


def _max(a: Level, b: Level | None) -> Level:
    return a if b is None or LEVELS.index(a) >= LEVELS.index(b) else b


def _type_effect(rubric: Rubric, type_id: str) -> str:
    t = rubric.types[type_id]
    effect = f"tipo = {t.name}"
    if t.legal_deadline_days is not None:
        effect += f"; prazo legal {t.legal_deadline_days} dias"
    return effect


def _signal_effect(rubric: Rubric, signal_id: str) -> str:
    s = rubric.signals[signal_id]
    parts = []
    if s.urgency:
        parts.append(f"urgência → {URGENCY_PT[s.urgency]}")
    if s.risk:
        parts.append(f"risco → {RISK_PT[s.risk]}")
    if s.override:
        parts.append(f"prioridade → {PRIORITY_PT[s.override]} (regra de exceção)")
    return "; ".join(parts)


def decide(extraction: Extraction, rubric: Rubric) -> Decision:
    t = rubric.types[extraction.type]
    urgency, risk = t.urgency, t.risk
    override: Priority | None = None
    fired = [Fired(t.id, extraction.type_span, _type_effect(rubric, t.id))]
    for hit in extraction.signals:
        s = rubric.signals[hit.id]
        urgency, risk = _max(urgency, s.urgency), _max(risk, s.risk)
        override = override or s.override
        fired.append(Fired(s.id, hit.span, _signal_effect(rubric, s.id)))
    priority = override or rubric.matrix[(urgency, risk)]

    reasons: list[ReviewReason] = []
    if risk == "high":
        reasons.append("high_risk")
    if override:
        reasons.append("override")
    if extraction.confidence == "low":
        reasons.append("low_confidence")
    if extraction.missing_info:
        reasons.append("missing_info")
    if t.id == "other":
        reasons.append("type_other")
    if extraction.secondary_type and extraction.secondary_type != t.id:
        reasons.append("two_types")

    return Decision(
        type=t.id,
        urgency=urgency,
        risk=risk,
        priority=priority,
        internal_deadline_days=rubric.deadlines[priority],
        legal_deadline_days=t.legal_deadline_days,
        legal_basis=t.legal_basis,
        fired=tuple(fired),
        review_reasons=tuple(reasons),
    )


def fallback(rubric: Rubric) -> Decision:
    t = rubric.types["other"]
    priority = rubric.matrix[(t.urgency, t.risk)]
    return Decision(
        type=t.id,
        urgency=t.urgency,
        risk=t.risk,
        priority=priority,
        internal_deadline_days=rubric.deadlines[priority],
        legal_deadline_days=t.legal_deadline_days,
        legal_basis=t.legal_basis,
        fired=(),
        review_reasons=("invalid_output",),
    )
