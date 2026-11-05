"""Throwaway Space for the model spike: run one candidate on one text and show seconds per stage."""

import os

os.environ.setdefault("GRADIO_ANALYTICS_ENABLED", "False")

import json  # noqa: E402

import gradio as gr  # noqa: E402

from guardrail.pipeline import run_check  # noqa: E402
from guardrail.rubric import load_rubric  # noqa: E402
from guardrail.runtimes import CANDIDATES, get_model_pass  # noqa: E402

RUBRIC = load_rubric()
_loaded = {}  # one model pass in memory at a time


def run(text: str, model: str):
    if not (text or "").strip():
        return "Cole um texto.", ""
    if model not in _loaded:
        _loaded.clear()
        _loaded[model] = get_model_pass(model)
    result = run_check(text, RUBRIC, _loaded[model])  # never logged or stored
    timing = " · ".join(f"{k} {v:.1f} s" for k, v in result.seconds.items())
    flags = [{"group": f.group, "kind": f.kind, "text": f.text, "source": f.source} for f in result.flags]
    return f"{sum(result.seconds.values()):.1f} s ({timing}) · modelo: {result.model_status}", json.dumps(
        {"flags": flags, "preview": result.preview}, ensure_ascii=False, indent=2
    )


with gr.Blocks(title="Lex Seed · Guardrail de Sigilo (spike)", analytics_enabled=False) as demo:
    gr.Markdown("# Lex Seed · Guardrail de Sigilo (spike)\n🚧 Em construção: versão de teste para escolher o modelo.")
    gr.Markdown("⚠️ **Não cole dados reais.** O texto é processado só em memória e não é guardado.")
    text_in = gr.Textbox(label="Texto", lines=6, max_length=3000)
    model_in = gr.Dropdown(choices=list(CANDIDATES), value=CANDIDATES[0], label="Modelo")
    button = gr.Button("Verificar", variant="primary")
    timing = gr.Markdown()
    out = gr.Code(language="json", label="Resultado")
    button.click(run, inputs=[text_in, model_in], outputs=[timing, out], api_visibility="private")

if __name__ == "__main__":
    demo.queue(max_size=10)
    demo.launch()
