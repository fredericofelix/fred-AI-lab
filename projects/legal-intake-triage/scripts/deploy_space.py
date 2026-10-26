"""Stage the app and the triage package into a temp dir and upload it to a Hugging Face Space.

Usage: python -m scripts.deploy_space --space lexseed/triagem-juridica [--spike]
"""

from __future__ import annotations

import argparse
import shutil
import tempfile
from pathlib import Path

from huggingface_hub import HfApi

ROOT = Path(__file__).resolve().parent.parent

SPIKE_README = """---
title: Lex Seed · Triagem (spike)
emoji: 🌱
colorFrom: yellow
colorTo: gray
sdk: gradio
sdk_version: 6.30.0
python_version: "3.12"
app_file: app.py
pinned: false
license: apache-2.0
short_description: Teste temporário para escolher o modelo da triagem
---

Space temporário, apagado depois da escolha do modelo. Não cole dados reais.
"""


def stage(dest: Path, spike: bool) -> None:
    shutil.copytree(ROOT / "triage", dest / "triage", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copy(ROOT / "rubric.yaml", dest / "rubric.yaml")
    shutil.copy(ROOT / "requirements-space.txt", dest / "requirements.txt")
    if spike:
        shutil.copy(ROOT / "space" / "spike_app.py", dest / "app.py")
        (dest / "README.md").write_text(SPIKE_README, encoding="utf-8")
        return
    for f in (ROOT / "space").iterdir():
        if f.is_file() and f.name != "spike_app.py":
            shutil.copy(f, dest / f.name)
    if (ROOT / "METRICS.md").exists():
        shutil.copy(ROOT / "METRICS.md", dest / "METRICS.md")
    if (ROOT / "assets").exists():
        shutil.copytree(ROOT / "assets", dest / "assets")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--space", required=True)
    parser.add_argument("--spike", action="store_true")
    args = parser.parse_args()

    api = HfApi()
    api.create_repo(args.space, repo_type="space", space_sdk="gradio", private=False, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        stage(Path(tmp), args.spike)
        api.upload_folder(folder_path=tmp, repo_id=args.space, repo_type="space", commit_message="deploy")
    print(f"https://huggingface.co/spaces/{args.space}")


if __name__ == "__main__":
    main()
