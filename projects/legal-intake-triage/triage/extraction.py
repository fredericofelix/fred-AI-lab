"""What the model extracts from a request: type and signals, each with a verbatim span."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class SignalHit:
    id: str
    span: str


@dataclass(frozen=True)
class Extraction:
    type: str
    type_span: str
    secondary_type: str | None
    signals: tuple[SignalHit, ...]
    confidence: Literal["high", "low"]
    missing_info: tuple[str, ...]
