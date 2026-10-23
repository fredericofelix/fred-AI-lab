"""Deterministic checks on what the model extracted, before the rubric decides."""

from __future__ import annotations

import dataclasses
import re

from triage.extraction import Extraction, SignalHit
from triage.rubric import Rubric

# "R$ 240 mil", "80 mil", "R$ 18.000,00", "R$ 1,2 milhão", "2 milhões"
_MONEY = re.compile(r"(?:R\$\s*)?(\d{1,3}(?:\.\d{3})+|\d+)(?:,(\d+))?\s*(mil\b|milh(?:ão|ões|ao|oes)\b)?", re.I)
_SCALE = {"mil": 1_000, "milh": 1_000_000}


def amounts(text: str) -> list[int]:
    found = []
    for m in _MONEY.finditer(text):
        whole, frac, scale = m.group(1), m.group(2), m.group(3)
        has_currency = m.group(0).upper().startswith("R$")
        if not scale and not has_currency:
            continue  # a bare number (dates, percentages, counts) is not an amount
        value = float(whole.replace(".", "") + (f".{frac}" if frac else ""))
        if scale:
            value *= _SCALE["mil" if scale.lower() == "mil" else "milh"]
        found.append(int(round(value)))
    return found


def _brl(value: int) -> str:
    return f"R$ {value:,}".replace(",", ".")


def check_values(extraction: Extraction, rubric: Rubric) -> tuple[Extraction, list[str]]:
    """Drop value signals whose quoted span does not show an amount above the rubric's threshold."""
    kept, dropped = [], []
    for hit in extraction.signals:
        threshold = rubric.signals[hit.id].min_value
        if threshold is None:
            kept.append(hit)
            continue
        values = amounts(hit.span)
        if not values:
            dropped.append(f"{hit.id}: o trecho citado não traz um valor")
        elif max(values) <= threshold:
            dropped.append(f"{hit.id}: valor citado ({_brl(max(values))}) não passa de {_brl(threshold)}")
        else:
            kept.append(hit)
    if not dropped:
        return extraction, []
    return dataclasses.replace(extraction, signals=tuple(kept)), dropped


# Safety floor for the two override signals: plain keywords that can only raise the result.
# A model can be talked out of a signal; these words cannot.
_FLOOR = {
    "SIG-HARD-DEADLINE": re.compile(
        r"cita[çc][ãa]o|intima[çc][ãa]o|notifica[çc][ãa]o extrajudicial|carta do (?:f[óo]rum|tribunal)", re.I
    ),
    "SIG-INCIDENT": re.compile(r"vazamento|acesso indevido|vazaram|vazou", re.I),
}

_INJECTION = re.compile(
    r"ignor[ea]\w*\s+(?:\w+\s+){0,3}instru[çc][õo]es"
    r"|desconsider\w*\s+(?:\w+\s+){0,3}(?:instru[çc][õo]es|regras)"
    r"|instru[çc][ãa]o (?:ao|para o) (?:modelo|sistema|assistente)"
    r"|</?\s*demanda\s*>"
    r"|\bSISTEMA\s*:",
    re.I,
)


def override_floor(text: str) -> list[SignalHit]:
    hits = []
    for signal_id, pattern in _FLOOR.items():
        m = pattern.search(text)
        if m:
            hits.append(SignalHit(signal_id, m.group(0)))
    return hits


def apply_floor(extraction: Extraction, text: str, rubric: Rubric) -> tuple[Extraction, list[str]]:
    """Add override signals the keywords show but the model left out. Never removes anything."""
    present = {h.id for h in extraction.signals}
    missing = [h for h in override_floor(text) if h.id not in present and h.id in rubric.signals]
    if not missing:
        return extraction, []
    signals = (*extraction.signals, *missing)
    return dataclasses.replace(extraction, signals=signals), [h.id for h in missing]


def injection_markers(text: str) -> list[str]:
    return [m.group(0) for m in _INJECTION.finditer(text)]
