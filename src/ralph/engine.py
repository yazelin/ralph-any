"""Ralph Loop engine — the core iteration loop over any ACP-compatible agent."""

from __future__ import annotations

import asyncio
import sys
import time
from dataclasses import dataclass, field
from typing import Literal

from claude_code_acp import AcpClient

from ralph.detect import detect_promise
from ralph.prompt import build_system_prompt

LoopState = Literal["complete", "failed", "cancelled", "timeout", "max_iterations"]


@dataclass
class LoopConfig:
    prompt: str
    promise_phrase: str = "任務完成！🥇"
    command: str = "claude-code-acp"
    command_args: list[str] = field(default_factory=list)
    working_dir: str = "."
    max_iterations: int = 10
    timeout_seconds: int = 1800  # 30 minutes
    dry_run: bool = False


@dataclass
class LoopResult:
    state: LoopState
    iterations: int
    duration_seconds: float
    error: str | None = None


class RalphEngine:
    def __init__(self, config: LoopConfig) -> None:
        self.config = config
        self.client = AcpClient(
            command=config.command,
            args=config.command_args or None,
            cwd=config.working_dir,
        )
        self._register_events()

    def _register_events(self) -> None:
        client = self.client

        @client.on_text
        async def on_text(text: str) -> None:
            sys.stdout.write(text)
            sys.stdout.flush()

        @client.on_tool_start
        async def on_tool_start(tool_id: str, name: str, input: dict) -> None:
            print(f"\n🛠️  {name}", flush=True)

        @client.on_tool_end
        async def on_tool_end(tool_id: str, status: str, output: object) -> None:
            icon = "✔️" if status == "completed" else "❌"
            print(f" {icon} {status}", flush=True)

        @client.on_error
        async def on_error(exception: Exception) -> None:
            print(f"\n⚠️  Error: {exception}", file=sys.stderr, flush=True)

    async def run(self) -> LoopResult:
        config = self.config
        system_prompt = build_system_prompt(config.promise_phrase)
        start = time.monotonic()

        async with self.client:
            await self.client.prompt(f"/system {system_prompt}")

            for i in range(1, config.max_iterations + 1):
                elapsed = time.monotonic() - start
                if elapsed >= config.timeout_seconds:
                    return LoopResult(
                        state="timeout",
                        iterations=i - 1,
                        duration_seconds=elapsed,
                    )

                print(f"\n━━━ Iteration {i}/{config.max_iterations} ━━━", flush=True)

                prompt = (
                    f"[Iteration {i}/{config.max_iterations}]\n\n{config.prompt}"
                )

                try:
                    response = await asyncio.wait_for(
                        self.client.prompt(prompt),
                        timeout=max(0, config.timeout_seconds - elapsed),
                    )
                except asyncio.TimeoutError:
                    return LoopResult(
                        state="timeout",
                        iterations=i,
                        duration_seconds=time.monotonic() - start,
                    )

                if detect_promise(response, config.promise_phrase):
                    print(
                        f"\n🎉 Promise detected: \"{config.promise_phrase}\"",
                        flush=True,
                    )
                    return LoopResult(
                        state="complete",
                        iterations=i,
                        duration_seconds=time.monotonic() - start,
                    )

                print(f"\n✓ Iteration {i} complete", flush=True)

        return LoopResult(
            state="max_iterations",
            iterations=config.max_iterations,
            duration_seconds=time.monotonic() - start,
        )
