"""Local open models behind the Extractor protocol. Candidates and the choice are recorded in SPIKE.md."""

from __future__ import annotations

import os
import threading
import time
from pathlib import Path

from huggingface_hub import hf_hub_download

from triage.extract import extraction_schema
from triage.rubric import Rubric, load_rubric

CGROUP_CPU_MAX = Path("/sys/fs/cgroup/cpu.max")


def default_threads(cgroup_cpu_max: Path = CGROUP_CPU_MAX) -> int:
    """CPUs this process may really use: TRIAGE_THREADS, else the container quota, else cpu_count."""
    if os.environ.get("TRIAGE_THREADS"):
        return int(os.environ["TRIAGE_THREADS"])
    try:
        quota, period = cgroup_cpu_max.read_text().split()
        if quota != "max":
            return max(1, int(quota) // int(period))
    except (OSError, ValueError):
        pass
    return os.cpu_count() or 1


# key: (Hugging Face repo, GGUF file, system message, pinned revision or None)
# The default model is pinned, so an upstream change cannot swap the file under the Space.
CANDIDATES: dict[str, tuple[str, str, str | None, str | None]] = {
    "qwen3-4b": (
        "unsloth/Qwen3-4B-Instruct-2507-GGUF",
        "Qwen3-4B-Instruct-2507-Q4_K_M.gguf",
        None,
        "a06e946bb6b655725eafa393f4a9745d460374c9",
    ),
    "qwen3-1.7b": ("unsloth/Qwen3-1.7B-GGUF", "Qwen3-1.7B-Q4_K_M.gguf", "/no_think", None),
    "phi-4-mini": ("unsloth/Phi-4-mini-instruct-GGUF", "Phi-4-mini-instruct-Q4_K_M.gguf", None, None),
    "gemma-3-4b": ("unsloth/gemma-3-4b-it-GGUF", "gemma-3-4b-it-Q4_K_M.gguf", None, None),
}
DEFAULT_MODEL = "qwen3-4b"  # chosen by the spike, see SPIKE.md


class LlamaCppExtractor:
    """Runs a GGUF model on CPU with llama.cpp; JSON output constrained by the rubric's schema."""

    def __init__(
        self,
        repo_id: str,
        filename: str,
        name: str,
        system: str | None = None,
        revision: str | None = None,
        rubric: Rubric | None = None,
        n_ctx: int = 4096,
        max_tokens: int = 512,
        timeout_s: float = 90.0,
    ):
        self.name = name
        self._repo_id, self._filename, self._system = repo_id, filename, system
        self._revision = revision
        self._schema = extraction_schema(rubric or load_rubric())
        self._n_ctx, self._max_tokens = n_ctx, max_tokens
        self._timeout_s = timeout_s
        self._llm = None
        self._ready = False
        self._busy_since: float | None = None  # monotonic time the model was taken, for the watchdog
        # One llama.cpp instance is not thread-safe: load once, run one request at a time.
        self._lock = threading.Lock()

    @property
    def loaded(self) -> bool:
        return self._llm is not None

    @property
    def ready(self) -> bool:
        """Weights loaded and the rubric prefix primed: the next request skips the slow part."""
        return self._ready

    def _load(self):
        from llama_cpp import Llama  # heavy import, only when a model actually runs

        threads = default_threads()
        path = hf_hub_download(self._repo_id, self._filename, revision=self._revision)
        # use_mmap=False keeps the weights in RAM: after a long idle the host can drop mmap'd pages,
        # and re-reading 2.5 GB on the first request was the suspect of the 2026-10-23 hang.
        self._llm = Llama(
            model_path=path,
            n_ctx=self._n_ctx,
            n_threads=threads,
            n_threads_batch=threads,
            use_mmap=False,
            verbose=False,
        )

    def __call__(self, prompt: str) -> str:
        # Waiting for the model counts against the time limit, so a stuck call cannot queue visitors forever.
        if not self._lock.acquire(timeout=self._timeout_s):
            raise TimeoutError(f"model busy for more than {self._timeout_s:.0f} s")
        self._busy_since = time.monotonic()
        try:
            if self._llm is None:
                self._load()
            return self._complete(prompt)
        finally:
            self._busy_since = None
            self._lock.release()

    def warm_up(self, prefix_prompt: str) -> None:
        """Load the weights and prime llama.cpp's prefix cache with the rubric, generating one token."""
        with self._lock:
            self._busy_since = time.monotonic()
            try:
                if self._llm is None:
                    self._load()
                self._llm.create_chat_completion(messages=self._messages(prefix_prompt), max_tokens=1, temperature=0)
                self._ready = True
            finally:
                self._busy_since = None

    def check_watchdog(self, limit_s: float) -> None:
        """Exit the process if one call holds the model too long; Hugging Face restarts the Space."""
        since = self._busy_since
        if since is not None and time.monotonic() - since > limit_s:
            print(f"watchdog: model busy for more than {limit_s:.0f} s, restarting", flush=True)
            os._exit(1)

    def _messages(self, prompt: str) -> list[dict]:
        messages = [{"role": "user", "content": prompt}]
        if self._system:
            messages.insert(0, {"role": "system", "content": self._system})
        return messages

    def _complete(self, prompt: str) -> str:
        messages = self._messages(prompt)
        deadline = time.monotonic() + self._timeout_s
        stream = self._llm.create_chat_completion(
            messages=messages,
            response_format={"type": "json_object", "schema": self._schema},
            temperature=0,
            max_tokens=self._max_tokens,
            stream=True,  # token by token, so a slow request can be cut at the deadline
        )
        parts = []
        for chunk in stream:
            parts.append(chunk["choices"][0]["delta"].get("content") or "")
            if time.monotonic() > deadline:
                stream.close()  # stops generation and frees the model for the next visitor
                raise TimeoutError(f"no answer within {self._timeout_s:.0f} s")
        return "".join(parts)


def get_extractor(name: str) -> LlamaCppExtractor:
    if name not in CANDIDATES:
        raise KeyError(f"unknown model {name!r}; known: {', '.join(CANDIDATES)}")
    repo_id, filename, system, revision = CANDIDATES[name]
    return LlamaCppExtractor(repo_id, filename, name=name, system=system, revision=revision)
