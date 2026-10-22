import pytest

from triage.checks import amounts, check_values
from triage.extraction import Extraction, SignalHit
from triage.rubric import load_rubric


@pytest.fixture(scope="module")
def rubric():
    return load_rubric()


@pytest.mark.parametrize(
    "text, expected",
    [
        ("contrato de R$ 240 mil por ano", [240_000]),
        ("proposta de 80 mil", [80_000]),
        ("R$ 18.000,00 por ano", [18_000]),
        ("R$ 1,2 milhão", [1_200_000]),
        ("R$ 2 milhões e R$ 300 mil", [2_000_000, 300_000]),
        ("R$ 49 mil", [49_000]),
        ("R$ 75.500", [75_500]),
        ("um acordo grande", []),
        ("multa de 20%", []),
    ],
)
def test_amounts_reads_brazilian_money(text, expected):
    assert amounts(text) == expected


def _ex(*hits):
    return Extraction("contract", "contrato", None, tuple(SignalHit(i, s) for i, s in hits), "high", ())


def test_value_signal_below_threshold_is_dropped(rubric):
    checked, dropped = check_values(_ex(("SIG-VALUE", "R$ 49 mil"), ("SIG-EXEC", "o CEO pediu")), rubric)
    assert [h.id for h in checked.signals] == ["SIG-EXEC"]
    assert dropped == ["SIG-VALUE: valor citado (R$ 49.000) não passa de R$ 50.000"]


def test_value_signal_without_a_number_is_dropped(rubric):
    checked, dropped = check_values(_ex(("SIG-VALUE", "um acordo grande")), rubric)
    assert checked.signals == ()
    assert dropped == ["SIG-VALUE: o trecho citado não traz um valor"]


def test_value_signal_above_threshold_is_kept(rubric):
    ex = _ex(("SIG-VALUE", "contrato de R$ 240 mil por ano"))
    assert check_values(ex, rubric) == (ex, [])


def test_threshold_comes_from_the_rubric(rubric):
    assert rubric.signals["SIG-VALUE"].min_value == 50_000
    assert rubric.signals["SIG-EXEC"].min_value is None


def test_gold_value_labels_pass_the_check(rubric):
    from pathlib import Path

    from triage.cases import load_cases

    for case in load_cases(Path(__file__).resolve().parent.parent / "cases.jsonl", rubric):
        assert check_values(case.gold, rubric)[1] == [], case.id
