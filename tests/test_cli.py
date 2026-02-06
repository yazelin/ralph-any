"""Tests for CLI prompt resolution and auto-detection."""

from pathlib import Path
from unittest.mock import patch

import pytest

from ralph.cli import _auto_detect_prompt, _resolve_prompt


def test_resolve_prompt_plain_text():
    assert _resolve_prompt("do something") == "do something"


def test_resolve_prompt_reads_md_file(tmp_path: Path):
    f = tmp_path / "task.md"
    f.write_text("# Task\nDo this.")
    assert _resolve_prompt(str(f)) == "# Task\nDo this."


def test_resolve_prompt_reads_txt_file(tmp_path: Path):
    f = tmp_path / "task.txt"
    f.write_text("hello")
    assert _resolve_prompt(str(f)) == "hello"


def test_auto_detect_ralph_md(tmp_path: Path):
    (tmp_path / "ralph.md").write_text("auto task")
    result = _auto_detect_prompt(str(tmp_path))
    assert result == "auto task"


def test_auto_detect_task_md(tmp_path: Path):
    (tmp_path / "TASK.md").write_text("task file")
    result = _auto_detect_prompt(str(tmp_path))
    assert result == "task file"


def test_auto_detect_priority(tmp_path: Path):
    (tmp_path / "ralph.md").write_text("ralph wins")
    (tmp_path / "TASK.md").write_text("task loses")
    result = _auto_detect_prompt(str(tmp_path))
    assert result == "ralph wins"


def test_auto_detect_none(tmp_path: Path):
    result = _auto_detect_prompt(str(tmp_path))
    assert result is None
