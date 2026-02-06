from ralph.detect import detect_promise


def test_matches_wrapped_promise():
    assert detect_promise("<promise>I'm done!</promise>", "I'm done!") is True


def test_case_sensitive():
    assert detect_promise("<promise>IM DONE!</promise>", "I'm done!") is False


def test_empty_phrase_returns_false():
    assert detect_promise("done", "") is False


def test_phrase_without_tags_returns_false():
    assert detect_promise("I'm done!", "I'm done!") is False


def test_partial_tag_returns_false():
    assert detect_promise("<promise>I'm done!", "I'm done!") is False


def test_promise_embedded_in_text():
    text = "All tasks finished.\n<promise>任務完成！🥇</promise>"
    assert detect_promise(text, "任務完成！🥇") is True
