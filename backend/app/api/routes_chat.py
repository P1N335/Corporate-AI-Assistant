"""Эндпоинты чата и оценки ответа."""

from fastapi import APIRouter, HTTPException, status
from starlette.concurrency import run_in_threadpool

from app.core.config import settings
from app.repositories import chat_repo
from app.schemas.chat import ChatRequest, ChatResponse, FeedbackRequest, Source
from app.services.chat_service import handle_chat
from app.services.llm_service import LLMServiceError

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    try:
        turn = await handle_chat(request.message, request.session_id)
    except LLMServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Ошибка LLM-провайдера: {exc}",
        ) from exc

    sources = [
        Source(filename=c.filename, chunk_index=c.chunk_index, snippet=c.snippet, score=c.score)
        for c in turn.sources
    ]
    return ChatResponse(
        answer=turn.answer,
        model=settings.llm_model,
        route=turn.route,
        session_id=turn.session_id,