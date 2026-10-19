"""Compare dense, learned sparse, BM25, and hybrid retrieval."""

import argparse
import asyncio
import json
from pathlib import Path
from time import perf_counter

from app.modules.ai.search import search_documents


def metrics(found: list[dict], relevant: set[str]) -> tuple[float, float]:
    ranked = [str(item["document_id"]) for item in found]
    recall = len(relevant.intersection(ranked)) / len(relevant)
    reciprocal_rank = next(
        (
            1 / rank
            for rank, document_id in enumerate(ranked, 1)
            if document_id in relevant
        ),
        0.0,
    )
    return recall, reciprocal_rank


async def evaluate(path: Path, limit: int) -> dict:
    cases = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    if not cases:
        raise ValueError("Evaluation file has no cases")
    results = {}
    for mode in ("dense", "sparse", "bm25", "hybrid"):
        recalls = []
        reciprocal_ranks = []
        durations = []
        for case in cases:
            relevant = set(case["relevant_document_ids"])
            if not relevant:
                raise ValueError("Each case needs relevant_document_ids")
            started = perf_counter()
            found = await search_documents(
                case["user_id"],
                case["document_ids"],
                case["query"],
                limit=limit,
                mode=mode,
            )
            durations.append((perf_counter() - started) * 1000)
            recall, reciprocal_rank = metrics(found, relevant)
            recalls.append(recall)
            reciprocal_ranks.append(reciprocal_rank)
        results[mode] = {
            "recall_at_k": round(sum(recalls) / len(recalls), 4),
            "mrr_at_k": round(sum(reciprocal_ranks) / len(reciprocal_ranks), 4),
            "mean_latency_ms": round(sum(durations) / len(durations), 1),
            "cases": len(cases),
        }
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--limit", type=int, default=8)
    args = parser.parse_args()
    if args.limit < 1:
        parser.error("--limit must be positive")
    print(json.dumps(asyncio.run(evaluate(args.dataset, args.limit)), indent=2))


if __name__ == "__main__":
    main()
