from pathlib import Path

import pytest
import yaml

from triage.rubric import DEFAULT_RUBRIC, RubricError, load_rubric


def test_default_rubric_loads_eight_types_and_nine_signals():
    r = load_rubric()
    assert set(r.types) == {
        "contract",
        "advisory",
        "litigation",
        "labor",
        "corporate",
        "data_subject_rights",
        "compliance",
        "other",
    }
    assert len(r.signals) == 9


def test_matrix_covers_all_nine_cells_as_in_spec():
    r = load_rubric()
    assert r.matrix[("high", "high")] == "critical"
    assert r.matrix[("medium", "high")] == "high"
    assert r.matrix[("high", "low")] == "normal"
    assert r.matrix[("low", "low")] == "low"
    assert len(r.matrix) == 9


def test_deadlines():
    assert load_rubric().deadlines == {"critical": 0, "high": 2, "normal": 5, "low": 10}


def test_overrides_and_legal_deadline():
    r = load_rubric()
    assert r.signals["SIG-HARD-DEADLINE"].override == "critical"
    assert r.signals["SIG-INCIDENT"].override == "critical"
    assert r.types["data_subject_rights"].legal_deadline_days == 15
    assert r.types["data_subject_rights"].legal_basis == "LGPD, art. 19, II"


def _write_broken(tmp_path: Path, mutate) -> Path:
    data = yaml.safe_load(DEFAULT_RUBRIC.read_text(encoding="utf-8"))
    mutate(data)
    path = tmp_path / "rubric.yaml"
    path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
    return path


def _unknown_level(d):
    d["types"][0]["urgency"] = "urgent"


def _missing_cell(d):
    d["matrix"]["high"].pop("low")


def _duplicate_signal(d):
    d["signals"].append(dict(d["signals"][0]))


def _signal_without_effect(d):
    for key in ("urgency", "risk", "override"):
        d["signals"][0].pop(key, None)


@pytest.mark.parametrize(
    "mutate, needle",
    [
        (_unknown_level, "urgent"),
        (_missing_cell, "matrix"),
        (_duplicate_signal, "SIG-EXEC"),
        (_signal_without_effect, "SIG-EXEC"),
    ],
)
def test_bad_rubric_raises(tmp_path, mutate, needle):
    with pytest.raises(RubricError, match=needle):
        load_rubric(_write_broken(tmp_path, mutate))


def test_public_complaint_counts_as_exposure():
    # Fred, 2026-10-22: an angry customer threatening Reclame Aqui is real exposure, like Procon.
    s = load_rubric().signals["SIG-REGULATOR"]
    assert s.name == "Exposição regulatória, reputacional ou ilícito grave"
    assert "Reclame Aqui" in s.description
    # Fred, 2026-10-22: signs of corruption or fraud are exposure too (Lei 12.846/2013).
    assert "corrupção" in s.description and "fraude" in s.description
    assert s.risk == "high"
