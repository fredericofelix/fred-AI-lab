"""Labeled synthetic cases (cases.jsonl) for the eval. Labeling rules: LABELING.md."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from guardrail.rubric import KINDS

CASES_PATH = Path(__file__).resolve().parent.parent / "cases.jsonl"


@dataclass(frozen=True)
class Label:
    group: int
    kind: str
    span: str


@dataclass(frozen=True)
class Case:
    id: str
    text: str
    labels: tuple[Label, ...]
    clean: bool
    doubtful: bool
    note: str


def _case(row: dict) -> Case:
    labels = tuple(Label(int(x["group"]), x["kind"], x["span"]) for x in row.get("labels") or [])
    for label in labels:
        if label.kind not in KINDS.get(label.group, ()):
            raise ValueError(f"{row['id']}: kind {label.kind!r} not valid for group {label.group}")
        if label.span not in row["text"]:
            raise ValueError(f"{row['id']}: span not in text: {label.span!r}")
    clean = bool(row.get("clean", False))
    if clean == bool(labels):
        raise ValueError(f"{row['id']}: clean cases have no labels, and every other case has at least one")
    return Case(row["id"], row["text"], labels, clean, bool(row.get("doubtful", False)), row.get("note", ""))


def load_cases(path: Path = CASES_PATH) -> list[Case]:
    cases = [_case(json.loads(line)) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    ids = [c.id for c in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("case ids must be unique")
    return cases
