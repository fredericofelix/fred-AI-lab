import json
from pathlib import Path

import pytest

from triage.cases import load_cases
from triage.extraction import SignalHit
from triage.rubric import load_rubric

REPO_CASES = Path(__file__).resolve().parent.parent / "cases.jsonl"


@pytest.fixture(scope="module")
def rubric():
    return load_rubric()


def _line(**overrides) -> dict:
    case = {
        "id": "T-900",
        "status": "provisional",
        "text": "Contrato de R$ 90 mil com o fornecedor para revisar.",
        "type": "contract",
        "type_span": "Contrato",
        "secondary_type": None,
        "signals": [{"id": "SIG-VALUE", "span": "R$ 90 mil"}],
        "confidence": "high",
        "missing_info": [],
        "hard_case": None,
        "fred_priority": None,
    }
    case.update(overrides)
    return case


def _write(tmp_path: Path, *cases: dict) -> Path:
    path = tmp_path / "cases.jsonl"
    path.write_text("\n".join(json.dumps(c, ensure_ascii=False) for c in cases) + "\n", encoding="utf-8")
    return path


def test_valid_line_loads(tmp_path, rubric):
    [case] = load_cases(_write(tmp_path, _line()), rubric)
    assert case.id == "T-900" and case.status == "provisional"
    assert case.gold.type == "contract"
    assert case.gold.signals == (SignalHit("SIG-VALUE", "R$ 90 mil"),)


def test_bad_signal_id_names_case(tmp_path, rubric):
    with pytest.raises(ValueError, match="T-900"):
        load_cases(_write(tmp_path, _line(signals=[{"id": "SIG-FOO", "span": "R$ 90 mil"}])), rubric)


def test_span_not_in_text_names_case(tmp_path, rubric):
    with pytest.raises(ValueError, match="T-900"):
        load_cases(_write(tmp_path, _line(type_span="aditivo")), rubric)


def test_duplicate_case_id(tmp_path, rubric):
    with pytest.raises(ValueError, match="T-900"):
        load_cases(_write(tmp_path, _line(), _line()), rubric)


def test_repo_cases_cover_hard_cases(rubric):
    cases = load_cases(REPO_CASES, rubric)
    assert len(cases) == 40
    assert all(c.status == "final" for c in cases)  # labeled by Fred, 2026-10-22
    assert {c.hard_case for c in cases} >= {"ambiguous", "two_types", "hidden_urgency", "disguised_dsar"}
    assert cases[0].id == "T-001" and cases[0].hard_case == "disguised_dsar"


def test_rubric_fit_case_recorded(rubric):
    by_id = {c.id: c for c in load_cases(REPO_CASES, rubric)}
    assert by_id["T-032"].fred_priority == "high"
