from privacyseed_lgpd.entity import Entity, Result

from guardrail.personal import personal_flags

TEXT = "Fale com Maria Souza, CPF 123.456.789-09, da empresa CNPJ 11.222.333/0001-81."


def _entity(label: str, text: str, category: str = "personal") -> Entity:
    start = TEXT.index(text)
    return Entity(label, text, start, start + len(text), 0.9, "fake", category)


class FakeDetector:
    def __init__(self, result: Result):
        self.result = result
        self.calls = 0

    def analyze(self, text: str) -> Result:
        self.calls += 1
        return self.result


def _run(entities=(), flagged=(), warnings=()):
    result = Result(anonymized="", entities=tuple(entities), flagged=tuple(flagged), warnings=tuple(warnings))
    return personal_flags(TEXT, FakeDetector(result))


def test_person_name_is_group_1():
    [flag], _ = _run(entities=[_entity("person_name", "Maria Souza")])
    assert (flag.group, flag.kind, flag.text, flag.source) == (1, "person", "Maria Souza", "detector")


def test_cpf_is_group_6_with_tag():
    [flag], _ = _run(entities=[_entity("cpf", "123.456.789-09")])
    assert (flag.group, flag.kind, flag.tag) == (6, "personal", "[CPF]")


def test_cnpj_flagged_entity_is_group_6():
    [flag], _ = _run(flagged=[_entity("cnpj", "11.222.333/0001-81")])
    assert (flag.group, flag.tag) == (6, "[CNPJ]")


def test_warnings_passed_through():
    _, warnings = _run(warnings=["sem [ml]"])
    assert warnings == ["sem [ml]"]
