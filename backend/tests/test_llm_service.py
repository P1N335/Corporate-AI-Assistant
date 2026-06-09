"""Тесты вспомогательной логики LLM-сервиса."""

from app.services.llm_service import _strip_thinking


def test_strip_thinking_removes_block():
    assert _strip_thinking("<think>рассуждения</think>Ответ") == "Ответ"


def test_strip_thinking_multiline():
    text = "<think>line1\nline2</think>  Финал"
    assert _strip_thinking(text) == "Финал"


def test_strip_thinking_no_block():
    assert _strip_thinking("Просто ответ") == "Просто ответ"
