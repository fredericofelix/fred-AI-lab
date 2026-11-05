from guardrail.flags import Flag
from guardrail.merge import (
    VERDICT_CLEAN,
    VERDICT_FAILSAFE,
    assign_labels,
    merge,
    preview,
    verdict,
)
from guardrail.rubric import load_rubric

RUBRIC = load_rubric()


def _at(text, sub, group, kind, source="model", nth=0, tag=None):
    start = -1
    for _ in range(nth + 1):
        start = text.index(sub, start + 1)
    return Flag(group, kind, start, start + len(sub), sub, source, tag=tag)


def test_model_cannot_remove_deterministic():
    text = "CONFIDENCIAL: acordo até R$ 200 mil"
    det = [_at(text, "CONFIDENCIAL", 4, "marking", "lexicon"), _at(text, "R$ 200 mil", 3, "amount", "regex")]
    model = [_at(text, "R$ 200 mil", 5, "third_party")]
    merged = merge(det, model)
    assert all(f in merged for f in det)
    assert len(merged) == 2


def test_cnj_wins_over_personal_on_same_span():
    text = "autos 00012343420258130024"
    cnj = _at(text, "00012343420258130024", 2, "cnj", "regex")
    pis = _at(text, "00012343420258130024", 6, "personal", "detector", tag="[PIS]")
    assert merge([pis, cnj], []) == [cnj]


def test_same_entity_same_label():
    text = "A Construtora Alfa e a CONSTRUTORA ALFA contra a Beta Ltda."
    flags = [
        _at(text, "Construtora Alfa", 1, "org"),
        _at(text, "CONSTRUTORA ALFA", 1, "org"),
        _at(text, "Beta Ltda", 1, "org"),
    ]
    labels = assign_labels(merge([], flags), RUBRIC)
    assert [labels[f] for f in flags] == ["[EMPRESA 1]", "[EMPRESA 1]", "[EMPRESA 2]"]
    assert preview(text, labels) == "A [EMPRESA 1] e a [EMPRESA 1] contra a [EMPRESA 2]."


def test_overlap_person_inside_org():
    text = "Contrato da Construtora Alfa Souza Ltda com o banco."
    person = _at(text, "Alfa Souza", 1, "person", "detector")
    org = _at(text, "Construtora Alfa Souza Ltda", 1, "org")
    merged = merge([person], [org])
    assert person in merged and org in merged
    out = preview(text, assign_labels(merged, RUBRIC))
    assert out == "Contrato da [EMPRESA 1] com o banco."


def test_clause_and_marking_not_replaced_but_names_inside_are():
    text = "Confidencial. Vamos alegar que Ana Lima assinou sem poderes."
    marking = _at(text, "Confidencial", 4, "marking", "lexicon")
    clause = _at(text, "Vamos alegar que Ana Lima assinou sem poderes", 3, "clause")
    person = _at(text, "Ana Lima", 1, "person", "detector")
    labels = assign_labels(merge([marking, person], [clause]), RUBRIC)
    assert labels[marking] is None and labels[clause] is None
    assert preview(text, labels) == "Confidencial. Vamos alegar que [PESSOA 1] assinou sem poderes."


def test_personal_uses_detector_tag():
    text = "CPF 123.456.789-09"
    cpf = _at(text, "123.456.789-09", 6, "personal", "detector", tag="[CPF]")
    assert assign_labels([cpf], RUBRIC)[cpf] == "[CPF]"


def test_verdict_copy():
    one = [Flag(4, "marking", 0, 1, "x", "lexicon")]
    assert verdict(one, "ok") == "Encontramos 1 ponto de atenção. Revise antes de enviar."
    assert verdict(one * 3, "ok") == "Encontramos 3 pontos de atenção. Revise antes de enviar."
    assert verdict([], "ok") == VERDICT_CLEAN
    assert VERDICT_CLEAN == (
        "Não encontramos pontos de atenção nos grupos verificados. "
        "Isso não garante que o texto esteja livre de informação sigilosa."
    )
    assert verdict(one, "timeout").endswith(VERDICT_FAILSAFE)


def test_verdict_never_clean_on_timeout():
    for status in ("timeout", "error"):
        out = verdict([], status)
        assert "Não encontramos" not in out
        assert out == VERDICT_FAILSAFE
