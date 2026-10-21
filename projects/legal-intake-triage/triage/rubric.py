"""Load and validate rubric.yaml, the editable criteria behind every decision."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, get_args

import yaml

Level = Literal["low", "medium", "high"]
Priority = Literal["critical", "high", "normal", "low"]
LEVELS: tuple[Level, ...] = ("low", "medium", "high")
PRIORITIES: tuple[Priority, ...] = get_args(Priority)

DEFAULT_RUBRIC = Path(__file__).resolve().parent.parent / "rubric.yaml"


class RubricError(ValueError):
    pass


@dataclass(frozen=True)
class TypeDef:
    id: str
    name: str
    description: str
    examples: tuple[str, ...]
    urgency: Level
    risk: Level
    legal_deadline_days: int | None
    legal_basis: str | None


@dataclass(frozen=True)
class Signal:
    id: str
    name: str
    description: str
    examples: tuple[str, ...]
    urgency: Level | None
    risk: Level | None
    override: Priority | None


@dataclass(frozen=True)
class Rubric:
    version: str
    types: dict[str, TypeDef]
    signals: dict[str, Signal]
    matrix: dict[tuple[Level, Level], Priority]
    deadlines: dict[Priority, int]


def _level(value, where: str, optional: bool = False):
    if value is None and optional:
        return None
    if value not in LEVELS:
        raise RubricError(f"{where}: invalid level {value!r}")
    return value


def _priority(value, where: str, optional: bool = False):
    if value is None and optional:
        return None
    if value not in PRIORITIES:
        raise RubricError(f"{where}: invalid priority {value!r}")
    return value


def _unique(items: list[dict], kind: str) -> None:
    seen: set[str] = set()
    for item in items:
        if item["id"] in seen:
            raise RubricError(f"duplicate {kind} id {item['id']}")
        seen.add(item["id"])


def _type(d: dict) -> TypeDef:
    where = f"type {d['id']}"
    return TypeDef(
        id=d["id"],
        name=d["name"],
        description=d["description"],
        examples=tuple(d.get("examples", ())),
        urgency=_level(d.get("urgency"), where),
        risk=_level(d.get("risk"), where),
        legal_deadline_days=d.get("legal_deadline_days"),
        legal_basis=d.get("legal_basis"),
    )


def _signal(d: dict) -> Signal:
    where = f"signal {d['id']}"
    signal = Signal(
        id=d["id"],
        name=d["name"],
        description=d["description"],
        examples=tuple(d.get("examples", ())),
        urgency=_level(d.get("urgency"), where, optional=True),
        risk=_level(d.get("risk"), where, optional=True),
        override=_priority(d.get("override"), where, optional=True),
    )
    if signal.urgency is None and signal.risk is None and signal.override is None:
        raise RubricError(f"{where}: needs urgency, risk or override")
    return signal


def _matrix(data: dict) -> dict[tuple[Level, Level], Priority]:
    matrix = {}
    for urgency in LEVELS:
        row = data.get(urgency) or {}
        for risk in LEVELS:
            if risk not in row:
                raise RubricError(f"matrix: missing cell urgency={urgency} risk={risk}")
            matrix[(urgency, risk)] = _priority(row[risk], f"matrix {urgency}/{risk}")
    return matrix


def _deadlines(data: dict) -> dict[Priority, int]:
    if set(data) != set(PRIORITIES):
        raise RubricError(f"deadlines: need exactly {list(PRIORITIES)}")
    return {p: int(data[p]) for p in PRIORITIES}


def load_rubric(path: Path = DEFAULT_RUBRIC) -> Rubric:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    _unique(data["types"], "type")
    _unique(data["signals"], "signal")
    return Rubric(
        version=str(data["version"]),
        types={t["id"]: _type(t) for t in data["types"]},
        signals={s["id"]: _signal(s) for s in data["signals"]},
        matrix=_matrix(data["matrix"]),
        deadlines=_deadlines(data["deadlines"]),
    )
