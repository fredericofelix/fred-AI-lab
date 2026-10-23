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


def test_concurrent_calls_load_once_and_never_overlap(monkeypatch):
    # The Space warms the model up in a thread while visitors may already submit requests.
    import threading
    import time

    ex = get_extractor(DEFAULT_MODEL)
    loads, active, overlaps = [], [0], []

    class FakeLlama:
        def create_chat_completion(self, **_):
            active[0] += 1
            if active[0] > 1:
                overlaps.append(True)
            time.sleep(0.05)
            active[0] -= 1
            yield {"choices": [{"delta": {"content": "{}"}}]}

    def fake_load():
        loads.append(1)
        time.sleep(0.05)
        ex._llm = FakeLlama()

    monkeypatch.setattr(ex, "_load", fake_load)
    threads = [threading.Thread(target=ex, args=("p",)) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len(loads) == 1
    assert not overlaps


def test_default_model_is_a_candidate():
    assert DEFAULT_MODEL in CANDIDATES


def test_unknown_name_lists_known_ones():
    with pytest.raises(KeyError, match="qwen3-4b"):
        get_extractor("gpt-9")


def test_loaded_flag_follows_model_state():
    ex = get_extractor(DEFAULT_MODEL)
    assert ex.loaded is False
    ex._llm = object()
    assert ex.loaded is True


def test_generation_stops_at_the_time_limit(monkeypatch):
    import time

    ex = get_extractor(DEFAULT_MODEL)
    ex._timeout_s = 0.2

    class SlowLlama:
        def create_chat_completion(self, **kwargs):
            assert kwargs["stream"] is True
            for _ in range(100):
                time.sleep(0.05)
                yield {"choices": [{"delta": {"content": "x"}}]}

    ex._llm = SlowLlama()
    start = time.perf_counter()
    with pytest.raises(TimeoutError):
        ex("p")
    assert time.perf_counter() - start < 1.0


def test_streamed_chunks_are_joined():
    ex = get_extractor(DEFAULT_MODEL)

    class FastLlama:
        def create_chat_completion(self, **_):
            yield {"choices": [{"delta": {"role": "assistant"}}]}
            yield {"choices": [{"delta": {"content": '{"a"'}}]}
            yield {"choices": [{"delta": {"content": ": 1}"}}]}

    ex._llm = FastLlama()
    assert ex("p") == '{"a": 1}'


def test_default_model_download_is_pinned_to_a_revision(monkeypatch):
    import sys
    import types

    import triage.extractors as mod

    calls = {}

    def fake_download(repo_id, filename, revision=None):
        calls.update(repo_id=repo_id, filename=filename, revision=revision)
        return "/tmp/model.gguf"

    fake_llama = types.ModuleType("llama_cpp")
    fake_llama.Llama = lambda model_path, **kw: calls.update(model_path=model_path) or object()
    monkeypatch.setitem(sys.modules, "llama_cpp", fake_llama)
    monkeypatch.setattr(mod, "hf_hub_download", fake_download)
    ex = get_extractor(DEFAULT_MODEL)
    ex._load()
    assert calls["revision"] == "a06e946bb6b655725eafa393f4a9745d460374c9"
    assert calls["model_path"] == "/tmp/model.gguf"


def test_space_requirements_are_pinned():
    from pathlib import Path

    reqs = (Path(__file__).resolve().parent.parent / "requirements-space.txt").read_text()
    assert "llama-cpp-python==0.3.36" in reqs


def test_waiting_for_the_lock_counts_against_the_time_limit():
    import time

    ex = get_extractor(DEFAULT_MODEL)
    ex._timeout_s = 0.2
    ex._lock.acquire()  # a stuck warm-up or request holds the model
    try:
        start = time.perf_counter()
        with pytest.raises(TimeoutError):
            ex("p")
        assert time.perf_counter() - start < 1.0
    finally:
        ex._lock.release()


def test_model_weights_are_kept_in_ram(monkeypatch):
    import sys
    import types

    import triage.extractors as mod

    kwargs = {}
    fake_llama = types.ModuleType("llama_cpp")
    fake_llama.Llama = lambda **kw: kwargs.update(kw) or object()
    monkeypatch.setitem(sys.modules, "llama_cpp", fake_llama)
    monkeypatch.setattr(mod, "hf_hub_download", lambda *a, **k: "/tmp/m.gguf")
    get_extractor(DEFAULT_MODEL)._load()
    assert kwargs["use_mmap"] is False  # idle hosts evict mmap'd pages; reload on first request was the hang suspect


def test_warm_up_loads_and_primes_prefix_with_one_token():
    ex = get_extractor(DEFAULT_MODEL)
    seen = {}

    class FakeLlama:
        def create_chat_completion(self, **kw):
            seen.update(kw)
            return {"choices": [{"message": {"content": ""}}]}

    ex._load = lambda: setattr(ex, "_llm", FakeLlama())
    ex.warm_up("prefixo da rubrica")
    assert seen["max_tokens"] == 1 and "response_format" not in seen
    assert seen["messages"][-1]["content"] == "prefixo da rubrica"
    assert ex.ready


def test_watchdog_exits_when_a_call_runs_too_long(monkeypatch):
    import time

    import triage.extractors as mod

    exits = []
    monkeypatch.setattr(mod.os, "_exit", lambda code: exits.append(code))
    ex = get_extractor(DEFAULT_MODEL)
    ex._busy_since = time.monotonic() - 1000
    ex.check_watchdog(limit_s=300)
    assert exits == [1]
    ex._busy_since = None
    ex.check_watchdog(limit_s=300)
    assert exits == [1]
