import re
from pathlib import Path

REQ = (Path(__file__).resolve().parent.parent / "requirements-space.txt").read_text(encoding="utf-8")
LINES = [line.strip() for line in REQ.splitlines() if line.strip() and not line.startswith("#")]


def test_no_extra_package_index():
    assert not any(line.startswith(("--extra-index-url", "--index-url", "-i ")) for line in LINES)


def test_every_requirement_pinned():
    for line in LINES:
        if " @ " in line:
            assert re.search(r"#sha256=[0-9a-f]{64}$", line), line
        else:
            assert "==" in line, line
