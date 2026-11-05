import json
from pathlib import Path

import pytest

from guardrail.cases import CASES_PATH, load_cases


def _write(tmp_path: Path, rows: list[dict]) -> Path:
    path = tmp_path / "cases.jsonl"
    path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows), encoding="utf-8")
    return path


def _row(**over):
    row = {"id": "C-1", "text": "Contrato da Construtora Alfa.", "labels": [{"group": 1, "kind": "org",
           "span": "Construtora Alfa"}], "clean": False, "doubtful": False, "note": ""}
    return {**row, **over}


def test_span_must_be_verbatim(tmp_path):
    bad = _row(labels=[{"group": 1, "kind": "org", "span": "Construtora Beta"}])
    with pytest.raises(ValueError):
        load_cases(_write(tmp_path, [bad]))


def test_clean_means_no_labels(tmp_path):
    with pytest.raises(ValueError):
        load_cases(_write(tmp_path, [_row(clean=True)]))
    with pytest.raises(ValueError):
        load_cases(_write(tmp_path, [_row(labels=[], clean=False)]))


def test_ids_unique(tmp_path):
    with pytest.raises(ValueError):
        load_cases(_write(tmp_path, [_row(), _row()]))


def test_unknown_kind_rejected(tmp_path):
    with pytest.raises(ValueError):
        load_cases(_write(tmp_path, [_row(labels=[{"group": 1, "kind": "cnj", "span": "Construtora Alfa"}])]))


def test_repo_cases_load():
    cases = load_cases(CASES_PATH)
    groups = {label.group for c in cases for label in c.labels}
    assert groups == {1, 2, 3, 4, 5, 6}
    assert any(c.clean for c in cases)
