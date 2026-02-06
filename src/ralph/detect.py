"""Promise completion detection."""


def detect_promise(text: str, phrase: str) -> bool:
    if not phrase:
        return False
    return f"<promise>{phrase}</promise>" in text
