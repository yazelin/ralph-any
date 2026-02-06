"""Ralph Any — iterative AI dev loop via ACP."""

__version__ = "0.1.0"

from ralph.detect import detect_promise
from ralph.engine import LoopConfig, LoopResult, RalphEngine

__all__ = [
    "__version__",
    "detect_promise",
    "LoopConfig",
    "LoopResult",
    "RalphEngine",
]
