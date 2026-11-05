import pytest

from guardrail.model_pass import ModelSpan
from guardrail.runtimes import CANDIDATES, DEFAULT_MODEL_PASS, GlinerPass, HybridPass, get_model_pass


def test_candidates_resolve_without_loading():
    for name in CANDIDATES:
        model_pass = get_model_pass(name)
        assert model_pass.name == name
    assert DEFAULT_MODEL_PASS in CANDIDATES


def test_unknown_name_rejected():
    with pytest.raises(ValueError):
        get_model_pass("gpt-x")


class _FakeGliner:
    def extract_entities_long(self, text, labels, **kw):
        start = text.index("Construtora Alfa")
        return {"entities": {"empresa ou organização": [
            {"start": start, "end": start + 16, "text": "Construtora Alfa", "confidence": 0.9}]}}


def test_gliner_pass_maps_labels_to_groups():
    model_pass = GlinerPass(model=_FakeGliner())
    assert model_pass("Contrato com a Construtora Alfa.") == [ModelSpan(1, "org", "Construtora Alfa")]


def test_hybrid_takes_orgs_from_gliner_and_the_rest_from_llm():
    class _Llm:
        name = "llm"

        def __call__(self, text):
            return [ModelSpan(1, "org", "ignored"), ModelSpan(3, "clause", "nossa tese")]

    hybrid = HybridPass(GlinerPass(model=_FakeGliner()), _Llm(), name="hybrid")
    assert hybrid("Construtora Alfa: nossa tese") == [ModelSpan(1, "org", "Construtora Alfa"),
                                                       ModelSpan(3, "clause", "nossa tese")]


def test_warm_up_loads_once_without_a_request(monkeypatch):
    from guardrail.runtimes import LlamaPass

    llm = LlamaPass()
    loads = []
    monkeypatch.setattr(llm, "_load", lambda: loads.append(1) or setattr(llm, "_llm", object()))
    hybrid = HybridPass(GlinerPass(model=_FakeGliner()), llm)
    hybrid.warm_up()
    hybrid.warm_up()
    assert loads == [1] and llm.loaded
