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
async def test_hybrid_search_filters_user_and_selected_documents(monkeypatch) -> None:
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
    assert len(captured["prefetch"]) == 3
    assert [branch.using for branch in captured["prefetch"]] == [
        "dense",
        "sparse",
        "bm25",
    ]
    assert captured["prefetch"][2].query.text == "question"
    assert captured["prefetch"][2].query.model == "Qdrant/bm25"
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
