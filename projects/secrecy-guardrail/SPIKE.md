# Model spike (2026-11-05)

Goal: pick the model pass for groups 1 (companies), 3 (strategy) and 5 (third-party information), spec §6.
Criteria, in order: recall on groups 1–5, valid spans, latency end to end and warm (target ≤ 30 s, stop above 60 s),
RAM, license, PT-BR quality.

## Candidates

| Key | What | License |
|---|---|---|
| `gliner` | GLiNER2 zero-shot ([fastino/gliner2-privacy-filter-PII-multi](https://huggingface.co/fastino/gliner2-privacy-filter-PII-multi), the model `privacyseed-lgpd[ml]` already loads), PT labels for all three groups | Apache-2.0 |
| `qwen3-4b` | [unsloth/Qwen3-4B-Instruct-2507-GGUF](https://huggingface.co/unsloth/Qwen3-4B-Instruct-2507-GGUF) Q4_K_M via llama.cpp, JSON constrained by schema (same file and revision as the triage Space) | Apache-2.0 |
| `hybrid` | GLiNER2 for companies, Qwen3-4B for strategy and third-party information | Apache-2.0 |

`GlinerPass` calls `privacyseed_lgpd.recognizers._model` (a private module): acceptable because `privacyseed-lgpd` is pinned to 0.1.0.

## Quality: first 10 cases (local, Apple Silicon, 2 threads, `metrics/spike-*.json`)

| Pass | Headline recall (1, 2, 4, 5) | Group 1 | Group 3 (experimental) | Group 5 | Clean false alarm | Flag precision | Dropped spans | Seconds p50 / max |
|---|---|---|---|---|---|---|---|---|
| rules + detector only (`metrics/v0-rules-only.json`) | 0.71 | 0.56 | 0.67 | 0.50 | 0/1 | 0.94 | — | 0.2 / — |
| `gliner` | 0.94 | 1.00 | 0.83 | 0.50 | **1/1** | 0.85 | 0 | 0.3 / 7.8 |
| `qwen3-4b` | 0.88 | 0.78 | 0.67 | 1.00 | 0/1 | 0.88 | 2 | 3.8 / 33.6 |
| **`hybrid`** | **1.00** | **1.00** | 0.67 | **1.00** | **0/1** | 0.86 | 1 | 4.9 / 29.6 |

- `gliner`'s strategy label marks statute names ("Código Civil", "Lei das Duplicatas") as strategy: the clean case fails.
- `qwen3-4b` misses some company names that GLiNER2 finds; both miss the pure thesis clauses of C-003.
- The max includes the first call, which loads the weights.
- Detector finding (Privacy Seed backlog, not fixed here): `privacyseed-lgpd` 0.1.0 labels a bare year ("2023") as `birth_date` (score 0.94).

## Quality on the full set (40 cases, `metrics/v1-*.json`)

| Pass | Headline recall | Group 3 | Group 5 | Clean false alarm | Flag precision |
|---|---|---|---|---|---|
| rules + detector only | 0.63 | 0.63 | 0.43 | 0/10 | 0.96 |
| `hybrid`, before the generic-name filter | 0.93 | 0.63 | 0.57 | 4/10 | 0.77 |
| `hybrid`, with the generic-name filter | 0.93 | 0.63 | 0.57 | 0/10 | 0.84 |
| **`hybrid`, after the final-review merge fix** | **0.98** | 0.63 | **0.86** | **0/10** | 0.84 |

The four false alarms were company flags from GLiNER2 on placeholders (`[CLIENTE]`), "empresa X", "LGPD" and
"Fazenda Pública". The filter (`generic_names` in `rubric.yaml`, model flags only) was tuned on these same cases.

## Latency on the Space (Hugging Face CPU basic, 2 vCPU), `hybrid`, 2026-11-05

| Call | End to end | Detector | Model pass |
|---|---|---|---|
| First (download + load both models) | 73 s | 14.4 s | 58.6 s |
| Warm, C-001 | 24 s | 0.9 s | 23.3 s |
| Warm, C-004 | 18 s | 0.6 s | 17.7 s |
| Warm, C-031 | 23 s | 0.6 s | 22.6 s |

Warm calls are within the 30 s target. The final Space loads both models at boot (`warm_up`), so visitors only
see the cold time right after a restart. Both models fit in the free tier's memory (no crash across the runs).

## Choice

**`hybrid`** (`DEFAULT_MODEL_PASS`): best headline recall with no clean false alarms, warm latency 18–24 s on the
free CPU tier. The spike Space was deleted after the measurement. The final review found that the merge dropped a
long model span (the secret) when it overlapped a short NDA cue; fixing it raised group 5 from 0.57 to 0.86.
