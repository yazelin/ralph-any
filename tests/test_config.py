"""Tests for ralph.yml config loading."""

from pathlib import Path

from ralph.config import load_config_file


def test_load_full_config(tmp_path: Path):
    (tmp_path / "ralph.yml").write_text(
        "command: gemini\n"
        "command_args: --experimental-acp\n"
        "max_iterations: 20\n"
        "timeout: 3600\n"
        "promise: done!\n"
    )
    cfg = load_config_file(str(tmp_path))
    assert cfg is not None
    assert cfg["command"] == "gemini"
    assert cfg["command_args"] == ["--experimental-acp"]
    assert cfg["max_iterations"] == 20
    assert cfg["timeout_seconds"] == 3600
    assert cfg["promise_phrase"] == "done!"


def test_load_yaml_extension(tmp_path: Path):
    (tmp_path / "ralph.yaml").write_text("command: gemini\n")
    cfg = load_config_file(str(tmp_path))
    assert cfg is not None
    assert cfg["command"] == "gemini"


def test_missing_config_returns_none(tmp_path: Path):
    cfg = load_config_file(str(tmp_path))
    assert cfg is None


def test_comments_and_blanks(tmp_path: Path):
    (tmp_path / "ralph.yml").write_text(
        "# Ralph config\n"
        "\n"
        "command: gemini\n"
        "# max_iterations: 5\n"
    )
    cfg = load_config_file(str(tmp_path))
    assert cfg == {"command": "gemini"}


def test_partial_config(tmp_path: Path):
    (tmp_path / "ralph.yml").write_text("max_iterations: 50\n")
    cfg = load_config_file(str(tmp_path))
    assert cfg == {"max_iterations": 50}
