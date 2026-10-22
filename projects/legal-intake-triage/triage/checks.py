"""Deterministic checks on what the model extracted, before the rubric decides."""

from __future__ import annotations

import dataclasses
import re

from triage.extraction import Extraction
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
