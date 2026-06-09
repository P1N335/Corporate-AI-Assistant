"""Тесты построения промпта и модели чанка."""

from app.services.rag_service import RAGService, RetrievedChunk


def test_build_prompt_contains_context_and_question():
    chunks = [RetrievedChunk(filename="handbook.txt", chunk_index=0, text="28 дней", score=0.1)]
    prompt = RAGService.build_prompt("Сколько отпуска?", chunks)
    assert "Сколько отпуска?" in prompt
    assert "handbook.txt" in prompt
    assert "28 дней" in prompt


def test_retrieved_chunk_snippet_truncates():
    chunk = RetrievedChunk(filename="f", chunk_index=0, text="a" * 300, score=0.0)
    assert len(chunk.snippet) <= 201
    assert chunk.snippet.endswith("…")


def test_retrieved_chunk_snippet_short_text():
    chunk = RetrievedChunk(filename="f", chunk_index=0, text="коротко", score=0.0)
    assert chunk.snippet == "коротко"
