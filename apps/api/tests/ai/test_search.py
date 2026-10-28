from types import SimpleNamespace

import pytest
from langchain_core.messages import AIMessage, HumanMessage
from qdrant_client import models

from app.modules.ai import agent, search
from app.modules.ai.evaluate import metrics
from app.modules.ai.storage import chunks


def test_chunks_keep_page_numbers() -> None:
    result = chunks(
        [(2, "alpha beta gamma"), (3, "delta epsilon")], width=10, overlap=2
    )
    assert result[0][0] == 2
    assert result[-1][0] == 3
    assert all(text for _, text in result)


def test_retrieval_metrics() -> None:
    recall, reciprocal_rank = metrics(
        [{"document_id": "unrelated"}, {"document_id": "relevant"}],
        {"relevant"},
    )
    assert recall == 1
    assert reciprocal_rank == 0.5


@pytest.mark.asyncio
@pytest.mark.parametrize("provider", ["openai", "local"])
async def test_hybrid_search_filters_user_and_selected_documents(
    monkeypatch, provider
) -> None:
    monkeypatch.setattr(search.settings, "ai_embedding_provider", provider)
    captured = {}

    class FakeQdrant:
        async def collection_exists(self, _name):
            return True

        async def query_points(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(points=[])

        async def close(self):
            pass

    async def fake_encode(_texts):
        return [([0.0] * 1024, models.SparseVector(indices=[1], values=[1.0]))]

    monkeypatch.setattr(search, "client", FakeQdrant)
    monkeypatch.setattr(search, "encode", fake_encode)

    assert await search.search_documents("alice", ["owned-doc"], "question") == []
    expected = ["dense", "sparse", "bm25"] if provider == "local" else ["dense", "bm25"]
    assert [branch.using for branch in captured["prefetch"]] == expected
    assert captured["prefetch"][-1].query.text == "question"
    assert captured["prefetch"][-1].query.model == "Qdrant/bm25"
    for branch in captured["prefetch"]:
        conditions = {item.key: item.match for item in branch.filter.must}
        assert conditions["user_id"].value == "alice"
        assert conditions["document_id"].any == ["owned-doc"]


@pytest.mark.asyncio
async def test_index_document_adds_bm25_vector(monkeypatch) -> None:
    captured = {}

    class FakeQdrant:
        async def collection_exists(self, _name):
            return False

        async def create_collection(self, **kwargs):
            captured["collection"] = kwargs

        async def create_payload_index(self, **_kwargs):
            pass

        async def upsert(self, **kwargs):
            captured["points"] = kwargs["points"]

    async def fake_encode(_texts):
        return [([0.0] * 1024, models.SparseVector(indices=[1], values=[1.0]))]

    monkeypatch.setattr(search, "encode", fake_encode)
    await search.index_document(
        FakeQdrant(),
        SimpleNamespace(id="doc", user_id="alice", filename="a.txt"),
        [(1, "keyword evidence")],
    )

    assert (
        captured["collection"]["sparse_vectors_config"]["bm25"].modifier
        == models.Modifier.IDF
    )
    point = captured["points"][0]
    assert set(point.vector) == {"dense", "sparse", "bm25"}
    assert point.vector["bm25"].text == "keyword evidence"
    assert point.vector["bm25"].model == "Qdrant/bm25"


@pytest.mark.asyncio
async def test_bm25_search_skips_bge_and_keeps_owner_filter(monkeypatch) -> None:
    captured = {}

    class FakeQdrant:
        async def collection_exists(self, _name):
            return True

        async def query_points(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(points=[])

        async def close(self):
            pass

    async def unexpected_encode(_texts):
        raise AssertionError("BM25 search must not run BGE-M3")

    monkeypatch.setattr(search, "client", FakeQdrant)
    monkeypatch.setattr(search, "encode", unexpected_encode)

    found = await search.search_documents("alice", ["owned-doc"], "term", mode="bm25")
    assert found == []
    assert captured["using"] == "bm25"
    assert captured["query"].text == "term"
    conditions = {item.key: item.match for item in captured["query_filter"].must}
    assert conditions["user_id"].value == "alice"
    assert conditions["document_id"].any == ["owned-doc"]


@pytest.mark.asyncio
async def test_answer_exposes_only_cited_sources(monkeypatch) -> None:
    class FakeModel:
        async def ainvoke(self, _messages):
            return AIMessage(content="The answer is in [2].")

    monkeypatch.setattr(agent, "model", FakeModel)
    result = await agent.answer(
        {
            "messages": [HumanMessage(content="Question")],
            "document_ids": ["doc"],
            "memories": [],
            "retrieved": [
                {
                    "document_id": "doc",
                    "filename": "a.pdf",
                    "page": 1,
                    "chunk": 0,
                    "content": "First",
                },
                {
                    "document_id": "doc",
                    "filename": "a.pdf",
                    "page": 2,
                    "chunk": 1,
                    "content": "Second",
                },
            ],
        }
    )
    assert [item["number"] for item in result["citations"]] == [2]


@pytest.mark.asyncio
async def test_openai_encode_avoids_local_model(monkeypatch) -> None:
    captured = {}

    class FakeEmbeddings:
        def __init__(self, **kwargs):
            captured.update(kwargs)

        async def aembed_documents(self, texts):
            assert texts == ["first", "second"]
            return [[0.1] * 1024, [0.2] * 1024]

    def unexpected_local():
        raise AssertionError("OpenAI must not load the local model")

    monkeypatch.setattr(search.settings, "ai_embedding_provider", "openai")
    monkeypatch.setattr(search.settings, "ai_embedding_api_key", "test-key")
    monkeypatch.setattr(search, "OpenAIEmbeddings", FakeEmbeddings)
    monkeypatch.setattr(search, "embedding_model", unexpected_local)
    result = await search.encode(["first", "second"])
    assert [dense[0] for dense, _ in result] == [0.1, 0.2]
    assert captured["dimensions"] == 1024
    assert captured["model"] == search.settings.ai_openai_embedding_model
    assert captured["api_key"] == "test-key"


@pytest.mark.asyncio
async def test_local_provider_preserves_bge_encode(monkeypatch) -> None:
    from unittest.mock import AsyncMock

    expected = [([0.5], models.SparseVector(indices=[1], values=[1.0]))]
    local = AsyncMock(return_value=expected)
    monkeypatch.setattr(search.settings, "ai_embedding_provider", "local")
    monkeypatch.setattr(search, "encode_local", local)
    assert await search.encode(["text"]) == expected
    local.assert_awaited_once_with(["text"])


@pytest.mark.parametrize("provider", ["openai", "local"])
def test_memory_embedding_configuration(monkeypatch, tmp_path, provider) -> None:
    from app.modules.ai.memory import memory_configuration

    monkeypatch.setattr(search.settings, "ai_embedding_provider", provider)
    monkeypatch.setattr(search.settings, "ai_storage_path", str(tmp_path / "uploads"))
    config = memory_configuration()
    if provider == "openai":
        assert config["embedder"]["provider"] == "openai"
        assert config["embedder"]["config"]["embedding_dims"] == 1024
        assert (
            config["vector_store"]["config"]["collection_name"]
            == "ai_memories_openai_v1"
        )
    else:
        assert config["embedder"]["provider"] == "huggingface"
        assert config["embedder"]["config"]["model"] == "BAAI/bge-m3"


@pytest.mark.asyncio
async def test_openai_sparse_search_uses_bm25_without_embeddings(monkeypatch) -> None:
    from unittest.mock import AsyncMock

    qdrant = SimpleNamespace(
        collection_exists=AsyncMock(return_value=True),
        query_points=AsyncMock(return_value=SimpleNamespace(points=[])),
        close=AsyncMock(),
    )
    monkeypatch.setattr(search.settings, "ai_embedding_provider", "openai")
    monkeypatch.setattr(search, "client", lambda: qdrant)
    encoder = AsyncMock(side_effect=AssertionError("Must not call embeddings"))
    monkeypatch.setattr(search, "encode", encoder)
    await search.search_documents("alice", ["doc"], "term", mode="sparse")
    assert qdrant.query_points.call_args.kwargs["using"] == "bm25"
    encoder.assert_not_awaited()


@pytest.mark.asyncio
async def test_qwen_request_sends_strings_and_float_vectors(monkeypatch) -> None:
    import json

    import httpx
    from openai import AsyncOpenAI

    requests = []

    def respond(request):
        body = json.loads(request.content)
        requests.append(body)
        assert all(isinstance(text, str) for text in body["input"])
        assert body["encoding_format"] == "float"
        assert body["dimensions"] == 1024
        assert body["model"] == "text-embedding-v4"
        return httpx.Response(
            200,
            json={
                "object": "list",
                "model": body["model"],
                "data": [
                    {"index": i, "object": "embedding", "embedding": [0.1] * 1024}
                    for i in range(len(body["input"]))
                ],
                "usage": {"prompt_tokens": 1, "total_tokens": 1},
            },
        )

    monkeypatch.setattr(search.settings, "ai_embedding_api_key", "test-key")
    monkeypatch.setattr(
        search.settings, "ai_openai_embedding_model", "text-embedding-v4"
    )
    monkeypatch.setattr(
        search.settings,
        "ai_embedding_base_url",
        "https://qwen.example/compatible-mode/v1",
    )
    embeddings = search.openai_embedding_model()
    async with (
        httpx.AsyncClient(transport=httpx.MockTransport(respond)) as http,
        AsyncOpenAI(
            api_key="test-key",
            base_url=search.settings.ai_embedding_base_url,
            http_client=http,
        ) as sdk,
    ):
        embeddings.async_client = sdk.embeddings
        texts = ["PDF extracted text 中文"] * 11
        result = await embeddings.aembed_documents(texts)
    assert len(result) == 11
    assert [len(body["input"]) for body in requests] == [8, 3]
    assert [text for body in requests for text in body["input"]] == texts
