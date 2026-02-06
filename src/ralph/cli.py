"""CLI interface for Ralph Any."""

from __future__ import annotations

import argparse
import asyncio
import shlex
import sys
from pathlib import Path
from typing import Any

from ralph.config import load_config_file
from ralph.engine import LoopConfig, RalphEngine

EXIT_SUCCESS = 0
EXIT_FAILED = 1
EXIT_CANCELLED = 2
EXIT_TIMEOUT = 3
EXIT_MAX_ITERATIONS = 4

_STATE_TO_EXIT = {
    "complete": EXIT_SUCCESS,
    "failed": EXIT_FAILED,
    "cancelled": EXIT_CANCELLED,
    "timeout": EXIT_TIMEOUT,
    "max_iterations": EXIT_MAX_ITERATIONS,
}

# Auto-detected prompt files, checked in order.
_AUTO_PROMPT_FILES = ("ralph.md", "TASK.md", "ralph.txt", "TASK.txt")


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="ralph",
        description="Ralph Wiggum Loop — iterative AI dev loop via ACP",
    )
    p.add_argument(
        "prompt",
        nargs="?",
        default=None,
        help="Task description, or path to a .md/.txt file (auto-detects ralph.md / TASK.md)",
    )
    p.add_argument(
        "-m", "--max-iterations",
        type=int,
        default=None,
        help="Maximum loop iterations (default: 10)",
    )
    p.add_argument(
        "-t", "--timeout",
        type=int,
        default=None,
        help="Maximum runtime in seconds (default: 1800 = 30m)",
    )
    p.add_argument(
        "--promise",
        default=None,
        help="Completion promise phrase (default: 任務完成！🥇)",
    )
    p.add_argument(
        "-c", "--command",
        default=None,
        help="ACP CLI command (default: claude-code-acp)",
    )
    p.add_argument(
        "--command-args",
        default=None,
        help="Extra arguments for the ACP CLI (e.g. '--experimental-acp')",
    )
    p.add_argument(
        "-d", "--working-dir",
        default=None,
        help="Working directory (default: .)",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Show config without running",
    )
    return p


def _resolve_prompt(raw: str) -> str:
    """If ``raw`` is a path to an existing .md or .txt file, read it."""
    p = Path(raw)
    if p.is_file() and p.suffix in (".md", ".txt"):
        return p.read_text(encoding="utf-8")
    return raw


def _auto_detect_prompt(working_dir: str) -> str | None:
    """Look for a default prompt file in the working directory."""
    base = Path(working_dir)
    for name in _AUTO_PROMPT_FILES:
        p = base / name
        if p.is_file():
            print(f"📄 Auto-detected prompt file: {p}", flush=True)
            return p.read_text(encoding="utf-8")
    return None


def _run(config: LoopConfig) -> int:
    engine = RalphEngine(config)
    try:
        result = asyncio.run(engine.run())
    except KeyboardInterrupt:
        print("\n⚠ Loop cancelled", flush=True)
        return EXIT_CANCELLED

    duration = f"{result.duration_seconds:.1f}s"
    print(f"\n▶ Result: {result.state} ({result.iterations} iterations, {duration})")

    return _STATE_TO_EXIT.get(result.state, EXIT_FAILED)


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    # Layer 1: defaults
    cfg: dict[str, Any] = {
        "prompt": None,
        "promise_phrase": "任務完成！🥇",
        "command": "claude-code-acp",
        "command_args": [],
        "working_dir": ".",
        "max_iterations": 10,
        "timeout_seconds": 1800,
        "dry_run": False,
    }

    # Layer 2: ralph.yml (overrides defaults)
    file_cfg = load_config_file(args.working_dir or ".")
    if file_cfg:
        cfg.update({k: v for k, v in file_cfg.items() if v is not None})

    # Layer 3: CLI args (overrides config file)
    if args.prompt is not None:
        cfg["prompt"] = _resolve_prompt(args.prompt)
    if args.max_iterations is not None:
        cfg["max_iterations"] = args.max_iterations
    if args.timeout is not None:
        cfg["timeout_seconds"] = args.timeout
    if args.promise is not None:
        cfg["promise_phrase"] = args.promise
    if args.command is not None:
        cfg["command"] = args.command
    if args.command_args is not None:
        cfg["command_args"] = shlex.split(args.command_args)
    if args.working_dir is not None:
        cfg["working_dir"] = args.working_dir
    if args.dry_run:
        cfg["dry_run"] = True

    # Auto-detect prompt file if no prompt given
    if cfg["prompt"] is None:
        cfg["prompt"] = _auto_detect_prompt(cfg["working_dir"])

    if cfg["prompt"] is None:
        parser.error("prompt is required (provide as argument or create ralph.md / TASK.md)")

    config = LoopConfig(**cfg)

    if config.dry_run:
        print("Dry-run config:")
        for k, v in vars(config).items():
            print(f"  {k}: {v}")
        sys.exit(EXIT_SUCCESS)

    sys.exit(_run(config))
