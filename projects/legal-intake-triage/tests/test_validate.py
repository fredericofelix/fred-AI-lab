import json

import pytest

from triage.extraction import Extraction, SignalHit
from triage.rubric import load_rubric
from triage.validate import ExtractionInvalid, parse_extraction, span_in_text

TEXT = "Oi jurídico, o cliente quer saber quais dados temos dele e apagar tudo,\nsenão vai no Procon."


@pytest.fixture(scope="module")
def rubric():
    return load_rubric()


def _raw(**overrides) -> str:
    data = {
        "type": "data_subject_rights",
        "type_span": "quais dados temos dele e apagar tudo",
        "signals": [{"id": "SIG-REGULATOR", "span": "senão vai no Procon"}],
        "confidence": "high",
    }
    data.update(overrides)
    return json.dumps(data, ensure_ascii=False)


def test_valid_json_becomes_extraction(rubric):
    assert parse_extraction(_raw(), rubric, TEXT) == Extraction(
        type="data_subject_rights",
        type_span="quais dados temos dele e apagar tudo",
        secondary_type=None,
        signals=(SignalHit("SIG-REGULATOR", "senão vai no Procon"),),
        confidence="high",
        missing_info=(),
    )


def test_json_inside_fence_and_prose_is_parsed(rubric):
    raw = f"Claro! Segue a triagem:\n```json\n{_raw()}\n```\nEspero ter ajudado."
    assert parse_extraction(raw, rubric, TEXT).type == "data_subject_rights"


def test_unknown_type_is_named(rubric):
    with pytest.raises(ExtractionInvalid) as e:
        parse_extraction(_raw(type="tax"), rubric, TEXT)
    assert any("tax" in p for p in e.value.problems)


def test_unknown_signal_is_named(rubric):
    with pytest.raises(ExtractionInvalid) as e:
        parse_extraction(_raw(signals=[{"id": "SIG-FOO", "span": "Procon"}]), rubric, TEXT)
    assert any("SIG-FOO" in p for p in e.value.problems)


def test_span_not_in_text_is_rejected(rubric):
    with pytest.raises(ExtractionInvalid) as e:
        parse_extraction(_raw(type_span="pediu a exclusão"), rubric, TEXT)
    assert any("pediu a exclusão" in p for p in e.value.problems)


def test_span_with_line_break_where_text_has_space_is_accepted(rubric):
    raw = _raw(signals=[{"id": "SIG-REGULATOR", "span": "apagar tudo, senão vai no Procon"}])
    assert parse_extraction(raw, rubric, TEXT).signals[0].span == "apagar tudo, senão vai no Procon"


def test_span_with_different_case_is_rejected(rubric):
    with pytest.raises(ExtractionInvalid):
        parse_extraction(_raw(type_span="Quais dados temos dele"), rubric, TEXT)


def test_duplicated_signal_is_kept_once(rubric):
    hit = {"id": "SIG-REGULATOR", "span": "senão vai no Procon"}
    assert len(parse_extraction(_raw(signals=[hit, hit]), rubric, TEXT).signals) == 1


def test_not_json_is_invalid(rubric):
    with pytest.raises(ExtractionInvalid):
        parse_extraction("não sei responder", rubric, TEXT)


def test_multiple_problems_reported_together(rubric):
    with pytest.raises(ExtractionInvalid) as e:
        parse_extraction(_raw(type="tax", confidence="maybe", type_span=""), rubric, TEXT)
    assert len(e.value.problems) >= 3


def test_secondary_type_and_missing_info_are_read(rubric):
    ex = parse_extraction(_raw(secondary_type="contract", missing_info=["valor"]), rubric, TEXT)
    assert ex.secondary_type == "contract" and ex.missing_info == ("valor",)


def test_span_in_text_collapses_whitespace():
    assert span_in_text("a  b\nc", "x a b c y")
    assert not span_in_text("A b", "a b")


@pytest.mark.parametrize(
    "overrides",
    [
        {"type": ["contract"]},
        {"secondary_type": {"a": 1}},
        {"signals": [{"id": ["SIG-REGULATOR"], "span": "senão vai no Procon"}]},
        {"confidence": ["high"]},
    ],
)
def test_non_string_values_are_invalid_not_a_crash(rubric, overrides):
    with pytest.raises(ExtractionInvalid):
        parse_extraction(_raw(**overrides), rubric, TEXT)
