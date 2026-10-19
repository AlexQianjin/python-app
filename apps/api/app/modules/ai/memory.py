import asyncio
import logging
import os
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

from app.core.config import settings

logger = logging.getLogger(__name__)


def memory_configuration() -> dict:
    parsed = urlparse(settings.qdrant_url)
    history_path = Path(settings.ai_storage_path).resolve().parent / "mem0_history.db"
    history_path.parent.mkdir(parents=True, exist_ok=True)
    config = {
        "history_db_path": str(history_path),
        "vector_store": {
            "provider": "qdrant",
            "config": {
                "host": parsed.hostname,
                "port": parsed.port or 6333,
                "api_key": settings.qdrant_api_key or None,
                "collection_name": "ai_memories",
                "embedding_model_dims": 1024,
            },
        },
        "embedder": {
            "provider": "huggingface",
            "config": {"model": settings.ai_embedding_model},
        },
        "llm": {
            "provider": "openai",
            "config": {
                "model": settings.ai_model,
                "api_key": settings.ai_model_api_key
                or os.environ.get("OPENAI_API_KEY"),
                **(
                    {"openai_base_url": settings.ai_model_base_url}
                    if settings.ai_model_base_url
                    else {}
                ),
            },
        },
    }
    return config


@lru_cache
def memory_client():
    from mem0 import Memory

    return Memory.from_config(memory_configuration())


async def recall(user_id: str, query: str) -> list[str]:
    if not settings.ai_memory_enabled:
        return []
    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(
                lambda: memory_client().search(
                    query, filters={"user_id": user_id}, top_k=5
                )
            ),
            timeout=4,
        )
        rows = result.get("results", []) if isinstance(result, dict) else result
        return [str(row.get("memory", "")) for row in rows if row.get("memory")]
    except Exception:
        logger.exception("Memory recall failed")
        return []


async def remember(user_id: str, question: str) -> None:
    if not settings.ai_memory_enabled:
        return
    await asyncio.to_thread(
        lambda: memory_client().add(
            [{"role": "user", "content": question}], user_id=user_id
        )
    )


async def list_memories(user_id: str) -> list[dict]:
    if not settings.ai_memory_enabled:
        return []
    result = await asyncio.to_thread(
        lambda: memory_client().get_all(filters={"user_id": user_id}, top_k=100)
    )
    return result.get("results", []) if isinstance(result, dict) else result


async def delete_memory(user_id: str, memory_id: str) -> None:
    rows = await list_memories(user_id)
    if not any(str(row.get("id")) == memory_id for row in rows):
        raise KeyError(memory_id)
    await asyncio.to_thread(lambda: memory_client().delete(memory_id))
