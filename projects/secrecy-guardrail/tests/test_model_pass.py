import pytest

from guardrail.flags import Flag
from guardrail.masking import mask_for_model
from guardrail.model_pass import FakeModelPass, ModelSpan, build_prompt, locate, parse_llm_output
from guardrail.rubric import load_rubric

TEXT = "Contra a Construtora Alfa, nossa tese é a prescrição.\nPodemos  oferecer o parcelamento."


def test_parse_fenced_json():
    raw = 'Claro:\n```json\n{"flags": [{"group": 1, "kind": "org", "span": "Construtora Alfa"}]}\n```'
    assert parse_llm_output(raw) == [ModelSpan(1, "org", "Construtora Alfa")]


def test_parse_garbage_raises():
    with pytest.raises(ValueError):
        parse_llm_output("não sei")
    with pytest.raises(ValueError):
        parse_llm_output('{"flags": [{"group": "x"}]}')


def test_locate_drops_non_verbatim():
    flags, dropped = locate([ModelSpan(1, "org", "Construtora Beta")], mask_for_model(TEXT, []), TEXT)
    assert (flags, dropped) == ([], 1)


def test_locate_whitespace_collapse_ok():
    [flag], dropped = locate([ModelSpan(3, "clause", "Podemos oferecer")], mask_for_model(TEXT, []), TEXT)
    assert dropped == 0
    assert flag == Flag(3, "clause", TEXT.index("Podemos"), TEXT.index("oferecer") + 8, "Podemos  oferecer", "model")


def test_locate_rejects_group_2():
    flags, dropped = locate([ModelSpan(2, "cnj", "Construtora Alfa")], mask_for_model(TEXT, []), TEXT)
    assert (flags, dropped) == ([], 1)


def test_locate_maps_through_mask():
    cnj = "0001234-34.2025.8.13.0024"
    text = f"Processo {cnj} contra a Construtora Alfa."
    masked = mask_for_model(text, [Flag(2, "cnj", 9, 9 + len(cnj), cnj, "regex")])
    [flag], _ = locate([ModelSpan(1, "org", "Construtora Alfa")], masked, text)
    assert text[flag.start : flag.end] == "Construtora Alfa"


def test_prompt_delimits_text():
    prompt = build_prompt(TEXT, load_rubric())
    assert f"<texto>\n{TEXT}\n</texto>" in prompt


def test_fake_model_pass_replays_and_raises():
    fake = FakeModelPass([[ModelSpan(1, "org", "X")], TimeoutError()])
    assert fake("a") == [ModelSpan(1, "org", "X")]
    with pytest.raises(TimeoutError):
        fake("b")
    assert fake.inputs == ["a", "b"]


def test_locate_matches_other_case_repeats():
    text = "A Construtora Alfa ligou. A CONSTRUTORA ALFA respondeu."
    flags, dropped = locate([ModelSpan(1, "org", "Construtora Alfa")], mask_for_model(text, []), text)
    assert dropped == 0 and [f.text for f in flags] == ["Construtora Alfa", "CONSTRUTORA ALFA"]
