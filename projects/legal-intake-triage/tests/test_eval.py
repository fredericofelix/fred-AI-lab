import json
from pathlib import Path

import pytest

from triage.cases import Case, load_cases
from triage.decide import decide, fallback
from triage.eval import gold_runs, score
from triage.extraction import Extraction, SignalHit
from triage.pipeline import TriageRun
from triage.rubric import load_rubric
from triage.sanitize import Sanitized

REPO_CASES = Path(__file__).resolve().parent.parent / "cases.jsonl"


@pytest.fixture(scope="module")
def rubric():
    return load_rubric()


def _ex(type_, *signals, confidence="high"):
    return Extraction(type_, "t", None, tuple(SignalHit(s, "s") for s in signals), confidence, ())


def _case(cid, gold, fred_priority=None):
    return Case(cid, "texto", gold, None, fred_priority, "provisional")


def _run(rubric, extraction, seconds=1.0):
    decision = decide(extraction, rubric) if extraction else fallback(rubric)
    return TriageRun("texto", False, Sanitized("texto", {}, {}), extraction, decision, 1, seconds)


@pytest.fixture
def report(rubric):
    cases = [
        _case("C1", _ex("contract", "SIG-VALUE")),  # serious: risk high
        _case("C2", _ex("litigation", "SIG-HARD-DEADLINE")),  # serious: critical
        _case("C3", _ex("advisory")),
        _case("C4", _ex("contract"), fred_priority="high"),
    ]
    runs = [
        _run(rubric, _ex("contract", confidence="low"), 2.0),  # missed the value, but goes to a human
        _run(rubric, _ex("litigation", "SIG-HARD-DEADLINE"), 4.0),
        _run(rubric, _ex("advisory"), 1.0),
        _run(rubric, None, 1.0),  # invalid output
    ]
    return score(cases, runs, rubric, "test-model")


def test_serious_case_caught_only_by_review_counts_for_recall_not_strict(report):
    assert report.high_risk_recall == 1.0
    assert report.high_risk_recall_strict == 0.5


def test_review_rates_split_by_kind(report):
    assert report.review_rate_design == 0.25
    assert report.review_rate_uncertainty == 0.5


def test_accuracies(report):
    assert report.type_accuracy == 0.75
    assert report.signal_recall == 0.5
    assert report.priority_accuracy == 0.75
    assert report.valid_output_rate == 0.75


def test_latency_and_metadata(report):
    assert report.model == "test-model" and report.n == 4
    assert report.mean_seconds == 2.0 and report.max_seconds == 4.0


def test_rubric_fit_lists_mismatch(report):
    assert report.rubric_fit == [{"id": "C4", "rubric_priority": "low", "fred_priority": "high"}]
    assert len(report.rows) == 4
    assert json.loads(report.to_json())["model"] == "test-model"


def test_gold_runs_score_perfectly_on_repo_cases(rubric):
    cases = load_cases(REPO_CASES, rubric)
    r = score(cases, gold_runs(cases, rubric), rubric, "gold")
    assert (r.high_risk_recall, r.type_accuracy, r.priority_accuracy, r.signal_recall) == (1.0, 1.0, 1.0, 1.0)
