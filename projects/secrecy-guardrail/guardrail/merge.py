"""Add-only merge of fixed-rule and model flags, consistent replacement labels, preview and verdict."""

from __future__ import annotations

from collections import defaultdict

from guardrail.flags import Flag, fold
from guardrail.rubric import Rubric

VERDICT_CLEAN = (
    "Não encontramos pontos de atenção nos grupos verificados. "
    "Isso não garante que o texto esteja livre de informação sigilosa."
)
VERDICT_FAILSAFE = (
    "Verificação por IA não concluída: só as regras fixas foram aplicadas. Revise o texto com atenção."
)
VERDICT_INJECTION = "O texto tem possível instrução manipulativa: revise com atenção antes de enviar."
VERDICT_DROPPED = (
    "O modelo apontou trechos que não conseguimos localizar no texto: revise com atenção antes de enviar."
)


def _rank(flag: Flag) -> tuple[bool, bool]:
    # lower wins on an identical span: fixed rules and detector over the model; case number over personal data
    return flag.source == "model", flag.group != 2


def _repeats(m: Flag, f: Flag) -> bool:
    """A model flag that says only what a fixed flag of the same group and kind already says."""
    if (m.group, m.kind) != (f.group, f.kind):
        return False
    if m.kind == "amount":  # "por até R$ 350 mil" vs "R$ 350 mil": one value, one label
        return f.start < m.end and m.start < f.end
    return f.start <= m.start and m.end <= f.end  # a longer model span (the secret around a cue) is kept


def merge(deterministic: list[Flag], model: list[Flag]) -> list[Flag]:
    """Every deterministic flag survives unless an identical span holds a higher-ranked one; model flags only add."""
    fixed = [f for f in deterministic if f.source != "model"]
    model = [m for m in model if not any(_repeats(m, f) for f in fixed)]
    best: dict[tuple[int, int], Flag] = {}
    for flag in (*deterministic, *model):
        key = (flag.start, flag.end)
        if key not in best or _rank(flag) < _rank(best[key]):
            best[key] = flag
    return sorted(best.values(), key=lambda f: (f.start, -f.end))


def _entity_key(flag: Flag) -> tuple[int, str, str]:
    return flag.group, flag.kind, " ".join(fold(flag.text).split())


def assign_labels(flags: list[Flag], rubric: Rubric) -> dict[Flag, str | None]:
    labels: dict[Flag, str | None] = {}
    numbers: dict[tuple[int, str, str], int] = {}
    counters: dict[tuple[int, str], int] = defaultdict(int)
    for flag in sorted(flags, key=lambda f: (f.start, -f.end)):
        template = rubric.groups[flag.group].templates.get(flag.kind)
        if template is None:
            labels[flag] = None
        elif template == "detector":
            labels[flag] = flag.tag
        elif "{n}" in template:
            key = _entity_key(flag)
            if key not in numbers:
                counters[(flag.group, flag.kind)] += 1
                numbers[key] = counters[(flag.group, flag.kind)]
            labels[flag] = template.format(n=numbers[key])
        else:
            labels[flag] = template
    return labels


def preview(text: str, labels: dict[Flag, str | None]) -> str:
    """Replace labeled spans; the outermost labeled span wins, unlabeled spans (clauses, markings) stay."""
    chosen: list[tuple[int, int, str]] = []
    for flag in sorted((f for f, label in labels.items() if label), key=lambda f: (f.start, -f.end)):
        if chosen and flag.start < chosen[-1][1]:
            start, end, label = chosen[-1]
            chosen[-1] = (start, max(end, flag.end), label)  # a crossing span must not leak its tail
            continue
        chosen.append((flag.start, flag.end, labels[flag]))
    out, pos = [], 0
    for start, end, label in chosen:
        out += [text[pos:start], label]
        pos = end
    out.append(text[pos:])
    return "".join(out)


def verdict(flags: list[Flag], model_status: str, injection: bool = False, dropped: int = 0) -> str:
    """Never the clean line when the system knows it may have missed something."""
    n = len(flags)
    found = (
        "Encontramos 1 ponto de atenção. Revise antes de enviar."
        if n == 1
        else f"Encontramos {n} pontos de atenção. Revise antes de enviar."
    )
    warnings = [
        text
        for condition, text in (
            (model_status != "ok", VERDICT_FAILSAFE),
            (dropped > 0, VERDICT_DROPPED),
            (injection, VERDICT_INJECTION),
        )
        if condition
    ]
    if warnings:
        return " ".join([found, *warnings] if n else warnings)
    return found if n else VERDICT_CLEAN
