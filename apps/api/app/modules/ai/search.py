import asyncio
import os
from functools import lru_cache
from typing import Literal
from uuid import NAMESPACE_URL, uuid5

from langchain_openai import OpenAIEmbeddings
from qdrant_client import AsyncQdrantClient, models

from app.core.config import settings
from app.modules.ai.models import Document

VECTOR_SIZE = 1024


@lru_cache
def embedding_model():
    from FlagEmbedding import BGEM3FlagModel

    return BGEM3FlagModel(settings.ai_embedding_model, use_fp16=False)


def openai_embedding_model() -> OpenAIEmbeddings:
    key = (
        settings.ai_embedding_api_key
        or settings.ai_model_api_key
        or os.environ.get("OPENAI_API_KEY")
    )
    if not key:
        raise RuntimeError("Set AI_EMBEDDING_API_KEY or OPENAI_API_KEY for embeddings")
    return OpenAIEmbeddings(
        model=settings.ai_openai_embedding_model,
        dimensions=VECTOR_SIZE,
        api_key=key,
        base_url=settings.ai_embedding_base_url,
        # Compatible providers such as Qwen require strings, not OpenAI token IDs.
        check_embedding_ctx_length=False,
        chunk_size=8,
        model_kwargs={"encoding_format": "float"},
    )


async def encode(texts: list[str]) -> list[tuple[list[float], models.SparseVector]]:
    if not texts:
        return []
    if settings.ai_embedding_provider == "openai":
        dense_vectors = await openai_embedding_model().aembed_documents(texts)
        return [
            (dense, models.SparseVector(indices=[], values=[]))
            for dense in dense_vectors
        ]
    return await encode_local(texts)


async def encode_local(
    texts: list[str],
) -> list[tuple[list[float], models.SparseVector]]:
    def run():
        return embedding_model().encode(
            texts,
            batch_size=8,
            max_length=1024,
            return_dense=True,
            return_sparse=True,
            return_colbert_vecs=False,
        )

    result = await asyncio.to_thread(run)
    vectors = []
    for dense, sparse in zip(
        result["dense_vecs"], result["lexical_weights"], strict=True
    ):
        weights = sorted((int(key), float(value)) for key, value in sparse.items())
        vectors.append(
            (
                dense.tolist(),
                models.SparseVector(
                    indices=[key for key, _ in weights],
                    values=[value for _, value in weights],
                ),
            )
        )
    return vectors


def client() -> AsyncQdrantClient:
    return AsyncQdrantClient(
        url=settings.qdrant_url, api_key=settings.qdrant_api_key or None
    )


async def ensure_collection(qdrant: AsyncQdrantClient) -> None:
    if not await qdrant.collection_exists(settings.ai_document_collection):
        await qdrant.create_collection(
            collection_name=settings.ai_document_collection,
            vectors_config={
                "dense": models.VectorParams(
                    size=VECTOR_SIZE, distance=models.Distance.COSINE
                )
            },
            sparse_vectors_config={
                "sparse": models.SparseVectorParams(),
                "bm25": models.SparseVectorParams(modifier=models.Modifier.IDF),
            },
        )
        await qdrant.create_payload_index(
            collection_name=settings.ai_document_collection,
            field_name="user_id",
            field_schema=models.PayloadSchemaType.KEYWORD,
        )
        await qdrant.create_payload_index(
            collection_name=settings.ai_document_collection,
            field_name="document_id",
            field_schema=models.PayloadSchemaType.KEYWORD,
        )


async def delete_document(qdrant: AsyncQdrantClient, document_id: str) -> None:
    if await qdrant.collection_exists(settings.ai_document_collection):
        await qdrant.delete(
            collection_name=settings.ai_document_collection,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="document_id",
                            match=models.MatchValue(value=document_id),
                        )
                    ]
                )
            ),
            wait=True,
        )


async def index_document(
    qdrant: AsyncQdrantClient, document: Document, parts: list[tuple[int, str]]
) -> None:
    await ensure_collection(qdrant)
    await delete_document(qdrant, document.id)
    for offset in range(0, len(parts), 8):
        batch = parts[offset : offset + 8]
        encoded = await encode([text for _, text in batch])
        points = []
        for index, ((page, content), (dense, sparse)) in enumerate(
            zip(batch, encoded, strict=True), offset
        ):
            points.append(
                models.PointStruct(
                    id=str(uuid5(NAMESPACE_URL, f"{document.id}:{index}")),
                    vector={
                        "dense": dense,
                        "sparse": sparse,
                        "bm25": models.Document(text=content, model="Qdrant/bm25"),
                    },
                    payload={
                        "user_id": document.user_id,
                        "document_id": document.id,
                        "filename": document.filename,
                        "page": page,
                        "chunk": index,
                        "content": content,
                    },
                )
            )
        await qdrant.upsert(
            collection_name=settings.ai_document_collection, points=points, wait=True
        )


async def search_documents(
    user_id: str,
    document_ids: list[str],
    query: str,
    limit: int = 8,
    mode: Literal["hybrid", "dense", "sparse", "bm25"] = "hybrid",
) -> list[dict]:
    if not document_ids:
        return []
    qdrant = client()
    try:
        if not await qdrant.collection_exists(settings.ai_document_collection):
            return []
        # OpenAI provides dense vectors; use BM25 for sparse keyword retrieval.
        if mode == "sparse" and settings.ai_embedding_provider == "openai":
            mode = "bm25"
        dense, sparse = (await encode([query]))[0] if mode != "bm25" else (None, None)
        scope = models.Filter(
            must=[
                models.FieldCondition(
                    key="user_id", match=models.MatchValue(value=user_id)
                ),
                models.FieldCondition(
                    key="document_id", match=models.MatchAny(any=document_ids)
                ),
            ]
        )
        if mode == "hybrid":
            found = await qdrant.query_points(
                collection_name=settings.ai_document_collection,
                prefetch=[
                    models.Prefetch(query=dense, using="dense", filter=scope, limit=24),
                    *(
                        [
                            models.Prefetch(
                                query=sparse, using="sparse", filter=scope, limit=24
                            )
                        ]
                        if settings.ai_embedding_provider == "local"
                        else []
                    ),
                    models.Prefetch(
                        query=models.Document(text=query, model="Qdrant/bm25"),
                        using="bm25",
                        filter=scope,
                        limit=24,
                    ),
                ],
                query=models.FusionQuery(fusion=models.Fusion.RRF),
                limit=limit,
                with_payload=True,
            )
        else:
            found = await qdrant.query_points(
                collection_name=settings.ai_document_collection,
                query=(
                    dense
                    if mode == "dense"
                    else sparse
                    if mode == "sparse"
                    else models.Document(text=query, model="Qdrant/bm25")
                ),
                using=mode,
                query_filter=scope,
                limit=limit,
                with_payload=True,
            )
        return [dict(point.payload or {}) for point in found.points]
    finally:
        await qdrant.close()
