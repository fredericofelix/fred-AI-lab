"""Hugging Face Space: Lex Seed · Triagem Jurídica."""

import os

os.environ.setdefault("GRADIO_ANALYTICS_ENABLED", "False")

import threading  # noqa: E402
from pathlib import Path  # noqa: E402

import gradio as gr  # noqa: E402
import views  # noqa: E402

from triage.extractors import DEFAULT_MODEL, get_extractor  # noqa: E402
from triage.pipeline import MAX_CHARS, StageEvent, TriageRun, triage  # noqa: E402
from triage.rubric import DEFAULT_RUBRIC, load_rubric  # noqa: E402
from triage.sanitize import sanitize  # noqa: E402

HERE = Path(__file__).parent
RUBRIC = load_rubric()
EXTRACTOR = get_extractor(DEFAULT_MODEL)
EXAMPLES = views.load_examples(HERE / "examples.json")
TYPES_TABLE, SIGNALS_TABLE = views.rubric_tables(RUBRIC)
HOW_IT_WORKS = (HERE / "how_it_works.md").read_text(encoding="utf-8")
METRICS = HERE / "METRICS.md"

# Load the model in the background so the page and the examples work at once.
threading.Thread(target=EXTRACTOR, args=("Aquecimento do modelo.",), daemon=True).start()


def _render(run: TriageRun, events: list[StageEvent]):
    return (
        views.steps_html(events, running=False),
        views.sanitize_html(run.sanitized),
        views.result_html(run.decision, RUBRIC),
        views.why_rows(run.decision),
        "Texto truncado em 3000 caracteres." if run.truncated else "",
    )


def run(text: str):
    empty = views.validate_input(text)
    if empty:
        yield "", "", "", [], empty
        return
    events: list[StageEvent] = []
    step1 = ""
    for item in triage(text, RUBRIC, EXTRACTOR):  # never logged or stored
        if isinstance(item, StageEvent):
            events.append(item)
            if item.stage == "sanitize" and item.done:
                # Show Step 1 while the model reads; regex sanitizing twice costs milliseconds.
                step1 = views.sanitize_html(sanitize(text[:MAX_CHARS]))
            yield views.steps_html(events, running=True, model_loaded=EXTRACTOR.loaded), step1, "", [], ""
        else:
            yield _render(item, events)


def show_example(index: int):
    run_ = views.example_run(EXAMPLES[index], RUBRIC)
    events = [StageEvent(stage, True, "") for stage, _ in views.STEPS]
    return (EXAMPLES[index]["text"], *_render(run_, events))


with gr.Blocks(title="Lex Seed · Triagem Jurídica", analytics_enabled=False) as demo:
    gr.Markdown("# Lex Seed · Triagem Jurídica")
    gr.Markdown(views.BANNER)
    with gr.Tabs():
        with gr.Tab("Triagem"):
            gr.Markdown("**Exemplos prontos** (resultado na hora, gerado antes pelo mesmo modelo):")
            with gr.Row():
                example_buttons = [gr.Button(e["label"], size="sm") for e in EXAMPLES]
            text_in = gr.Textbox(label="Ou cole uma demanda", lines=6, max_length=3000)
            gr.Markdown(views.NOTICE)
            button = gr.Button("Triar demanda", variant="primary")
            gr.Markdown(views.LOAD_NOTICE, elem_classes="load-notice")
            status = gr.Markdown()
            steps = gr.HTML()
            sanitized = gr.HTML()
            result = gr.HTML()
            why = gr.Dataframe(
                headers=["Regra", "Trecho literal da demanda", "Efeito"],
                label="Por quê: regras da rubrica acionadas",
                column_widths=["22%", "48%", "30%"],
                interactive=False,
                wrap=True,
            )
            gr.Markdown(views.DISCLAIMER)
            gr.Markdown(views.CTA)
        with gr.Tab("A rubrica"):
            gr.Markdown(
                "A régua da triagem fica em um arquivo editável, `rubric.yaml`. Baixe, ajuste ao seu jurídico e "
                "rode localmente (veja o README do projeto)."
            )
            gr.Dataframe(
                TYPES_TABLE,
                headers=["Tipo", "Descrição", "Urgência base", "Risco base", "Prazo legal"],
                label="Tipos",
                interactive=False,
                wrap=True,
            )
            gr.Dataframe(
                SIGNALS_TABLE, headers=["Sinal", "Descrição", "Efeito"], label="Sinais", interactive=False, wrap=True
            )
            gr.DownloadButton("Baixar rubric.yaml", value=str(DEFAULT_RUBRIC))
        with gr.Tab("Como funciona"):
            gr.Markdown(HOW_IT_WORKS)
        with gr.Tab("Métricas"):
            gr.Markdown(METRICS.read_text(encoding="utf-8") if METRICS.exists() else "Métricas da v0 em breve.")

    outputs = [steps, sanitized, result, why, status]
    # private: not listed in the API docs and not callable by Gradio clients.
    button.click(run, inputs=text_in, outputs=outputs, api_visibility="private")
    for i, b in enumerate(example_buttons):
        b.click(lambda i=i: show_example(i), outputs=[text_in, *outputs], api_visibility="private")

if __name__ == "__main__":
    theme = gr.themes.Base(font=gr.themes.GoogleFont("Inter")).set(**views.theme_settings())
    demo.launch(css=views.CSS, theme=theme, head=views.FONTS_HEAD)
