import pytest

from triage.extract import FakeExtractor, build_prompt, build_retry_prompt, extraction_schema
from triage.rubric import load_rubric

TEXT = "Preciso revisar o contrato de R$ 120 mil até sexta."


@pytest.fixture(scope="module")
def rubric():
    return load_rubric()


def test_prompt_lists_every_type_and_signal(rubric):
    prompt = build_prompt(TEXT, rubric)
    for type_id in rubric.types:
        assert type_id in prompt
    for signal_id in rubric.signals:
        assert signal_id in prompt


def test_prompt_wraps_request_and_forbids_deciding(rubric):
    prompt = build_prompt(TEXT, rubric)
    assert f"<demanda>\n{TEXT}\n</demanda>" in prompt
    assert "não decida prioridade nem prazo" in prompt
    assert "copie os trechos exatamente como aparecem no texto" in prompt


def test_prompt_keeps_the_full_schema(rubric):
    # Measured 2026-10-21: dropping it saved no time (prefix cache) and cost type accuracy.
    assert '"properties"' in build_prompt(TEXT, rubric)


def test_prompt_prefix_is_identical_across_requests(rubric):
    # llama.cpp reuses the cached prefix, so only the request at the end is processed per call.
    a, b = build_prompt("um pedido", rubric), build_prompt("outro pedido bem diferente", rubric)
    prefix = a.split("<demanda>")[0]
    assert b.startswith(prefix)


def test_retry_prompt_carries_previous_output_and_problems(rubric):
    prompt = build_retry_prompt(TEXT, rubric, '{"type": "tax"}', ["unknown type 'tax'", "missing key 'signals'"])
    assert '{"type": "tax"}' in prompt
    assert "unknown type 'tax'" in prompt and "missing key 'signals'" in prompt
    assert f"<demanda>\n{TEXT}\n</demanda>" in prompt


def test_schema_enums_match_rubric(rubric):
    schema = extraction_schema(rubric)
    props = schema["properties"]
    assert props["type"]["enum"] == list(rubric.types)
    assert props["signals"]["items"]["properties"]["id"]["enum"] == list(rubric.signals)
    assert props["confidence"]["enum"] == ["high", "low"]
    assert set(schema["required"]) == {"type", "type_span", "signals", "confidence"}


def test_fake_extractor_returns_in_order_and_records_prompts():
    fake = FakeExtractor(["a", "b"])
    assert fake("p1") == "a" and fake("p2") == "b"
    assert fake.prompts == ["p1", "p2"]
    assert fake.name == "fake"


def test_fake_extractor_raises_queued_exception():
    fake = FakeExtractor([RuntimeError("model crashed")])
    with pytest.raises(RuntimeError, match="model crashed"):
        fake("p")
