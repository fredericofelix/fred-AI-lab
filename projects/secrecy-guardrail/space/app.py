"""Hugging Face Space: Lex Seed · Guardrail de Sigilo."""

import os

os.environ.setdefault("GRADIO_ANALYTICS_ENABLED", "False")

import threading  # noqa: E402
import time  # noqa: E402
from pathlib import Path  # noqa: E402

import gradio as gr  # noqa: E402
import views  # noqa: E402

from guardrail.personal import default_detector  # noqa: E402
from guardrail.pipeline import StageEvent  # noqa: E402
from guardrail.rubric import RUBRIC_PATH, load_rubric  # noqa: E402
from guardrail.runtimes import DEFAULT_MODEL_PASS, get_model_pass  # noqa: E402

HERE = Path(__file__).parent
RUBRIC = load_rubric()
MODEL_PASS = get_model_pass(DEFAULT_MODEL_PASS)
EXAMPLES = views.load_examples(HERE / "examples.json")
HOW_IT_WORKS = (HERE / "how_it_works.md").read_text(encoding="utf-8")
METRICS = HERE / "METRICS.md"



def _warm_up():
    default_detector().analyze("aquecimento")  # loads the Privacy Seed detector (regex + GLiNER2)
    MODEL_PASS.warm_up()


# Load the models in the background, so the page and the examples work at once.
threading.Thread(target=_warm_up, daemon=True).start()


def _watchdog():
    while True:
        time.sleep(15)
        MODEL_PASS.check_watchdog(limit_s=300)  # longer than download + load + one request


threading.Thread(target=_watchdog, daemon=True).start()


def run(text: str):
    yield from views.handle(text, RUBRIC, MODEL_PASS)


def show_example(index: int):
    example = EXAMPLES[index]
    run_ = views.example_run(example, RUBRIC)
    events = [StageEvent(stage, True, "") for stage, _ in views.STEPS]
    return (example["text"], *views.render(run_, events, RUBRIC))


with gr.Blocks(title="Lex Seed · Guardrail de Sigilo", analytics_enabled=False) as demo:
    gr.Markdown("# Lex Seed · Guardrail de Sigilo")
    with gr.Tabs():
        with gr.Tab("Verificar"):
            gr.Markdown(
                "Cole o texto que você ia enviar a uma ferramenta de IA. O guardrail aponta o que pode violar o "
                "sigilo profissional e sugere substituições. Ele não reescreve nem envia nada."
            )
            gr.Markdown("**Exemplos prontos** (resultado na hora, gerado antes pelo mesmo modelo):")
            with gr.Row():
                example_buttons = [gr.Button(e["label"], size="sm") for e in EXAMPLES]
            text_in = gr.Textbox(label="Ou cole um texto", lines=8, max_length=3000)
            gr.Markdown(views.NOTICE)
            button = gr.Button("Verificar texto", variant="primary")
            gr.Markdown(views.LOAD_NOTICE, elem_classes="load-notice")
            status = gr.Markdown()
            steps = gr.HTML()
            personal = gr.HTML()
            result = gr.HTML()
            flags = gr.HTML()
            preview = gr.Textbox(
                label="Prévia com as substituições sugeridas (copie se quiser)",
                lines=8,
                interactive=False,
                buttons=["copy"],
            )
            gr.Markdown(views.DISCLAIMER)
            gr.Markdown(views.CTA)
        with gr.Tab("A rubrica"):
            gr.Markdown(
                "Os grupos, os fundamentos legais, as marcações e as substituições ficam em um arquivo editável, "
                "`rubric.yaml`. Baixe, ajuste ao seu jurídico e rode localmente (veja o README do projeto)."
            )
            gr.Code(RUBRIC_PATH.read_text(encoding="utf-8"), language="yaml", interactive=False)
            gr.DownloadButton("Baixar rubric.yaml", value=str(RUBRIC_PATH))
        with gr.Tab("Como funciona"):
            gr.Markdown(HOW_IT_WORKS)
        with gr.Tab("Métricas"):
            gr.Markdown(METRICS.read_text(encoding="utf-8") if METRICS.exists() else "Métricas da v0 em breve.")

    outputs = [steps, personal, result, flags, preview, status]
    # private: not listed in the API docs and not callable by Gradio clients.
    button.click(run, inputs=text_in, outputs=outputs, api_visibility="private")
    for i, b in enumerate(example_buttons):
        b.click(lambda i=i: show_example(i), outputs=[text_in, *outputs], api_visibility="private")

if __name__ == "__main__":
    theme = gr.themes.Base(font=gr.themes.GoogleFont("Inter")).set(**views.theme_settings())
    demo.queue(max_size=10)  # one request at a time on 2 vCPUs; cap the waiting line
    _push = demo._queue.push  # Gradio is pinned (6.30.0)

    async def _push_pt(*args, **kwargs):
        return views.localize_queue_push(await _push(*args, **kwargs))

    demo._queue.push = _push_pt
    demo.launch(css=views.CSS, theme=theme, head=views.FONTS_HEAD)
