"""examples/headless_pipeline.py: imports without Streamlit; approvals answered in code."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

from streamlit_coco.conversation import Conversation
from streamlit_coco.policy import FolderPolicy
from streamlit_coco.testing.scripted import ScriptedAgent

EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "headless_pipeline.py"


def _load():
    spec = importlib.util.spec_from_file_location("headless_pipeline", EXAMPLE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_example_imports_without_streamlit() -> None:
    code = (
        "import runpy, sys; runpy.run_path(sys.argv[1], run_name='x');"
        "assert 'streamlit' not in sys.modules; print('ok')"
    )
    done = subprocess.run(
        [sys.executable, "-c", code, str(EXAMPLE)], capture_output=True, text=True, check=False
    )
    assert done.returncode == 0 and "ok" in done.stdout, done.stderr


def _conversation(tmp_path: Path) -> Conversation:
    (tmp_path / "README.md").write_text("# Alpha\n", encoding="utf-8")
    return Conversation(
        tmp_path,
        policy=FolderPolicy(tmp_path),
        agent=lambda emit: ScriptedAgent(emit, delay=0, connect_delay=0),
    )


def test_approvals_are_answered_in_code(tmp_path: Path) -> None:
    pipeline = _load()
    conv = _conversation(tmp_path)
    try:
        pipeline.connect(conv, timeout=20)
        asked: list[dict] = []

        def decide(request: dict) -> bool:
            asked.append(request)
            return False

        thread = pipeline.run_with_approvals(conv, "write a note", decide, timeout=20)
        assert [r["kind"] for r in asked] == ["change"]
        assert not (tmp_path / "coco_note.md").exists()  # declined: nothing was written
        assert any(i["kind"] == "answer" for i in thread)

        pipeline.run_with_approvals(conv, "write a note", lambda request: True, timeout=20)
        assert (tmp_path / "coco_note.md").exists()
    finally:
        conv.close()
