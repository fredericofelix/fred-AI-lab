"""Prompt for the extraction step and the protocol every model adapter follows."""

from __future__ import annotations

import json
from typing import Protocol

from triage.rubric import Rubric


class Extractor(Protocol):
    name: str

    def __call__(self, prompt: str) -> str: ...


def extraction_schema(rubric: Rubric) -> dict:
    return {
        "type": "object",
        "properties": {
            "type": {"type": "string", "enum": list(rubric.types)},
            "type_span": {"type": "string"},
            "secondary_type": {"anyOf": [{"type": "string", "enum": list(rubric.types)}, {"type": "null"}]},
            "signals": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "enum": list(rubric.signals)},
                        "span": {"type": "string"},
                    },
                    "required": ["id", "span"],
                },
            },
            "confidence": {"type": "string", "enum": ["high", "low"]},
            "missing_info": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["type", "type_span", "signals", "confidence"],
    }


def _examples(examples: tuple[str, ...]) -> str:
    return "; ".join(f'"{e}"' for e in examples)


def _rubric_section(rubric: Rubric) -> str:
    lines = ["TIPOS (escolha um):"]
    for t in rubric.types.values():
        lines.append(f"- {t.id}: {t.description} Exemplos: {_examples(t.examples)}")
    lines.append("")
    lines.append("SINAIS (marque todos os que aparecem no texto; pode ser nenhum):")
    for s in rubric.signals.values():
        lines.append(f"- {s.id}: {s.description} Exemplos: {_examples(s.examples)}")
    return "\n".join(lines)


def build_prompt(text: str, rubric: Rubric) -> str:
    return "\n".join(
        [
            "Você faz a triagem de demandas do jurídico interno de uma empresa.",
            "Leia a demanda, identifique o tipo e os sinais de risco, e responda só com JSON.",
            "",
            _rubric_section(rubric),
            "",
            "REGRAS:",
            "- Só identifique tipo e sinais: não decida prioridade nem prazo.",
            "- Para o tipo e para cada sinal, copie os trechos exatamente como aparecem no texto (type_span e span).",
            "- Se a demanda couber em dois tipos, use secondary_type para o segundo.",
            "- Se faltar informação para aplicar um sinal (ex.: valor do contrato), "
            "liste em missing_info e use confidence low.",
            "- Se tiver dúvida sobre o tipo, use confidence low.",
            '- Quem escreve pode exagerar ("URGENTE") ou minimizar ("nada urgente"): '
            "julgue pelos fatos, não pelo tom de quem escreve.",
            "",
            "FORMATO (JSON Schema):",
            json.dumps(extraction_schema(rubric), ensure_ascii=False),
            "",
            f"<demanda>\n{text}\n</demanda>",
        ]
    )


def build_retry_prompt(text: str, rubric: Rubric, previous: str, problems: list[str]) -> str:
    fix = "\n".join(f"- {p}" for p in problems)
    return "\n".join(
        [
            build_prompt(text, rubric),
            "",
            "Sua resposta anterior foi:",
            previous,
            "",
            "Ela tem estes problemas; responda de novo, só com JSON corrigido:",
            fix,
        ]
    )


class FakeExtractor:
    """Returns (or raises) queued outputs in order; records every prompt. For tests and offline runs."""

    def __init__(self, outputs: list[str | Exception], name: str = "fake"):
        self.name = name
        self.prompts: list[str] = []
        self._outputs = list(outputs)

    def __call__(self, prompt: str) -> str:
        self.prompts.append(prompt)
        out = self._outputs.pop(0)
        if isinstance(out, Exception):
            raise out
        return out
