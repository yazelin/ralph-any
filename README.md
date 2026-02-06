# ralph-any

Ralph Wiggum Loop — iterative AI dev loop via ACP (supports Claude, Gemini, and more).

Powered by [`claude-code-acp`](https://github.com/yazelin/claude-code-acp-py)'s `AcpClient`, `ralph-any` can drive **any** ACP-compatible AI CLI in an autonomous loop until the task is done.

## Install

```bash
pip install ralph-any
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv tool install ralph-any
```

## Quick Start

```bash
# Claude Code (default)
ralph "Refactor utils.py to use dataclasses"

# Gemini CLI
ralph "Fix the failing tests" --command gemini --command-args --experimental-acp

# Read task from a file
ralph task.md -m 20
```

## CLI Usage

```
ralph <prompt> [options]
```

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `prompt` | | *(required)* | Task description, or path to `.md`/`.txt` file |
| `--max-iterations` | `-m` | `10` | Maximum loop iterations |
| `--timeout` | `-t` | `1800` | Maximum runtime in seconds (30 min) |
| `--promise` | | `任務完成！🥇` | Completion phrase the AI must output |
| `--command` | `-c` | `claude-code-acp` | ACP CLI command |
| `--command-args` | | | Extra arguments for the ACP CLI |
| `--working-dir` | `-d` | `.` | Working directory |
| `--dry-run` | | | Show config without running |

## How It Works

1. Ralph sends your prompt to an ACP-compatible AI agent
2. Each iteration, the AI sees the current repo state and makes progress
3. When done, the AI outputs a `<promise>` tag with the completion phrase
4. Ralph detects the promise and exits with code `0`

If the AI doesn't finish within `--max-iterations`, Ralph exits with code `4`.

### Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Complete (promise detected) |
| `1` | Failed |
| `2` | Cancelled (Ctrl+C) |
| `3` | Timeout |
| `4` | Max iterations reached |

## Tested Agents

### Claude Code (via `claude-code-acp`)

```bash
ralph "在當前目錄建立 hello.py，內容為 print('Hello from Ralph!')" -m 3
```

```
━━━ Iteration 1/3 ━━━

🛠️  Write hello.py
 ✔️ completed

🛠️  Read hello.py
 ✔️ completed

🛠️  Run: python3 hello.py
 ✔️ completed

<promise>任務完成！🥇</promise>
🎉 Promise detected: "任務完成！🥇"

▶ Result: complete (1 iterations, 22.6s)
```

### Gemini CLI (via `--experimental-acp`)

```bash
ralph "在當前目錄建立 hello.py，內容為 print('Hello from Ralph!')" -m 3 \
  --command gemini --command-args="--experimental-acp"
```

```
━━━ Iteration 1/3 ━━━

I will create the `hello.py` file with the specified content.
 ✔️ completed

<promise>任務完成！🥇</promise>
🎉 Promise detected: "任務完成！🥇"

▶ Result: complete (1 iterations, 58.6s)
```

Both agents completed the task in 1 iteration with promise detection working correctly.

## Using Your Own API Key (BYOK)

ralph-any doesn't handle API keys — authentication is managed by the ACP CLI you choose. Just set the environment variable as you normally would for that CLI:

```bash
# Claude (subscription — no key needed)
claude /login
ralph "Build a REST API"

# Claude (BYOK)
export ANTHROPIC_API_KEY=sk-xxx
ralph "Build a REST API"

# Gemini (BYOK)
export GEMINI_API_KEY=xxx
ralph "Build a REST API" --command gemini --command-args="--experimental-acp"
```

Environment variables are automatically inherited by the child process — no extra config needed.

## Architecture

6 core files, ported from [copilot-ralph](https://github.com/yazelin/copilot-ralph) (19+ TS files):

```
src/ralph/
├── __init__.py    # Version + exports
├── __main__.py    # python -m ralph entry
├── cli.py         # argparse CLI (8 options)
├── engine.py      # Ralph Loop engine (AcpClient)
├── prompt.py      # System prompt template
└── detect.py      # Promise detection (~5 lines)
```

| Aspect | copilot-ralph (TS) | ralph-any (Py) |
|--------|-------------------|----------------|
| Source lines | 2,065 | 328 |
| Files | 19+ | 6 |
| AI Backend | Copilot SDK (single) | AcpClient (any ACP CLI) |
| SDK wrapper | 651 lines (custom) | 0 (delegates to AcpClient) |
| Event system | 12 event types + AsyncQueue | 5 decorators |
| Retry logic | Custom 3x exponential backoff | Built into AcpClient |
| CLI params | 18+ (incl. Azure BYOK) | 8 (provider config via ACP CLI) |
| BYOK | 6 CLI params for Azure | env vars (handled by ACP CLI) |
| Multi-AI | No | Yes (Claude, Gemini, any ACP) |
| Dependencies | 9 | 2 |

## Development

```bash
git clone https://github.com/yazelin/ralph-any.git
cd ralph-any
uv sync --dev
uv run pytest -v
```

## License

MIT
