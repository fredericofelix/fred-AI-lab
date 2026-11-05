"""Load and validate rubric.yaml: groups, legal anchors, replacement templates and lexicons."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

RUBRIC_PATH = Path(__file__).resolve().parent.parent / "rubric.yaml"

KINDS: dict[int, frozenset[str]] = {
    1: frozenset({"person", "org"}),
    2: frozenset({"cnj"}),
    3: frozenset({"amount", "clause"}),
    4: frozenset({"marking"}),
    5: frozenset({"third_party"}),
    6: frozenset({"personal"}),
}


@dataclass(frozen=True)
class Group:
    id: int
    name: str
    reason: str
    anchor: str
    experimental: bool
    templates: dict[str, str | None]


@dataclass(frozen=True)
class Rubric:
    groups: dict[int, Group]
    markings: tuple[str, ...]
    nda_cues: tuple[str, ...]
    negotiation_cues: tuple[str, ...]
    precedent_cues: tuple[str, ...]


def _strings(data: dict, key: str) -> tuple[str, ...]:
    values = data.get(key) or []
    if not all(isinstance(v, str) and v.strip() for v in values):
        raise ValueError(f"{key}: every entry must be non-empty text")
    return tuple(values)


def load_rubric(path: Path = RUBRIC_PATH) -> Rubric:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    groups: dict[int, Group] = {}
    for raw in data.get("groups") or []:
        gid = raw.get("id")
        if gid not in KINDS or gid in groups:
            raise ValueError(f"unknown or repeated group id: {gid!r}")
        templates = dict(raw.get("templates") or {})
        if set(templates) != KINDS[gid]:
            raise ValueError(f"group {gid}: templates must cover exactly {sorted(KINDS[gid])}")
        for field in ("name", "reason", "anchor"):
            if not str(raw.get(field) or "").strip():
                raise ValueError(f"group {gid}: missing {field}")
        groups[gid] = Group(
            id=gid,
            name=raw["name"],
            reason=raw["reason"],
            anchor=raw["anchor"],
            experimental=bool(raw.get("experimental", False)),
            templates=templates,
        )
    if set(groups) != set(KINDS):
        raise ValueError(f"rubric must define groups {sorted(KINDS)}, found {sorted(groups)}")
    return Rubric(
        groups=groups,
        markings=_strings(data, "markings"),
        nda_cues=_strings(data, "nda_cues"),
        negotiation_cues=_strings(data, "negotiation_cues"),
        precedent_cues=_strings(data, "precedent_cues"),
    )
