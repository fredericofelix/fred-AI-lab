"""Throwaway Space for the model spike: run one candidate on one request and show the seconds."""

import os

os.environ.setdefault("GRADIO_ANALYTICS_ENABLED", "False")

import json  # noqa: E402
from dataclasses import asdict  # noqa: E402

import gradio as gr  # noqa: E402

from triage.extractors import CANDIDATES, get_extractor  # noqa: E402
from triage.pipeline import run_triage  # noqa: E402
from triage.rubric import load_rubric  # noqa: E402

RUBRIC = load_rubric()
_loaded = {}  # one model in memory at a time


def run(text: str, model: str):
    if not (text or "").strip():
        return "Cole uma demanda.", ""
    if model not in _loaded:
        _loaded.clear()
        _loaded[model] = get_extractor(model)
    result = run_triage(text, RUBRIC, _loaded[model])  # never logged or stored
    decision = asdict(result.decision)
    return f"{result.seconds:.1f} s · {result.attempts} tentativa(s)", json.dumps(
        {"sanitized": result.sanitized.text, "decision": decision}, ensure_ascii=False, indent=2
    )


with gr.Blocks(title="Lex Seed · Triagem (spike)", analytics_enabled=False) as demo:
    gr.Markdown("# Lex Seed · Triagem (spike)\n🚧 Em construção: versão de teste para escolher o modelo.")
    gr.Markdown("⚠️ **Não cole dados reais.** O texto é processado só em memória e não é guardado.")
    text_in = gr.Textbox(label="Demanda", lines=6, max_length=3000)
    model_in = gr.Dropdown(choices=list(CANDIDATES), value=next(iter(CANDIDATES)), label="Modelo")
    button = gr.Button("Triar", variant="primary")
    timing = gr.Markdown()
    out = gr.Code(language="json", label="Resultado")
    button.click(run, inputs=[text_in, model_in], outputs=[timing, out], api_visibility="private")

if __name__ == "__main__":
    demo.launch()
