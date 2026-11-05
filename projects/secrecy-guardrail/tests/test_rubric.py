from pathlib import Path

import pytest

from guardrail.rubric import load_rubric


def test_six_groups_with_anchors():
    rubric = load_rubric()
    assert set(rubric.groups) == {1, 2, 3, 4, 5, 6}
    assert all(g.anchor.strip() for g in rubric.groups.values())


def test_only_group_3_experimental():
    rubric = load_rubric()
    assert [g.id for g in rubric.groups.values() if g.experimental] == [3]


def test_templates_kinds():
    rubric = load_rubric()
    assert rubric.groups[3].templates["clause"] is None
    assert rubric.groups[4].templates["marking"] is None
    assert rubric.groups[1].templates["person"] == "[PESSOA {n}]"


def test_bad_rubric_rejected(tmp_path: Path):
    text = load_rubric.__globals__["RUBRIC_PATH"].read_text(encoding="utf-8")
    import yaml

    data = yaml.safe_load(text)
    data["groups"] = [g for g in data["groups"] if g["id"] != 2]
    bad = tmp_path / "rubric.yaml"
    bad.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
    with pytest.raises(ValueError):
        load_rubric(bad)
