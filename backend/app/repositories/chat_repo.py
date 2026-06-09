"""Репозиторий истории чата: сессии, сообщения, источники, оценки.

Возвращает dict'ы (не ORM-объекты), чтобы избежать DetachedInstanceError.
Синхронный, вызывается через run_in_threadpool.
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import select

from app.infrastructure.database import session_scope
from app.models.chat import ChatSession, Message, Source
from app.services.rag_service import RetrievedChunk


def _iso(value) -> str:
    return value.isoformat() if isinstance(value, datetime) else str(value)


def create_session() -> str:
    session_id = uuid4().hex
    with session_scope() as session:
        session.add(ChatSession(id=session_id))
    return session_id


def session_exists(session_id: str) -> bool:
    with session_scope() as session:
        return session.get(ChatSession, session_id) is not None


def add_user_message(session_id: str, content: str) -> str:
    message_id = uuid4().hex
    with session_scope() as session:
        session.add(
            Message(id=message_id, session_id=session_id, role="user", content=content)
        )
    return message_id


def add_assistant_message(
    session_id: str,
    content: str,
    route: str,
    sources: list[RetrievedChunk],
) -> str:
    message_id = uuid4().hex
    with session_scope() as session:
        message = Message(
            id=message_id,
            session_id=session_id,
            role="assistant",
            content=content,
            route=route,
        )
        for chunk in sources:
            message.sources.append(
                Source(
                    filename=chunk.filename,
                    chunk_index=chunk.chunk_index,
                    snippet=chunk.snippet,
                    score=chunk.score,
                )
            )
        session.add(message)
    return message_id


def rate_message(message_id: str, rating: int) -> bool:
    with session_scope() as session:
        message = session.get(Message, message_id)
        if message is None or message.role != "assistant":
            return False
        message.rating = rating
        return True


def _message_to_dict(message: Message) -> dict:
    return {
        "id": message.id,
        "role": message.role,
        "content": message.content,
        "route": message.route,
        "rating": message.rating,
        "created_at": _iso(message.created_at),
        "sources": [
            {
                "filename": s.filename,
                "chunk_index": s.chunk_index,
                "snippet": s.snippet,
                "score": s.score,
            }
            for s in message.sources
        ],
    }


def get_session(session_id: str) -> dict | None:
    with session_scope() as session:
        obj = session.get(ChatSession, session_id)
        if obj is None:
            return None
        return {
            "id": obj.id,
            "created_at": _iso(obj.created_at),
            "messages": [_message_to_dict(m) for m in obj.messages],
        }


def _session_title(messages: list[Message]) -> str:
    """Заголовок беседы = первое сообщение пользователя."""
    for m in messages:
        if m.role == "user":
            text = " ".join(m.content.strip().split())
            return (text[:40] + "…") if len(text) > 40 else text
    return "Пустая беседа"


def list_sessions() -> list[dict]:
    """Сводка по сессиям, отсортированная по последней активности."""
    with session_scope() as session:
      