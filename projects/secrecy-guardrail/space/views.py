"""Pure helpers for the Space UI (no gradio import, so CI tests them)."""

from __future__ import annotations

import base64
import html
import json
from collections.abc import Iterator
from pathlib import Path

from guardrail.model_pass import FakeModelPass, ModelSpan
from guardrail.pipeline import GuardrailRun, StageEvent, check, run_check
from guardrail.rubric import Rubric

ROOT = Path(__file__).resolve().parent
ROBOT_SVG = next(
    p for p in (ROOT / "assets" / "icon-robot.svg", ROOT.parent / "assets" / "icon-robot.svg") if p.exists()
)

DETECTOR_SPACE = "https://huggingface.co/spaces/fred-ai-lab/detector-lgpd"
DETECTOR_REPO = "https://github.com/fredericofelix/privacyseed-lgpd"

NOTICE = (
    "⚠️ Use texto fictício ou já genérico. Para texto real, rode no seu computador (veja o README). "
    "O texto é processado na infraestrutura do Hugging Face (EUA); este app não armazena nem registra o que "
    "você cola. Não cole dados sensíveis."
)
DISCLAIMER = (
    "**Guardrail de sigilo profissional antes do prompt.** Demonstração com dados sintéticos: regras fixas, o "
    "Detector LGPD da Privacy Seed e um modelo de IA aberto, rodando aqui mesmo, apontam trechos que podem violar o "
    "sigilo profissional. A ferramenta pode errar e não substitui a sua revisão: você decide o que enviar. "
    "Esta ferramenta não constitui aconselhamento jurídico."
)
CTA = (
    "Quer aplicar ao seu jurídico, com a sua lista de clientes e processos e as suas ferramentas de IA? "
    "[Fale com a Lex Seed](https://www.lexseed.com.br/?utm_source=huggingface&utm_medium=demo"
    "&utm_campaign=guardrail-sigilo)."
)
EXPERIMENTAL = "O grupo “Estratégia e negociação” é experimental: aqui o modelo erra mais. Revise com atenção."
INJECTION = "Atenção: possível instrução manipulativa no texto"
LOAD_NOTICE = (
    "⏱️ A primeira verificação depois de um tempo sem uso pode levar alguns minutos, porque os modelos são "
    "carregados. Os exemplos prontos respondem na hora."
)
EMPTY_INPUT = "Cole um texto para verificar."
TRUNCATED = "Texto truncado em 3000 caracteres."
QUEUE_FULL = "Muitas pessoas testando agora. Espere um minuto e tente de novo, ou use um dos exemplos prontos."

STEPS = [
    ("personal", "Dados pessoais — Detector LGPD by Privacy Seed"),
    ("rules", "Regras fixas: processos, marcações, valores"),
    ("model", "Modelo de IA: empresas, estratégia, informação de terceiro"),
    ("merge", "Juntando os pontos e preparando a prévia"),
]

# Lex Seed brand tokens (lex-seed-site/docs/brand.md), same as the triage Space.
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
CSS = """
body, .gradio-container { font-family: 'Inter', sans-serif }
.gradio-container h1, .gradio-container h2, .gradio-container h3 { font-family: 'Nunito', sans-serif; font-weight: 900 }
.gradio-container h1 { color: #F4F6F5 }
.tab-wrapper button.selected, button[role="tab"][aria-selected="true"] { color: #FFC857; border-color: #FFC857 }
.load-notice { color: #A9B4B0; font-size: 14px }
@keyframes bob { 0%,100% { transform: translateY(0) rotate(0) } 25% { transform: translateY(-6px) rotate(-4deg) }
  75% { transform: translateY(-6px) rotate(4deg) } }
@keyframes ring { 0% { box-shadow: 0 0 0 0 rgba(255,200,87,.7) } 100% { box-shadow: 0 0 0 22px rgba(255,200,87,0) } }
.g-steps { display:flex; gap:18px; align-items:center; padding:16px; border-radius:12px; background:#1E2428;
  border:1px solid #34404A; color:#F4F6F5 }
.g-steps .robot { width:72px; height:72px; border-radius:50% }
.g-steps .robot.thinking { animation: bob 1.6s ease-in-out infinite, ring 1.6s ease-out infinite }
.g-steps .step { margin:4px 0; font-size:14px }
.g-steps .done { color:#F4F6F5 } .g-steps .now { color:#FFC857 } .g-steps .next { color:#A9B4B0; opacity:.7 }
.g-card { border-radius:10px; padding:12px; margin:8px 0; border:1px solid #34404A }
/* Privacy Seed's own step: co-branded block, the one place its green appears. */
.g-card.detector { border:2px solid #2e7d32 }
.g-card.verdict { border:2px solid #FFC857 }
.g-card.warn { border:2px solid #D9A23A }
.g-flags { width:100%; border-collapse:collapse; font-size:14px }
.g-flags th, .g-flags td { border-bottom:1px solid #34404A; padding:6px; text-align:left; vertical-align:top }
"""


def _robot_src() -> str:
    return "data:image/svg+xml;base64," + base64.b64encode(ROBOT_SVG.read_bytes()).decode()


def _count(n: int, one: str, many: str) -> str:
    return f"{n} {one if n == 1 else many}"


def steps_html(events: list[StageEvent], running: bool) -> str:
    done = {e.stage: e.detail for e in events if e.done}
    started = {e.stage for e in events}
    rows = []
    for stage, label in STEPS:
        if stage in done:
            detail = f" ({html.escape(done[stage])})" if done[stage] else ""
            rows.append(f'<div class="step done">✓ {label}{detail}</div>')
        elif stage in started:
            rows.append(f'<div class="step now">● {label}…</div>')
        else:
            rows.append(f'<div class="step next">○ {label}</div>')
    robot_class = "robot thinking" if running else "robot"
    return (
        f'<div class="g-steps"><img class="{robot_class}" src="{_robot_src()}" alt="Robô da Lex Seed">'
        f"<div>{''.join(rows)}</div></div>"
    )


def personal_html(run: GuardrailRun) -> str:
    names = sum(1 for f in run.flags if f.group == 1 and f.source == "detector")
    data = sum(1 for f in run.flags if f.group == 6)
    return (
        '<div class="g-card detector"><b>Passo 1 · Dados pessoais — '
        f'<a href="{DETECTOR_SPACE}">Detector LGPD</a> by Privacy Seed</b><br>'
        f"{_count(data, 'dado pessoal', 'dados pessoais')} e {_count(names, 'nome', 'nomes')} encontrados. "
        f'Biblioteca aberta: <a href="{DETECTOR_REPO}">privacyseed-lgpd</a>.'
        + "".join(f"<br>⚠️ {html.escape(w)}" for w in run.warnings)
        + "</div>"
    )


def result_html(run: GuardrailRun, rubric: Rubric) -> str:
    title = "<b>Passo 2 · Sigilo profissional — Lex Seed</b>"
    parts = [f'<div class="g-card verdict">{title}<br>{html.escape(run.verdict)}']
    if run.truncated:
        parts.append(f"<br>{TRUNCATED}")
    parts.append("</div>")
    if any(f.group == 3 for f in run.flags):
        parts.append(f'<div class="g-card warn">{EXPERIMENTAL}</div>')
    if run.injection:
        found = "; ".join(f"“{html.escape(m)}”" for m in run.injection)
        parts.append(f'<div class="g-card warn">{INJECTION}: {found}. Revise o texto com atenção.</div>')
    return "".join(parts)


def flags_html(run: GuardrailRun, rubric: Rubric) -> str:
    if not run.flags:
        return ""
    rows = []
    for f in run.flags:
        group = rubric.groups[f.group]
        label = run.labels.get(f) or "só sinalizado"
        note = f"<br><i>{html.escape(f.note)}</i>" if f.note else ""
        rows.append(
            f"<tr><td>{html.escape(group.name)}</td><td>“{html.escape(f.text)}”{note}</td>"
            f"<td>{html.escape(group.reason)}<br><small>{html.escape(group.anchor)}</small></td>"
            f"<td>{html.escape(label)}</td></tr>"
        )
    return (
        '<table class="g-flags"><tr><th>Grupo</th><th>Trecho</th><th>Motivo e fundamento</th>'
        f"<th>Substituição sugerida</th></tr>{''.join(rows)}</table>"
    )


def render(run: GuardrailRun, events: list[StageEvent], rubric: Rubric) -> tuple[str, str, str, str, str, str]:
    return (
        steps_html(events, running=False),
        personal_html(run),
        result_html(run, rubric),
        flags_html(run, rubric),
        run.preview,
        "",
    )


def handle(text: str, rubric: Rubric, model_pass, detector=None) -> Iterator[tuple[str, str, str, str, str, str]]:
    """The Space handler without gradio: yields (steps, step 1, step 2, flags, preview, status)."""
    if not (text or "").strip():
        yield "", "", "", "", "", EMPTY_INPUT
        return
    events: list[StageEvent] = []
    for item in check(text, rubric, model_pass, detector):  # never logged or stored
        if isinstance(item, StageEvent):
            events.append(item)
            yield steps_html(events, running=True), "", "", "", "", ""
        else:
            print(timing_line(item), flush=True)  # stages and seconds only, never the text
            yield render(item, events, rubric)


def load_examples(path: Path) -> list[dict]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def example_run(example: dict, rubric: Rubric, detector=None) -> GuardrailRun:
    """Rebuild a precomputed example: the stored model output replayed through the current pipeline."""
    spans = [ModelSpan(s["group"], s["kind"], s["span"]) for s in example["model_spans"]]
    return run_check(example["text"], rubric, FakeModelPass([spans], name="precomputed"), detector)


def timing_line(run: GuardrailRun) -> str:
    """One privacy-safe log line per request: stages and seconds, never the text."""
    seconds = " ".join(f"{k}={v:.1f}" for k, v in run.seconds.items())
    return f"guardrail {seconds} flags={len(run.flags)} model={run.model_status} dropped={run.dropped_spans}"


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


def localize_queue_push(result: tuple) -> tuple:
    """Replace Gradio's English 'Queue is full' message; everything else passes through."""
    ok, message, state = result
    return (ok, QUEUE_FULL, state) if state == "queue_full" else result
