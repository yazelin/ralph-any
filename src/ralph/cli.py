"""CLI interface for Ralph Any."""

from __future__ import annotations

import argparse
import asyncio
import shlex
import sys
from pathlib import Path

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


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="ralph",
        description="Ralph Wiggum Loop — iterative AI dev loop via ACP",
    )
    p.add_argument(
        "prompt",
        help="Task description, or path to a .md/.txt file",
    )
    p.add_argument(
        "-m", "--max-iterations",
        type=int,
        default=10,
        help="Maximum loop iterations (default: 10)",
    )
    p.add_argument(
        "-t", "--timeout",
        type=int,
        default=1800,
        help="Maximum runtime in seconds (default: 1800 = 30m)",
    )
    p.add_argument(
        "--promise",
        default="任務完成！🥇",
        help="Completion promise phrase (default: 任務完成！🥇)",
    )
    p.add_argument(
        "-c", "--command",
        default="claude-code-acp",
        help="ACP CLI command (default: claude-code-acp)",
    )
    p.add_argument(
        "--command-args",
        default="",
        help="Extra arguments for the ACP CLI (e.g. '--experimental-acp')",
    )
    p.add_argument(
        "-d", "--working-dir",
        default=".",
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

    prompt_text = _resolve_prompt(args.prompt)

    config = LoopConfig(
        prompt=prompt_text,
        promise_phrase=args.promise,
        command=args.command,
        command_args=shlex.split(args.command_args) if args.command_args else [],
        working_dir=args.working_dir,
        max_iterations=args.max_iterations,
        timeout_seconds=args.timeout,
        dry_run=args.dry_run,
    )

    if config.dry_run:
        print("Dry-run config:")
        for k, v in vars(config).items():
            print(f"  {k}: {v}")
        sys.exit(EXIT_SUCCESS)

    sys.exit(_run(config))
