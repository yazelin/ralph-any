"""Load ralph.yml config file."""

from __future__ import annotations

import shlex
from pathlib import Path
from typing import Any


def load_config_file(working_dir: str) -> dict[str, Any] | None:
    """Load ralph.yml / ralph.yaml from *working_dir*. Returns None if absent."""
    base = Path(working_dir)
    for name in ("ralph.yml", "ralph.yaml"):
        path = base / name
        if path.is_file():
            return _parse(path)
    return None


def _parse(path: Path) -> dict[str, Any]:
    """Parse a ralph config file (simple YAML subset, no dependency needed)."""
    raw: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        raw[key.strip()] = value.strip()

    cfg: dict[str, Any] = {}

    _map = {
        "command": "command",
        "command_args": "command_args",
        "promise": "promise_phrase",
        "max_iterations": "max_iterations",
        "timeout": "timeout_seconds",
        "working_dir": "working_dir",
        "prompt": "prompt",
    }

    for yaml_key, cfg_key in _map.items():
        if yaml_key not in raw:
            continue
        val = raw[yaml_key]
        if cfg_key in ("max_iterations", "timeout_seconds"):
            cfg[cfg_key] = int(val)
        elif cfg_key == "command_args":
            cfg[cfg_key] = shlex.split(val)
        else:
            cfg[cfg_key] = val

    return cfg
