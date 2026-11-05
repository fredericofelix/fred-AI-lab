"""Text the model reads: case numbers and regex identifiers replaced by placeholders, names kept."""

from __future__ import annotations

from dataclasses import dataclass, field

from guardrail.flags import Flag

# Detector tags found by context or model, not by a fixed pattern: kept raw for the model.
_KEEP_TAGS = frozenset({"[NOME]", "[ENDERECO]", "[DADO_SENSIVEL]"})
CNJ_PLACEHOLDER = "[PROCESSO]"


@dataclass(frozen=True)
class Masked:
    text: str
    # (masked_start, masked_end, original_start) for each run of text copied unchanged
    _runs: tuple[tuple[int, int, int], ...] = field(default=(), repr=False)

    def to_original(self, start: int, end: int) -> tuple[int, int] | None:
        """Map a span of the masked text back to the original; None if it touches a placeholder."""
        for m_start, m_end, o_start in self._runs:
            if m_start <= start and end <= m_end:
                return o_start + (start - m_start), o_start + (end - m_start)
        return None


def _placeholder(flag: Flag) -> str | None:
    if flag.group == 2:
        return CNJ_PLACEHOLDER
    if flag.group == 6 and flag.source == "detector" and flag.tag and flag.tag not in _KEEP_TAGS:
        return flag.tag
    return None


def mask_for_model(text: str, flags: list[Flag]) -> Masked:
    targets = sorted(((f.start, f.end, p) for f in flags if (p := _placeholder(f))), key=lambda t: (t[0], -t[1]))
    out: list[str] = []
    runs: list[tuple[int, int, int]] = []
    pos = 0  # position in the original text
    length = 0  # length of the masked text so far
    for start, end, placeholder in targets:
        if start < pos:
            continue  # overlaps a span already replaced
        out.append(text[pos:start])
        runs.append((length, length + start - pos, pos))
        length += start - pos
        out.append(placeholder)
        length += len(placeholder)
        pos = end
    out.append(text[pos:])
    runs.append((length, length + len(text) - pos, pos))
    return Masked("".join(out), tuple(runs))
