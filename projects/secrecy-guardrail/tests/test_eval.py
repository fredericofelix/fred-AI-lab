import json

from guardrail.cases import Case, Label
from guardrail.eval import Report, score
from guardrail.flags import Flag
from guardrail.pipeline import GuardrailRun


def _run(flags, status="ok", seconds=1.0):
    return GuardrailRun(flags, {}, "", "", status, 0, [], False, [], {"model": seconds})


def _flag(text, sub, group, kind="org"):
    start = text.index(sub)
    return Flag(group, kind, start, start + len(sub), sub, "model")


TEXT = "Contrato da Construtora Alfa no processo 0001234-34.2025.8.13.0024, teto R$ 10 mil."
CASE = Case("C-1", TEXT, (Label(1, "org", "Construtora Alfa"), Label(2, "cnj", "0001234-34.2025.8.13.0024"),
                          Label(3, "amount", "R$ 10 mil")), False, False, "")
CLEAN = Case("C-2", "Qual o prazo de prescrição?", (), True, False, "")


def test_overlap_same_group_is_hit():
    report = score([CASE], [_run([_flag(TEXT, "Alfa", 1)])], "m")
    assert report.recall[1] == 1.0
    assert report.recall[2] == 0.0


def test_overlap_other_group_is_miss():
    report = score([CASE], [_run([_flag(TEXT, "Construtora Alfa", 5, "third_party")])], "m")
    assert report.recall[1] == 0.0
    assert report.precision[5] == 0.0


def test_headline_excludes_group_3():
    flags = [_flag(TEXT, "Construtora Alfa", 1), _flag(TEXT, "0001234-34.2025.8.13.0024", 2, "cnj")]
    report = score([CASE], [_run(flags)], "m")
    assert report.headline_recall == 1.0
    assert report.recall[3] == 0.0


def test_clean_false_alarm():
    alarm = _run([Flag(4, "marking", 0, 4, "Qual", "lexicon")])
    report = score([CLEAN, CLEAN], [alarm, _run([])], "m")
    assert report.clean_false_alarm == 0.5
    assert report.flag_precision == 0.0


def test_misses_and_failures():
    report = score([CASE], [_run([], status="timeout")], "m")
    assert report.model_failures == 1
    assert {m["span"] for m in report.misses} == {"Construtora Alfa", "0001234-34.2025.8.13.0024", "R$ 10 mil"}


def test_report_json_roundtrip():
    report = score([CASE, CLEAN], [_run([_flag(TEXT, "Alfa", 1)], seconds=2.0), _run([], seconds=4.0)], "m")
    data = json.loads(report.to_json())
    assert data["model"] == "m" and data["seconds_max"] == 4.0
    assert Report(**{**data, "recall": {int(k): v for k, v in data["recall"].items()},
                     "precision": {int(k): v for k, v in data["precision"].items()}}) == report
