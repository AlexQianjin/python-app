from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    size_bytes: int
    status: str
    error: str | None
    chunk_count: int
    created_at: datetime


class ConversationCreate(BaseModel):
    title: str = Field(default="New conversation", max_length=160)


class Citation(BaseModel):
    number: int
    document_id: str
    filename: str
    page: int
    chunk: int


class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    role: str
    content: str
    citations: list[Citation]
    created_at: datetime


class ConversationSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    created_at: datetime
    updated_at: datetime


class ConversationRead(ConversationSummary):
    messages: list[MessageRead]


class ChatRequest(BaseModel):
    content: str = Field(min_length=1, max_length=10000)
    document_ids: list[str] = Field(default_factory=list, max_length=30)
