"""Score an extractor on cases.jsonl. Headline: does it miss what is serious?

Usage: python -m triage.eval --model <name> [--cases cases.jsonl] [--out metrics/<name>.json]
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from triage.cases import Case, load_cases
from triage.decide import Decision, decide
from triage.extract import Extractor
from triage.pipeline import TriageRun, run_triage
from triage.rubric import Rubric, load_rubric
from triage.sanitize import sanitize


@dataclass
class Report:
    model: str
    n: int
    high_risk_recall: float
    high_risk_recall_strict: float
    review_rate_design: float
    review_rate_uncertainty: float
    type_accuracy: float
    signal_recall: float
    priority_accuracy: float
    valid_output_rate: float
    mean_seconds: float
    max_seconds: float
    rubric_fit: list[dict] = field(default_factory=list)
    rows: list[dict] = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)


def _serious(d: Decision) -> bool:
    return d.risk == "high" or d.priority == "critical"


def _share(flags: list[bool]) -> float:
    return sum(flags) / len(flags) if flags else 0.0


def score(cases: list[Case], runs: list[TriageRun], rubric: Rubric, model: str) -> Report:
    golds = [decide(c.gold, rubric) for c in cases]
    serious = [(g, r.decision) for g, r in zip(golds, runs) if _serious(g)]
    gold_signals = sum(len(c.gold.signals) for c in cases)
    matched = sum(
        len({h.id for h in c.gold.signals} & {h.id for h in r.extraction.signals})
        for c, r in zip(cases, runs)
        if r.extraction
    )
    rows = [
        {
            "id": c.id,
            "gold_type": g.type,
            "type": r.decision.type,
            "gold_priority": g.priority,
            "priority": r.decision.priority,
            "gold_signals": sorted(h.id for h in c.gold.signals),
            "signals": sorted(h.id for h in r.extraction.signals) if r.extraction else [],
            "review_reasons": list(r.decision.review_reasons),
            "valid_output": r.extraction is not None,
            "seconds": round(r.seconds, 2),
        }
        for c, g, r in zip(cases, golds, runs)
    ]
    seconds = [r.seconds for r in runs]
    return Report(
        model=model,
        n=len(cases),
        high_risk_recall=_share([_serious(p) or p.human_review for _, p in serious]),
        high_risk_recall_strict=_share([_serious(p) for _, p in serious]),
        review_rate_design=_share([r.decision.review_by_design for r in runs]),
        review_rate_uncertainty=_share([r.decision.review_by_uncertainty for r in runs]),
        type_accuracy=_share([g.type == r.decision.type for g, r in zip(golds, runs)]),
        signal_recall=matched / gold_signals if gold_signals else 1.0,
        priority_accuracy=_share([g.priority == r.decision.priority for g, r in zip(golds, runs)]),
        valid_output_rate=_share([r.extraction is not None for r in runs]),
        mean_seconds=sum(seconds) / len(seconds) if seconds else 0.0,
        max_seconds=max(seconds, default=0.0),
        rubric_fit=[
            {"id": c.id, "rubric_priority": g.priority, "fred_priority": c.fred_priority}
            for c, g in zip(cases, golds)
            if c.fred_priority and c.fred_priority != g.priority
        ],
        rows=rows,
    )


def gold_runs(cases: list[Case], rubric: Rubric) -> list[TriageRun]:
    return [TriageRun(c.text, False, sanitize(c.text), c.gold, decide(c.gold, rubric), 0, 0.0) for c in cases]


def evaluate(cases: list[Case], rubric: Rubric, extractor: Extractor) -> Report:
    runs = [run_triage(c.text, rubric, extractor) for c in cases]
    return score(cases, runs, rubric, extractor.name)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--model", required=True)
    parser.add_argument("--cases", type=Path, default=Path(__file__).resolve().parent.parent / "cases.jsonl")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    rubric = load_rubric()
    cases = load_cases(args.cases, rubric)
    if args.model == "gold":
        report = score(cases, gold_runs(cases, rubric), rubric, "gold")
    else:
        from triage.extractors import get_extractor  # created with the model spike

        report = evaluate(cases, rubric, get_extractor(args.model))

    out = report.to_json()
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(out + "\n", encoding="utf-8")
    summary = {k: v for k, v in json.loads(out).items() if k not in ("rows", "rubric_fit")}
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
