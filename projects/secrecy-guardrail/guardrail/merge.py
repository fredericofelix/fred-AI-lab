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


def _rank(flag: Flag) -> tuple[bool, bool]:
    # lower wins on an identical span: fixed rules and detector over the model; case number over personal data
    return flag.source == "model", flag.group != 2


def merge(deterministic: list[Flag], model: list[Flag]) -> list[Flag]:
    """Every deterministic flag survives unless an identical span holds a higher-ranked one; model flags only add."""
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
            continue  # inside (or crossing) a span already replaced
        chosen.append((flag.start, flag.end, labels[flag]))
    out, pos = [], 0
    for start, end, label in chosen:
        out += [text[pos:start], label]
        pos = end
    out.append(text[pos:])
    return "".join(out)


def verdict(flags: list[Flag], model_status: str) -> str:
    n = len(flags)
    found = (
        "Encontramos 1 ponto de atenção. Revise antes de enviar."
        if n == 1
        else f"Encontramos {n} pontos de atenção. Revise antes de enviar."
    )
    if model_status != "ok":
        return f"{found} {VERDICT_FAILSAFE}" if n else VERDICT_FAILSAFE
    return found if n else VERDICT_CLEAN
