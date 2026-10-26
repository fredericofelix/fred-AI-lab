"""Labeled synthetic requests (cases.jsonl): the gold extraction for each one."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from triage.extraction import Extraction
from triage.rubric import Priority, Rubric
from triage.validate import ExtractionInvalid, parse_extraction


@dataclass(frozen=True)
class Case:
    id: str
    text: str
    gold: Extraction
    hard_case: str | None
    fred_priority: Priority | None
    status: Literal["provisional", "final"]


def load_cases(path: Path, rubric: Rubric) -> list[Case]:
    cases: list[Case] = []
    seen: set[str] = set()
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        data = json.loads(line)
        cid = data["id"]
        if cid in seen:
            raise ValueError(f"{cid}: duplicate case id")
        seen.add(cid)
        try:
            # Gold labels pass the same checks as model output.
            gold = parse_extraction(json.dumps(data, ensure_ascii=False), rubric, data["text"])
        except ExtractionInvalid as e:
            raise ValueError(f"{cid}: {e}") from e
        cases.append(
            Case(
                id=cid,
                text=data["text"],
                gold=gold,
                hard_case=data.get("hard_case"),
                fred_priority=data.get("fred_priority"),
                status=data["status"],
            )
        )
    return cases
