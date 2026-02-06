"""Engine tests using a mock AcpClient."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ralph.engine import LoopConfig, LoopResult, RalphEngine


def _config(**overrides) -> LoopConfig:
    defaults = dict(
        prompt="test prompt",
        promise_phrase="DONE",
        command="echo",
        command_args=[],
        working_dir=".",
        max_iterations=3,
        timeout_seconds=60,
        dry_run=False,
    )
    defaults.update(overrides)
    return LoopConfig(**defaults)


class FakeAcpClient:
    """Minimal mock that mimics AcpClient's async context manager + prompt."""

    def __init__(self, responses: list[str] | None = None) -> None:
        self._responses = list(responses or ["no progress"])
        self._call_count = 0
        # Stubs for event decorators
        self.on_text = lambda fn: fn
        self.on_tool_start = lambda fn: fn
        self.on_tool_end = lambda fn: fn
        self.on_error = lambda fn: fn

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        pass

    async def prompt(self, text: str) -> str:
        # Skip system prompt call
        if text.startswith("/system "):
            return "ok"
        idx = min(self._call_count, len(self._responses) - 1)
        resp = self._responses[idx]
        self._call_count += 1
        return resp


@patch("ralph.engine.AcpClient")
def test_complete_on_promise(mock_cls):
    fake = FakeAcpClient(["working...", "<promise>DONE</promise>"])
    mock_cls.return_value = fake

    config = _config(max_iterations=5)
    engine = RalphEngine(config)
    engine.client = fake

    result = asyncio.run(engine.run())
    assert result.state == "complete"
    assert result.iterations == 2


@patch("ralph.engine.AcpClient")
def test_max_iterations(mock_cls):
    fake = FakeAcpClient(["still working..."])
    mock_cls.return_value = fake

    config = _config(max_iterations=3)
    engine = RalphEngine(config)
    engine.client = fake

    result = asyncio.run(engine.run())
    assert result.state == "max_iterations"
    assert result.iterations == 3


@patch("ralph.engine.AcpClient")
def test_timeout(mock_cls):
    async def slow_prompt(text: str) -> str:
        if text.startswith("/system "):
            return "ok"
        await asyncio.sleep(5)
        return "never"

    fake = FakeAcpClient()
    fake.prompt = slow_prompt  # type: ignore[assignment]
    mock_cls.return_value = fake

    config = _config(max_iterations=10, timeout_seconds=1)
    engine = RalphEngine(config)
    engine.client = fake

    result = asyncio.run(engine.run())
    assert result.state == "timeout"


@patch("ralph.engine.AcpClient")
def test_first_iteration_complete(mock_cls):
    fake = FakeAcpClient(["<promise>DONE</promise>"])
    mock_cls.return_value = fake

    config = _config(max_iterations=10)
    engine = RalphEngine(config)
    engine.client = fake

    result = asyncio.run(engine.run())
    assert result.state == "complete"
    assert result.iterations == 1
    assert result.duration_seconds >= 0
