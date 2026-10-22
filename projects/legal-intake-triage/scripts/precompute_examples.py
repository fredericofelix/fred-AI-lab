"""Run the default model on chosen cases and store its output as the Space's instant examples.

Usage: python -m scripts.precompute_examples T-001:"Pedido de titular" T-002:"Contrato" ...
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

from triage.cases import load_cases
from triage.extractors import DEFAULT_MODEL, get_extractor
from triage.pipeline import run_triage
from triage.rubric import load_rubric

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    wanted = dict(arg.split(":", 1) for arg in sys.argv[1:])
    rubric = load_rubric()
    cases = {c.id: c for c in load_cases(ROOT / "cases.jsonl", rubric)}
    extractor = get_extractor(DEFAULT_MODEL)
    run_triage("Aquecimento do modelo.", rubric, extractor)  # keep load time out of the stored seconds
    examples = []
    for cid, label in wanted.items():
        run = run_triage(cases[cid].text, rubric, extractor)
        if run.extraction is None:
            sys.exit(f"{cid}: model output invalid, pick another case")
        extraction = asdict(run.extraction)
        extraction["signals"] = [asdict(h) for h in run.extraction.signals]
        examples.append(
            {
                "id": cid,
                "label": label,
                "text": cases[cid].text,
                "extraction": extraction,
                "seconds": round(run.seconds, 1),
            }
        )
        print(cid, run.decision.priority, f"{run.seconds:.1f}s")
    out = ROOT / "space" / "examples.json"
    out.write_text(json.dumps(examples, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
