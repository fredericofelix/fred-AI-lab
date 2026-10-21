"""Local open models behind the Extractor protocol. Candidates and the choice are recorded in SPIKE.md."""

from __future__ import annotations

from triage.extract import extraction_schema
from triage.rubric import Rubric, load_rubric

# key: (Hugging Face repo, GGUF file, system message)
CANDIDATES: dict[str, tuple[str, str, str | None]] = {
    "qwen3-4b": ("unsloth/Qwen3-4B-Instruct-2507-GGUF", "Qwen3-4B-Instruct-2507-Q4_K_M.gguf", None),
    "qwen3-1.7b": ("unsloth/Qwen3-1.7B-GGUF", "Qwen3-1.7B-Q4_K_M.gguf", "/no_think"),
    "phi-4-mini": ("unsloth/Phi-4-mini-instruct-GGUF", "Phi-4-mini-instruct-Q4_K_M.gguf", None),
    "gemma-3-4b": ("unsloth/gemma-3-4b-it-GGUF", "gemma-3-4b-it-Q4_K_M.gguf", None),
}
DEFAULT_MODEL = "qwen3-4b"  # provisional until the spike decides


class LlamaCppExtractor:
    """Runs a GGUF model on CPU with llama.cpp; JSON output constrained by the rubric's schema."""

    def __init__(
        self,
        repo_id: str,
        filename: str,
        name: str,
        system: str | None = None,
        rubric: Rubric | None = None,
        n_ctx: int = 4096,
        max_tokens: int = 512,
    ):
        self.name = name
        self._repo_id, self._filename, self._system = repo_id, filename, system
        self._schema = extraction_schema(rubric or load_rubric())
        self._n_ctx, self._max_tokens = n_ctx, max_tokens
        self._llm = None

    def _load(self):
        from llama_cpp import Llama  # heavy import, only when a model actually runs

        self._llm = Llama.from_pretrained(self._repo_id, self._filename, n_ctx=self._n_ctx, verbose=False)

    def __call__(self, prompt: str) -> str:
        if self._llm is None:
            self._load()
        messages = [{"role": "user", "content": prompt}]
        if self._system:
            messages.insert(0, {"role": "system", "content": self._system})
        out = self._llm.create_chat_completion(
            messages=messages,
            response_format={"type": "json_object", "schema": self._schema},
            temperature=0,
            max_tokens=self._max_tokens,
        )
        return out["choices"][0]["message"]["content"]


def get_extractor(name: str) -> LlamaCppExtractor:
    if name not in CANDIDATES:
        raise KeyError(f"unknown model {name!r}; known: {', '.join(CANDIDATES)}")
    repo_id, filename, system = CANDIDATES[name]
    return LlamaCppExtractor(repo_id, filename, name=name, system=system)
