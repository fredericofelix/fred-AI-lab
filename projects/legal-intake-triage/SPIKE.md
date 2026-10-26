# Model spike (2026-10-21)

Goal: pick the open model that runs inside the free-of-extra-cost Space (spec §7).
Criteria, in order: high-risk recall, valid output, latency (target 30 s, limit 60 s), license, PT-BR quality.

## Candidates (GGUF, Q4_K_M, llama.cpp on CPU)

| Key | Repo | License |
|---|---|---|
| `qwen3-4b` | [unsloth/Qwen3-4B-Instruct-2507-GGUF](https://huggingface.co/unsloth/Qwen3-4B-Instruct-2507-GGUF) | Apache-2.0 |
| `qwen3-1.7b` | [unsloth/Qwen3-1.7B-GGUF](https://huggingface.co/unsloth/Qwen3-1.7B-GGUF) | Apache-2.0 |
| `phi-4-mini` | [unsloth/Phi-4-mini-instruct-GGUF](https://huggingface.co/unsloth/Phi-4-mini-instruct-GGUF) | MIT |
| `gemma-3-4b` | [unsloth/gemma-3-4b-it-GGUF](https://huggingface.co/unsloth/gemma-3-4b-it-GGUF) | Gemma terms |

Licenses read from the Hugging Face API tags on 2026-10-21.

## Quality: 10 provisional cases (local, `metrics/spike-*.json`)

| Model | Valid output | Type | Signals | Priority | High-risk recall (strict) |
|---|---|---|---|---|---|
| **qwen3-4b** | **100%** | **90%** | **90%** | **90%** | **86%** |
| qwen3-1.7b | 50% | 40% | 50% | 50% | 57% |
| phi-4-mini | 50% | 40% | 50% | 50% | 43% |
| gemma-3-4b | 50% | 40% | 50% | 40% | 43% |

The smaller models mostly fail by quoting spans that are not verbatim in the request; the check sends those to a human.
qwen3-4b's one miss: T-005 (hidden urgency), it caught the expiring contract but not the 3-month penalty as cash impact.

## Latency on the Space (Hugging Face CPU basic, 2 vCPU), qwen3-4b

| Setup | First call (download + load) | Warm calls |
|---|---|---|
| llama.cpp defaults | 534 s | 145 s |
| threads = container quota (2) | 133 s | 28 s (T-009), 25 s (T-001), 40 s (T-002) |

llama-cpp-python sizes its batch threads by the host CPU count, which oversubscribes a 2-vCPU container; `default_threads()` reads the cgroup quota.

## Prompt variant (local, 2 threads, `metrics/bench-v*-prompt-2t.json`)

| Prompt | Valid | Type | Priority | Warm median |
|---|---|---|---|---|
| v0: rubric + JSON schema | 100% | 90% | 90% | 10.9 s |
| v1: rubric, schema removed | 90% | 80% | 90% | 10.3 s |

Removing the schema saved no time (the rubric prefix is cached between calls) and cost quality: kept v0.

## Decision

`qwen3-4b`: the only candidate with usable quality, Apache-2.0, ~25–40 s per request on the free CPU (target 30 s, limit 60 s).
