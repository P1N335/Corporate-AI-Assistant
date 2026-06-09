"""DTO чтения истории чата."""

from pydantic import BaseModel, Field

from app.schemas.chat import Source


class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    route: str | None = None
    rating: int | None = None
    created_at: str
    sources: list[Source] = Field(default_factory=list)


class SessionOut(BaseModel):
    id: str
    created_at: str
    messages: list[MessageOut] = Field(default_factory=list)


class SessionSummary(BaseModel):
    id: str
    title: str = ""
    created_at: str
    message_count: int
