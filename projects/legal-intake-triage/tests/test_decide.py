import pytest

from triage.decide import decide, fallback
from triage.extraction import Extraction, SignalHit
from triage.rubric import load_rubric


@pytest.fixture(scope="module")
def rubric():
    return load_rubric()


def _ex(type_, *signals, confidence="high", missing=(), secondary=None):
    return Extraction(
        type=type_,
        type_span="trecho",
        secondary_type=secondary,
        signals=tuple(SignalHit(s, f"trecho {s}") for s in signals),
        confidence=confidence,
        missing_info=tuple(missing),
    )


def test_showcase_dsar_with_regulator_threat_is_high_two_days_plus_legal_15(rubric):
    d = decide(
        Extraction(
            "data_subject_rights",
            "quais dados temos dele e apagar tudo",
            None,
            (SignalHit("SIG-REGULATOR", "senão vai no Procon"),),
            "high",
            (),
        ),
        rubric,
    )
    assert (d.urgency, d.risk, d.priority) == ("medium", "high", "high")
    assert d.internal_deadline_days == 2 and d.legal_deadline_days == 15
    assert d.legal_basis == "LGPD, art. 19, II"
    assert d.review_reasons == ("high_risk",)


def test_hard_deadline_overrides_matrix_to_critical_same_day(rubric):
    d = decide(_ex("advisory", "SIG-HARD-DEADLINE"), rubric)
    assert d.priority == "critical"
    assert d.internal_deadline_days == 0
    assert d.review_reasons == ("override",)
    assert d.review_by_design and not d.review_by_uncertainty


def test_no_signals_uses_type_baseline(rubric):
    d = decide(_ex("contract"), rubric)
    assert (d.urgency, d.risk, d.priority, d.internal_deadline_days) == ("low", "medium", "low", 10)
    assert d.review_reasons == ()
    assert not d.human_review


def test_exec_and_value_make_critical(rubric):
    d = decide(_ex("contract", "SIG-EXEC", "SIG-VALUE"), rubric)
    assert (d.urgency, d.risk, d.priority) == ("high", "high", "critical")


def test_uncertainty_reasons(rubric):
    d = decide(_ex("other", confidence="low", missing=["valor do contrato"], secondary="contract"), rubric)
    assert d.review_reasons == ("low_confidence", "missing_info", "type_other", "two_types")
    assert d.review_by_uncertainty and not d.review_by_design
    assert d.human_review


def test_same_secondary_type_is_not_two_types(rubric):
    assert decide(_ex("contract", secondary="contract"), rubric).review_reasons == ()


def test_fired_effects_text_in_portuguese(rubric):
    d = decide(
        _ex("data_subject_rights", "SIG-REGULATOR", "SIG-EXEC", "SIG-INCIDENT"),
        rubric,
    )
    assert [(f.rule_id, f.effect) for f in d.fired] == [
        ("data_subject_rights", "tipo = LGPD / direitos do titular; prazo legal 15 dias"),
        ("SIG-REGULATOR", "risco → alto"),
        ("SIG-EXEC", "urgência → alta"),
        ("SIG-INCIDENT", "prioridade → crítica (regra de exceção)"),
    ]
    assert d.fired[1].span == "trecho SIG-REGULATOR"
    assert decide(_ex("contract"), rubric).fired[0].effect == "tipo = Contratos"


def test_fallback(rubric):
    d = fallback(rubric)
    assert d.type == "other"
    assert d.fired == ()
    assert d.review_reasons == ("invalid_output",)
    assert d.human_review and d.review_by_uncertainty
