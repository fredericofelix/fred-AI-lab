"""Score the guardrail on cases.jsonl: recall per group (headline: groups 1, 2, 4, 5), false alarms, latency.

Usage: python -m guardrail.eval --model NAME [--out metrics/NAME.json]
NAME "none" runs the fixed rules and the detector only (no model pass).
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import statistics
from dataclasses import dataclass
from pathlib import Path

from guardrail.cases import CASES_PATH, Case, Label, load_cases
from guardrail.flags import Flag
from guardrail.model_pass import FakeModelPass, ModelPass
from guardrail.pipeline import GuardrailRun, run_check
from guardrail.rubric import Rubric, load_rubric

GROUPS = (1, 2, 3, 4, 5, 6)
HEADLINE_GROUPS = (1, 2, 4, 5)


@dataclass(frozen=True)
class Report:
    model: str
    recall: dict[int, float | None]
    precision: dict[int, float | None]
    headline_recall: float | None
    clean_false_alarm: float | None
    flag_precision: float | None
    dropped_spans: int
    model_failures: int
    seconds_p50: float
    seconds_max: float
    misses: list[dict]

    def to_json(self) -> str:
        return json.dumps(dataclasses.asdict(self), ensure_ascii=False, indent=2)


def _share(hits: int, total: int) -> float | None:
    return round(hits / total, 4) if total else None


def _positions(text: str, span: str) -> list[tuple[int, int]]:
    out, start = [], text.find(span)
    while start >= 0:
        out.append((start, start + len(span)))
        start = text.find(span, start + 1)
    return out


def _hit(label: Label, flag: Flag, text: str) -> bool:
    return flag.group == label.group and any(s < flag.end and flag.start < e for s, e in _positions(text, label.span))


def score(cases: list[Case], runs: list[GuardrailRun], model: str) -> Report:
    labels_total = dict.fromkeys(GROUPS, 0)
    labels_hit = dict.fromkeys(GROUPS, 0)
    flags_total = dict.fromkeys(GROUPS, 0)
    flags_ok = dict.fromkeys(GROUPS, 0)
    misses: list[dict] = []
    clean_alarms = 0
    for case, run in zip(cases, runs, strict=True):
        for label in case.labels:
            labels_total[label.group] += 1
            if any(_hit(label, f, case.text) for f in run.flags):
                labels_hit[label.group] += 1
            else:
                misses.append({"case": case.id, "doubtful": case.doubtful, **dataclasses.asdict(label)})
        for flag in run.flags:
            flags_total[flag.group] += 1
            if any(_hit(label, flag, case.text) for label in case.labels):
                flags_ok[flag.group] += 1
        clean_alarms += case.clean and bool(run.flags)
    seconds = [sum(r.seconds.values()) for r in runs] or [0.0]
    return Report(
        model=model,
        recall={g: _share(labels_hit[g], labels_total[g]) for g in GROUPS},
        precision={g: _share(flags_ok[g], flags_total[g]) for g in GROUPS},
        headline_recall=_share(
            sum(labels_hit[g] for g in HEADLINE_GROUPS), sum(labels_total[g] for g in HEADLINE_GROUPS)
        ),
        clean_false_alarm=_share(clean_alarms, sum(c.clean for c in cases)),
        flag_precision=_share(sum(flags_ok.values()), sum(flags_total.values())),
        dropped_spans=sum(r.dropped_spans for r in runs),
        model_failures=sum(r.model_status != "ok" for r in runs),
        seconds_p50=round(statistics.median(seconds), 2),
        seconds_max=round(max(seconds), 2),
        misses=misses,
    )


def evaluate(cases: list[Case], rubric: Rubric, model_pass: ModelPass, detector=None) -> Report:
    runs = [run_check(c.text, rubric, model_pass, detector) for c in cases]
    return score(cases, runs, model_pass.name)


def _model_pass(name: str) -> ModelPass:
    if name == "none":
        return FakeModelPass([], name="none")
    from guardrail.runtimes import get_model_pass  # heavy imports only when a model is asked for

    return get_model_pass(name)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--model", default="none")
    parser.add_argument("--cases", type=Path, default=CASES_PATH)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = evaluate(load_cases(args.cases), load_rubric(), _model_pass(args.model))
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(report.to_json() + "\n", encoding="utf-8")
    print(report.to_json())


if __name__ == "__main__":
    main()
