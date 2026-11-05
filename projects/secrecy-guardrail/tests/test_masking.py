from guardrail.flags import Flag
from guardrail.masking import mask_for_model

CNJ = "0001234-34.2025.8.13.0024"
TEXT = f"Processo {CNJ}, contato ana@exemplo.com.br, contra a Construtora Alfa e Ana Lima."


def _flag(group, kind, text, source, tag=None):
    start = TEXT.index(text)
    return Flag(group, kind, start, start + len(text), text, source, tag=tag)


FLAGS = [
    _flag(2, "cnj", CNJ, "regex"),
    _flag(6, "personal", "ana@exemplo.com.br", "detector", "[EMAIL]"),
    _flag(1, "person", "Ana Lima", "detector"),
]


def test_roundtrip_offsets():
    masked = mask_for_model(TEXT, FLAGS)
    assert CNJ not in masked.text and "ana@exemplo" not in masked.text
    start = masked.text.index("Construtora Alfa")
    assert masked.to_original(start, start + len("Construtora Alfa")) == (
        TEXT.index("Construtora Alfa"),
        TEXT.index("Construtora Alfa") + len("Construtora Alfa"),
    )


def test_names_not_masked():
    assert "Ana Lima" in mask_for_model(TEXT, FLAGS).text


def test_span_over_placeholder_is_none():
    masked = mask_for_model(TEXT, FLAGS)
    start = masked.text.index("[PROCESSO]")
    assert masked.to_original(start, start + 12) is None
