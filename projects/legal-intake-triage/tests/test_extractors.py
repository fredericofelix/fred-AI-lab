import pytest

from triage.extractors import CANDIDATES, DEFAULT_MODEL, LlamaCppExtractor, default_threads, get_extractor


def test_threads_from_env_win(tmp_path, monkeypatch):
    monkeypatch.setenv("TRIAGE_THREADS", "3")
    assert default_threads(cgroup_cpu_max=tmp_path / "missing") == 3


def test_threads_from_cgroup_quota(tmp_path, monkeypatch):
    # A container with 2 vCPUs on a big host: llama.cpp would otherwise use every host CPU.
    monkeypatch.delenv("TRIAGE_THREADS", raising=False)
    cpu_max = tmp_path / "cpu.max"
    cpu_max.write_text("200000 100000\n")
    assert default_threads(cgroup_cpu_max=cpu_max) == 2


def test_threads_unlimited_cgroup_falls_back_to_cpu_count(tmp_path, monkeypatch):
    monkeypatch.delenv("TRIAGE_THREADS", raising=False)
    cpu_max = tmp_path / "cpu.max"
    cpu_max.write_text("max 100000\n")
    assert default_threads(cgroup_cpu_max=cpu_max) >= 1


def test_every_candidate_resolves_without_loading_the_model():
    for key in CANDIDATES:
        ex = get_extractor(key)
        assert isinstance(ex, LlamaCppExtractor)
        assert ex.name == key
        assert ex._llm is None  # weights load on first call, not on lookup


def test_default_model_is_a_candidate():
    assert DEFAULT_MODEL in CANDIDATES


def test_unknown_name_lists_known_ones():
    with pytest.raises(KeyError, match="qwen3-4b"):
        get_extractor("gpt-9")
