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

## Latency on the Space (Hugging Face CPU basic, 2 vCPU)

To be measured on the spike Space.
