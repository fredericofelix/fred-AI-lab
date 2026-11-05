"""Run the chosen model pass on the showcase cases and store its raw output in space/examples.json.

Usage: python -m scripts.precompute_examples [--model hybrid]
The Space replays the stored model output through the current pipeline, so examples answer at once.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import time
from pathlib import Path

from guardrail.cases import load_cases
from guardrail.pipeline import run_check
from guardrail.rubric import load_rubric
from guardrail.runtimes import DEFAULT_MODEL_PASS, get_model_pass

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = {  # case id → button label
    "C-001": "E-mail de proposta de acordo",
    "C-004": "Informação sob NDA",
    "C-003": "Tese da contestação",
    "C-008": "Texto com instrução manipulativa",
    "C-006": "Pergunta sem dado sigiloso",
}


class _Recorder:
    def __init__(self, inner):
        self.name, self._inner, self.spans = inner.name, inner, []

    def __call__(self, text):
        self.spans = self._inner(text)
        return self.spans


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--model", default=DEFAULT_MODEL_PASS)
    args = parser.parse_args()
    rubric, cases = load_rubric(), {c.id: c for c in load_cases()}
    recorder = _Recorder(get_model_pass(args.model))
    out = []
    for case_id, label in EXAMPLES.items():
        start = time.perf_counter()
        run_check(cases[case_id].text, rubric, recorder)
        out.append({
            "label": label,
            "case": case_id,
            "text": cases[case_id].text,
            "model": args.model,
            "seconds": round(time.perf_counter() - start, 1),
            "model_spans": [dataclasses.asdict(s) for s in recorder.spans],
        })
    path = ROOT / "space" / "examples.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {path} ({len(out)} examples)")


if __name__ == "__main__":
    main()
