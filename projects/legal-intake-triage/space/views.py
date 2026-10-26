"""Pure helpers for the Space UI (no gradio import, so CI tests them)."""

from __future__ import annotations

import base64
import html
import json
from pathlib import Path

from triage.decide import PRIORITY_PT, RISK_PT, URGENCY_PT, Decision, decide
from triage.pipeline import StageEvent, TriageRun
from triage.rubric import Rubric
from triage.sanitize import TAG_PT, Sanitized, sanitize
from triage.validate import parse_extraction

ROOT = Path(__file__).resolve().parent
ROBOT_SVG = next(
    p for p in (ROOT / "assets" / "icon-robot.svg", ROOT.parent / "assets" / "icon-robot.svg") if p.exists()
)

DETECTOR_SPACE = "https://huggingface.co/spaces/fred-ai-lab/detector-lgpd"
DETECTOR_REPO = "https://github.com/fredericofelix/privacyseed-lgpd"

NOTICE = (
    "⚠️ **Não cole dados reais** de clientes, colaboradores ou processos, nem dados sensíveis (saúde, sindicato, "
    "religião e outros). Antes da triagem, o Detector LGPD "
    "da Privacy Seed mascara CPF, CNPJ, PIS, CNH, título de eleitor, cartão, e-mail, telefone, CEP e data de "
    "nascimento. **Nomes e endereços não são mascarados nesta versão.** O texto é processado só em memória, "
    "no Hugging Face, e não é guardado."
)
DISCLAIMER = (
    "**Triagem automatizada de demandas jurídicas.** Demonstração com dados sintéticos: um modelo de IA aberto "
    "identifica o tipo e os sinais da demanda, e regras explícitas (a rubrica) definem prioridade e prazo. "
    "A ferramenta pode errar; casos de risco alto ou incertos vão para revisão humana. "
    "Esta ferramenta não constitui aconselhamento jurídico."
)
CTA = (
    "Quer aplicar ao seu jurídico, com a sua régua e os seus canais (e-mail, Slack, Teams)? "
    "[Fale com a Lex Seed](https://www.lexseed.com.br/?utm_source=hf-space&utm_medium=space"
    "&utm_campaign=triagem-juridica)."
)
EMPTY_INPUT = "Cole uma demanda ou escolha um exemplo."
LOAD_NOTICE = (
    "⏱️ A primeira triagem depois de um tempo sem uso pode levar até ~3 minutos, porque o modelo é carregado. "
    "As seguintes levam cerca de 30 segundos. Os exemplos prontos respondem na hora."
)
LOADING_LABEL = "Carregando o modelo de IA (primeira vez, até ~3 min)"
QUEUE_FULL = "Muitas pessoas testando agora. Espere um minuto e tente de novo, ou use um dos exemplos prontos."

# Lex Seed brand tokens (lex-seed-site/docs/brand.md).
BRAND = {
    "amber": "#FFC857",
    "ochre": "#D9A23A",
    "graphite": "#48535B",
    "bg_dark": "#1E2428",
    "fg_dark": "#F4F6F5",
    "on_accent": "#2A1E00",
    "muted": "#A9B4B0",
    "line": "#34404A",
}
FONTS_HEAD = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&family=Nunito:wght@800;900'
    '&display=swap" rel="stylesheet">'
)
SANITIZE_LIMIT = "Não detecta nomes nem endereços nesta versão."

REASON_PT = {
    "high_risk": "risco alto",
    "override": "regra de exceção",
    "invalid_output": "saída do modelo inválida",
    "timeout": "tempo esgotado",
    "suspected_injection": "possível tentativa de manipulação do texto",
    "low_confidence": "baixa confiança",
    "missing_info": "falta informação",
    "type_other": "tipo não identificado",
    "two_types": "dois tipos possíveis",
}

STEPS = [
    ("sanitize", "Saneamento — Detector LGPD by Privacy Seed"),
    ("extract", "Lendo a demanda e procurando sinais da rubrica"),
    ("check", "Conferindo regras e trechos citados"),
    ("decide", "Calculando prioridade e prazo"),
]

CSS = """
body, .gradio-container { font-family: 'Inter', sans-serif }
.gradio-container h1, .gradio-container h2, .gradio-container h3 { font-family: 'Nunito', sans-serif; font-weight: 900 }
.gradio-container h1 { color: #F4F6F5 }
.tab-wrapper button.selected, button[role="tab"][aria-selected="true"] { color: #FFC857; border-color: #FFC857 }
.load-notice { color: #A9B4B0; font-size: 14px }
@keyframes bob { 0%,100% { transform: translateY(0) rotate(0) } 25% { transform: translateY(-6px) rotate(-4deg) }
  75% { transform: translateY(-6px) rotate(4deg) } }
@keyframes ring { 0% { box-shadow: 0 0 0 0 rgba(255,200,87,.7) } 100% { box-shadow: 0 0 0 22px rgba(255,200,87,0) } }
.triage-steps { display:flex; gap:18px; align-items:center; padding:16px; border-radius:12px; background:#1E2428;
  border:1px solid #34404A; color:#F4F6F5 }
.triage-steps .robot { width:72px; height:72px; border-radius:50% }
.triage-steps .robot.thinking { animation: bob 1.6s ease-in-out infinite, ring 1.6s ease-out infinite }
.triage-steps .step { margin:4px 0; font-size:14px }
.triage-steps .done { color:#F4F6F5 } .triage-steps .now { color:#FFC857 }
.triage-steps .next { color:#A9B4B0; opacity:.7 }
.triage-card { border-radius:10px; padding:12px; margin:8px 0; border:1px solid #34404A }
/* Privacy Seed's own step: co-branded block, the one place its green appears. */
.triage-card.detector { border:2px solid #2e7d32 }
.triage-cards { display:flex; flex-wrap:wrap; gap:10px }
.triage-cards div { border:1px solid #48535B; border-radius:8px; padding:8px 12px }
.triage-cards .priority { border:2px solid #FFC857 }
"""


def _robot_src() -> str:
    return "data:image/svg+xml;base64," + base64.b64encode(ROBOT_SVG.read_bytes()).decode()


def validate_input(text: str) -> str | None:
    return EMPTY_INPUT if not (text or "").strip() else None


def steps_html(events: list[StageEvent], running: bool, model_loaded: bool = True) -> str:
    done = {e.stage: e.detail for e in events if e.done}
    started = {e.stage for e in events}
    rows = []
    for stage, label in STEPS:
        if stage in done:
            detail = f" ({html.escape(done[stage])})" if done[stage] else ""
            rows.append(f'<div class="step done">✓ {label}{detail}</div>')
        elif stage in started:
            now = LOADING_LABEL if stage == "extract" and not model_loaded else label
            rows.append(f'<div class="step now">● {now}…</div>')
        else:
            rows.append(f'<div class="step next">○ {label}</div>')
    robot_class = "robot thinking" if running else "robot"
    return (
        f'<div class="triage-steps"><img class="{robot_class}" src="{_robot_src()}" alt="Robô da Lex Seed">'
        f"<div>{''.join(rows)}</div></div>"
    )


def _counts(counts: dict[str, int]) -> str:
    return ", ".join(f"{n} {TAG_PT.get(tag, tag)}" for tag, n in counts.items())


def sanitize_html(s: Sanitized) -> str:
    masked = _counts(s.masked) or "nenhum identificador encontrado"
    flagged = f"<br>CNPJ e similares ficam no texto, sinalizados: {_counts(s.flagged)}" if s.flagged else ""
    return (
        '<div class="triage-card detector">'
        "<b>Passo 1 · Saneamento — Detector LGPD by Privacy Seed 🛡️</b><br>"
        f"Antes de a IA ler a demanda, mascaramos: <b>{masked}</b>{flagged}<br>"
        f"Texto enviado ao modelo:<pre style='white-space:pre-wrap'>{html.escape(s.text)}</pre>"
        f"<small>{SANITIZE_LIMIT}</small><br>"
        f'<a href="{DETECTOR_SPACE}" target="_blank">Conheça o Detector LGPD</a> · '
        f'<a href="{DETECTOR_REPO}" target="_blank">código aberto</a>'
        "</div>"
    )


def _deadline(days: int) -> str:
    return "mesmo dia" if days == 0 else f"{days} dias úteis"


def result_html(d: Decision, rubric: Rubric) -> str:
    t = rubric.types[d.type]
    cards = [
        f"<div><b>Tipo</b><br>{html.escape(t.name)}</div>",
        f"<div><b>Urgência</b><br>{URGENCY_PT[d.urgency]}</div>",
        f"<div><b>Risco</b><br>{RISK_PT[d.risk]}</div>",
        f'<div class="priority"><b>Prioridade</b><br>{PRIORITY_PT[d.priority].capitalize()} · '
        f"{_deadline(d.internal_deadline_days)}</div>",
    ]
    if d.legal_deadline_days is not None:
        cards.append(
            f"<div><b>Prazo legal</b><br>{d.legal_deadline_days} dias ({html.escape(d.legal_basis or '')})</div>"
        )
    if d.human_review:
        reasons = ", ".join(REASON_PT[r] for r in d.review_reasons)
        review = f"👤 <b>Revisão humana: sim</b> ({reasons})"
    else:
        review = "👤 Revisão humana: não necessária pela rubrica"
    no_model_result = {"invalid_output", "timeout"} & set(d.review_reasons)
    if no_model_result and "override" not in d.review_reasons:
        cards = ["<div><b>Resultado</b><br>Sem triagem automática</div>"]
    return (
        '<div class="triage-card"><b>Passo 2 · Triagem — Lex Seed</b>'
        f'<div class="triage-cards">{"".join(cards)}</div><p>{review}</p></div>'
    )


def why_rows(d: Decision) -> list[list[str]]:
    return [[f.rule_id, f.span, f.effect] for f in d.fired]


def rubric_tables(rubric: Rubric) -> tuple[list[list[str]], list[list[str]]]:
    types = [
        [
            t.name,
            t.description,
            URGENCY_PT[t.urgency],
            RISK_PT[t.risk],
            f"{t.legal_deadline_days} dias" if t.legal_deadline_days else "—",
        ]
        for t in rubric.types.values()
    ]
    signals = []
    for s in rubric.signals.values():
        effects = []
        if s.urgency:
            effects.append(f"urgência → {URGENCY_PT[s.urgency]}")
        if s.risk:
            effects.append(f"risco → {RISK_PT[s.risk]}")
        if s.override:
            effects.append(f"prioridade → {PRIORITY_PT[s.override]}")
        signals.append([s.name, s.description, "; ".join(effects)])
    return types, signals


def load_examples(path: Path) -> list[dict]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def example_run(example: dict, rubric: Rubric) -> TriageRun:
    """Rebuild a precomputed example: stored model output, decision recomputed from the current rubric."""
    sanitized = sanitize(example["text"])
    extraction = parse_extraction(json.dumps(example["extraction"], ensure_ascii=False), rubric, sanitized.text)
    return TriageRun(example["text"], False, sanitized, extraction, decide(extraction, rubric), 1, example["seconds"])


def theme_settings() -> dict[str, str]:
    """Gradio theme variables; light and dark get the same dark values, so the page is always dark."""
    b = BRAND
    base = {
        "body_background_fill": b["bg_dark"],
        "body_text_color": b["fg_dark"],
        "body_text_color_subdued": b["muted"],
        "background_fill_primary": b["bg_dark"],
        "background_fill_secondary": "#252C31",
        "block_background_fill": "#252C31",
        "block_label_text_color": b["muted"],
        "block_title_text_color": b["fg_dark"],
        "border_color_primary": b["line"],
        "border_color_accent": b["amber"],
        "input_background_fill": b["bg_dark"],
        "input_border_color_focus": b["amber"],
        "link_text_color": b["amber"],
        "link_text_color_hover": b["ochre"],
        "link_text_color_visited": b["amber"],
        "button_primary_background_fill": b["amber"],
        "button_primary_background_fill_hover": b["ochre"],
        "button_primary_text_color": b["on_accent"],
        "button_primary_border_color": b["amber"],
        "button_secondary_background_fill": b["graphite"],
        "button_secondary_background_fill_hover": b["graphite"],
        "button_secondary_text_color": b["fg_dark"],
        "button_secondary_border_color": b["graphite"],
        "button_secondary_border_color_hover": b["amber"],
        "color_accent": b["amber"],
        "color_accent_soft": b["line"],
        "table_even_background_fill": "#252C31",
        "table_odd_background_fill": b["bg_dark"],
    }
    no_dark_variant = {"color_accent", "color_accent_soft"}
    return {**base, **{f"{k}_dark": v for k, v in base.items() if k not in no_dark_variant}}


def timing_line(run: TriageRun) -> str:
    """One privacy-safe log line per request: stages and seconds, never the text."""
    reasons = ",".join(run.decision.review_reasons) or "-"
    return (
        f"triage seconds={run.seconds:.1f} attempts={run.attempts} priority={run.decision.priority} reasons={reasons}"
    )


def localize_queue_push(result: tuple) -> tuple:
    """Replace Gradio's English 'Queue is full' message; everything else passes through."""
    ok, message, state = result
    return (ok, QUEUE_FULL, state) if state == "queue_full" else result
