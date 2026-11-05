"""Local model passes behind the ModelPass protocol. Candidates and the choice are recorded in SPIKE.md."""

from __future__ import annotations

import os
import threading
import time
from pathlib import Path

from guardrail.model_pass import ModelSpan, build_prompt, output_schema, parse_llm_output
from guardrail.rubric import Rubric, load_rubric

# GLiNER2 zero-shot labels (PT) → (group, kind). The model is the one privacyseed-lgpd[ml] already loads.
GLINER_LABELS: dict[str, tuple[int, str]] = {
    "empresa ou organização": (1, "org"),
    "valor de acordo ou proposta": (3, "amount"),
    "tese ou estratégia jurídica": (3, "clause"),
    "informação confidencial de terceiro": (5, "third_party"),
}
GLINER_ORG_ONLY = {k: v for k, v in GLINER_LABELS.items() if v == (1, "org")}
GLINER_THRESHOLD = 0.5

# Qwen3-4B GGUF, pinned revision (same file as the triage Space).
QWEN_REPO = "unsloth/Qwen3-4B-Instruct-2507-GGUF"
QWEN_FILE = "Qwen3-4B-Instruct-2507-Q4_K_M.gguf"
QWEN_REVISION = "a06e946bb6b655725eafa393f4a9745d460374c9"

CGROUP_CPU_MAX = Path("/sys/fs/cgroup/cpu.max")


def default_threads(cgroup_cpu_max: Path = CGROUP_CPU_MAX) -> int:
    """CPUs this process may really use: GUARDRAIL_THREADS, else the container quota, else cpu_count."""
    if os.environ.get("GUARDRAIL_THREADS"):
        return int(os.environ["GUARDRAIL_THREADS"])
    try:
        quota, period = cgroup_cpu_max.read_text().split()
        if quota != "max":
            return max(1, int(quota) // int(period))
    except (OSError, ValueError):
        pass
    return os.cpu_count() or 1


class GlinerPass:
    def __init__(
        self,
        model=None,
        labels: dict[str, tuple[int, str]] = GLINER_LABELS,
        name: str = "gliner",
        threshold: float = GLINER_THRESHOLD,
    ):
        self.name = name
        self._model = model
        self._labels = labels
        self._threshold = threshold

    def __call__(self, text: str) -> list[ModelSpan]:
        # privacyseed-lgpd's loader and offset check (private API; safe because the version is pinned)
        from privacyseed_lgpd.recognizers._model import extract, load_model

        if self._model is None:
            self._model = load_model()
        spans = extract(self._model, text, list(self._labels), self._threshold)
        found = [
            (start, *self._labels[label], text[start:end]) for label, start, end, _ in spans if label in self._labels
        ]
        return [ModelSpan(group, kind, span) for _, group, kind, span in sorted(found)]


class LlamaPass:
    """Qwen3-4B on CPU with llama.cpp; JSON constrained by the output schema; one request at a time."""

    def __init__(
        self,
        name: str = "qwen3-4b",
        rubric: Rubric | None = None,
        n_ctx: int = 4096,
        max_tokens: int = 512,
        timeout_s: float = 90.0,
    ):
        self.name = name
        self._rubric = rubric or load_rubric()
        self._n_ctx, self._max_tokens, self._timeout_s = n_ctx, max_tokens, timeout_s
        self._llm = None
        self._busy_since: float | None = None  # for the Space watchdog
        self._lock = threading.Lock()  # one llama.cpp instance is not thread-safe

    def _load(self) -> None:
        from huggingface_hub import hf_hub_download
        from llama_cpp import Llama  # heavy import, only when the model actually runs

        threads = default_threads()
        path = hf_hub_download(QWEN_REPO, QWEN_FILE, revision=QWEN_REVISION)
        # use_mmap=False keeps weights in RAM (lesson from the triage's 2026-10-23 hang)
        self._llm = Llama(
            model_path=path,
            n_ctx=self._n_ctx,
            n_threads=threads,
            n_threads_batch=threads,
            use_mmap=False,
            verbose=False,
        )

    def __call__(self, text: str) -> list[ModelSpan]:
        if not self._lock.acquire(timeout=self._timeout_s):
            raise TimeoutError(f"model busy for more than {self._timeout_s:.0f} s")
        self._busy_since = time.monotonic()
        try:
            if self._llm is None:
                self._load()
            return parse_llm_output(self._complete(build_prompt(text, self._rubric)))
        finally:
            self._busy_since = None
            self._lock.release()

    def check_watchdog(self, limit_s: float) -> None:
        """Exit the process if one call holds the model too long; Hugging Face restarts the Space."""
        since = self._busy_since
        if since is not None and time.monotonic() - since > limit_s:
            print(f"watchdog: model busy for more than {limit_s:.0f} s, restarting", flush=True)
            os._exit(1)

    def _complete(self, prompt: str) -> str:
        deadline = time.monotonic() + self._timeout_s
        stream = self._llm.create_chat_completion(
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object", "schema": output_schema()},
            temperature=0,
            max_tokens=self._max_tokens,
            stream=True,  # token by token, so a slow request can be cut at the deadline
        )
        parts = []
        for chunk in stream:
            parts.append(chunk["choices"][0]["delta"].get("content") or "")
            if time.monotonic() > deadline:
                stream.close()
                raise TimeoutError(f"no answer within {self._timeout_s:.0f} s")
        return "".join(parts)


class HybridPass:
    """Companies from GLiNER2 (fast), strategy and third-party information from the LLM."""

    def __init__(self, gliner: GlinerPass, llm, name: str = "hybrid"):
        self.name = name
        self._gliner, self._llm = gliner, llm

    def __call__(self, text: str) -> list[ModelSpan]:
        orgs = [s for s in self._gliner(text) if s.group == 1]
        rest = [s for s in self._llm(text) if s.group != 1]
        return orgs + rest


CANDIDATES = ("gliner", "qwen3-4b", "hybrid")
DEFAULT_MODEL_PASS = "hybrid"  # provisional until the spike decides, see SPIKE.md


def get_model_pass(name: str):
    if name == "gliner":
        return GlinerPass()
    if name == "qwen3-4b":
        return LlamaPass()
    if name == "hybrid":
        return HybridPass(GlinerPass(labels=GLINER_ORG_ONLY, name="gliner-org"), LlamaPass())
    raise ValueError(f"unknown model pass {name!r}; known: {', '.join(CANDIDATES)}")
