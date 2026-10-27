import json
import logging
import os
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse, Response, StreamingResponse
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from sqlalchemy import select

from app.core.config import settings
from app.db.session import async_session_factory
from app.db.urls import postgres_url
from app.dependencies.auth import AuthenticatedUser
from app.dependencies.database import DatabaseSession
from app.modules.ai.agent import build_graph
from app.modules.ai.memory import delete_memory, list_memories
from app.modules.ai.models import Conversation, Document, MemoryJob, Message
from app.modules.ai.schemas import (
    ChatRequest,
    ConversationCreate,
    ConversationRead,
    ConversationSummary,
    DocumentRead,
)
from app.modules.ai.search import client, delete_document
from app.modules.ai.storage import file_path, save_upload

router = APIRouter(prefix="/ai", tags=["ai"])
logger = logging.getLogger(__name__)


def event(name: str, payload: dict) -> str:
    return f"event: {name}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


async def owned_document(
    session: DatabaseSession, user_id: str, document_id: str
) -> Document:
    document = await session.scalar(
        select(Document).where(Document.id == document_id, Document.user_id == user_id)
    )
    if document is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    return document


async def owned_conversation(
    session: DatabaseSession, user_id: str, conversation_id: str
) -> Conversation:
    conversation = await session.scalar(
        select(Conversation).where(
            Conversation.id == conversation_id, Conversation.user_id == user_id
        )
    )
    if conversation is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation not found")
    return conversation


@router.post("/documents", response_model=DocumentRead, status_code=201)
async def upload_document(
    session: DatabaseSession,
    user: AuthenticatedUser,
    file: Annotated[UploadFile, File()],
) -> Document:
    key, size, sha256 = await save_upload(file)
    document = Document(
        id=str(uuid4()),
        user_id=user.id,
        filename=file.filename or "file",
        content_type=file.content_type or "application/octet-stream",
        storage_key=key,
        size_bytes=size,
        sha256=sha256,
        status="queued",
        chunk_count=0,
        attempts=0,
    )
    try:
        session.add(document)
        await session.commit()
        await session.refresh(document)
    except BaseException:
        file_path(key).unlink(missing_ok=True)
        raise
    return document


@router.get("/documents", response_model=list[DocumentRead])
async def list_documents(
    session: DatabaseSession, user: AuthenticatedUser
) -> list[Document]:
    result = await session.scalars(
        select(Document)
        .where(Document.user_id == user.id)
        .order_by(Document.created_at.desc())
    )
    return list(result)


@router.get("/documents/{document_id}/file")
async def get_document_file(
    document_id: str, session: DatabaseSession, user: AuthenticatedUser
) -> FileResponse:
    document = await owned_document(session, user.id, document_id)
    path = file_path(document.storage_key)
    if not path.exists():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "File not found")
    return FileResponse(
        path, media_type=document.content_type, filename=document.filename
    )


@router.post("/documents/{document_id}/retry", response_model=DocumentRead)
async def retry_document(
    document_id: str, session: DatabaseSession, user: AuthenticatedUser
) -> Document:
    document = await owned_document(session, user.id, document_id)
    if document.status != "failed":
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Only failed documents can be retried"
        )
    document.status = "queued"
    document.error = None
    document.attempts = 0
    await session.commit()
    await session.refresh(document)
    return document


@router.delete("/documents/{document_id}", status_code=204)
async def remove_document(
    document_id: str, session: DatabaseSession, user: AuthenticatedUser
) -> Response:
    document = await owned_document(session, user.id, document_id)
    qdrant = client()
    try:
        await delete_document(qdrant, document.id)
    finally:
        await qdrant.close()
    path = file_path(document.storage_key)
    await session.delete(document)
    await session.commit()
    path.unlink(missing_ok=True)
    return Response(status_code=204)


@router.post("/conversations", response_model=ConversationRead, status_code=201)
async def create_conversation(
    payload: ConversationCreate, session: DatabaseSession, user: AuthenticatedUser
) -> Conversation:
    conversation = Conversation(
        id=str(uuid4()),
        user_id=user.id,
        title=payload.title.strip() or "New conversation",
    )
    session.add(conversation)
    await session.commit()
    await session.refresh(conversation)
    return conversation


@router.get("/conversations", response_model=list[ConversationSummary])
async def list_conversations(
    session: DatabaseSession, user: AuthenticatedUser
) -> list[Conversation]:
    result = await session.scalars(
        select(Conversation)
        .where(Conversation.user_id == user.id)
        .order_by(Conversation.updated_at.desc())
    )
    return list(result)


@router.get("/conversations/{conversation_id}", response_model=ConversationRead)
async def get_conversation(
    conversation_id: str, session: DatabaseSession, user: AuthenticatedUser
) -> Conversation:
    return await owned_conversation(session, user.id, conversation_id)


@router.delete("/conversations/{conversation_id}", status_code=204)
async def remove_conversation(
    conversation_id: str, session: DatabaseSession, user: AuthenticatedUser
) -> Response:
    conversation = await owned_conversation(session, user.id, conversation_id)
    if conversation.messages:
        uri = postgres_url(settings.database_url)
        async with AsyncPostgresSaver.from_conn_string(uri) as checkpointer:
            await checkpointer.setup()
            await checkpointer.adelete_thread(conversation_id)
    await session.delete(conversation)
    await session.commit()
    return Response(status_code=204)


@router.post("/conversations/{conversation_id}/messages/stream")
async def stream_message(
    conversation_id: str,
    payload: ChatRequest,
    session: DatabaseSession,
    user: AuthenticatedUser,
) -> StreamingResponse:
    conversation = await owned_conversation(session, user.id, conversation_id)
    requested = list(dict.fromkeys(payload.document_ids))
    if requested:
        ready = await session.scalars(
            select(Document.id).where(
                Document.user_id == user.id,
                Document.id.in_(requested),
                Document.status == "ready",
            )
        )
        if set(ready) != set(requested):
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, "Select only your ready documents"
            )
    if not (settings.ai_model_api_key or os.environ.get("OPENAI_API_KEY")):
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, "AI model is not configured"
        )
    question = payload.content.strip()
    if not question:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Message is empty")
    user_message = Message(
        id=str(uuid4()),
        conversation_id=conversation.id,
        role="user",
        content=question,
        citations=[],
    )
    session.add(user_message)
    if conversation.title == "New conversation":
        conversation.title = question[:160]
    conversation.updated_at = datetime.now(UTC)
    await session.commit()

    async def stream() -> AsyncIterator[str]:
        yield event(
            "started",
            {"conversation_id": conversation_id, "message_id": user_message.id},
        )
        try:
            uri = postgres_url(settings.database_url)
            async with AsyncPostgresSaver.from_conn_string(uri) as checkpointer:
                await checkpointer.setup()
                graph = build_graph(checkpointer)
                config = {"configurable": {"thread_id": conversation_id}}
                answer_text = ""
                citations: list[dict] = []
                async for mode, part in graph.astream(
                    {
                        "messages": [HumanMessage(content=question)],
                        "question": question,
                        "user_id": user.id,
                        "document_ids": requested,
                    },
                    config=config,
                    stream_mode=["updates", "messages"],
                ):
                    if mode == "updates":
                        if "retrieve" in part:
                            yield event(
                                "sources",
                                {
                                    "items": [
                                        {
                                            key: item[key]
                                            for key in (
                                                "document_id",
                                                "filename",
                                                "page",
                                                "chunk",
                                            )
                                        }
                                        for item in part["retrieve"].get(
                                            "retrieved", []
                                        )
                                    ]
                                },
                            )
                        if "rewrite" in part:
                            yield event("progress", {"stage": "retrying_search"})
                        if "answer" in part:
                            answer_text = part["answer"]["answer"]
                            citations = part["answer"]["citations"]
                    elif mode == "messages":
                        chunk, metadata = part
                        if (
                            metadata.get("langgraph_node") == "answer"
                            and isinstance(chunk.content, str)
                            and chunk.content
                        ):
                            yield event("answer_delta", {"text": chunk.content})
                async with async_session_factory() as write_session:
                    write_session.add(
                        Message(
                            id=str(uuid4()),
                            conversation_id=conversation_id,
                            role="assistant",
                            content=answer_text,
                            citations=citations,
                        )
                    )
                    if settings.ai_memory_enabled:
                        write_session.add(
                            MemoryJob(
                                id=str(uuid4()),
                                user_id=user.id,
                                content=question,
                                status="queued",
                                attempts=0,
                            )
                        )
                    await write_session.commit()
                yield event("completed", {"citations": citations})
        except Exception:
            logger.exception("AI response failed for conversation %s", conversation_id)
            yield event("error", {"message": "The AI response failed. Please retry."})

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/memories")
async def get_memories(user: AuthenticatedUser) -> list[dict]:
    return await list_memories(user.id)


@router.delete("/memories/{memory_id}", status_code=204)
async def remove_memory(memory_id: str, user: AuthenticatedUser) -> Response:
    try:
        await delete_memory(user.id, memory_id)
    except KeyError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Memory not found") from exc
    return Response(status_code=204)
