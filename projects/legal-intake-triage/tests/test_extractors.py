import pytest

from triage.extractors import CANDIDATES, DEFAULT_MODEL, LlamaCppExtractor, get_extractor


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
