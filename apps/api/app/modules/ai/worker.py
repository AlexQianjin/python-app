import asyncio
import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import or_, select, update

from app.db.session import async_session_factory
from app.modules.ai.memory import remember
from app.modules.ai.models import Document, MemoryJob
from app.modules.ai.search import client, index_document
from app.modules.ai.storage import chunks, extract_pages, file_path

logger = logging.getLogger(__name__)


async def process_one() -> bool:
    stale = datetime.now(UTC) - timedelta(minutes=30)
    async with async_session_factory() as session, session.begin():
        await session.execute(
            update(Document)
            .where(
                Document.status == "processing",
                Document.started_at < stale,
                Document.attempts >= 3,
            )
            .values(status="failed", error="Worker stopped before completing")
        )
        document = await session.scalar(
            select(Document)
            .where(
                or_(
                    Document.status == "queued",
                    (Document.status == "processing") & (Document.started_at < stale),
                )
            )
            .where(Document.attempts < 3)
            .order_by(Document.created_at)
            .with_for_update(skip_locked=True)
            .limit(1)
        )
        if document is None:
            return False
        document.status = "processing"
        document.started_at = datetime.now(UTC)
        document.attempts += 1
        document_id = document.id

    async with async_session_factory() as session:
        document = await session.scalar(
            select(Document).where(Document.id == document_id).with_for_update()
        )
        if document is None:
            return True
        try:
            parts = await asyncio.to_thread(
                lambda: chunks(
                    extract_pages(file_path(document.storage_key), document.filename)
                )
            )
            if not parts:
                raise ValueError("No extractable text found")
            qdrant = client()
            try:
                await index_document(qdrant, document, parts)
            finally:
                await qdrant.close()
            document.status = "ready"
            document.error = None
            document.chunk_count = len(parts)
        except Exception as exc:
            logger.exception("Indexing failed for document %s", document_id)
            document.status = "failed"
            document.error = str(exc)[:1000]
        document.started_at = None
        await session.commit()
    return True


async def process_memory_one() -> bool:
    stale = datetime.now(UTC) - timedelta(minutes=30)
    async with async_session_factory() as session, session.begin():
        await session.execute(
            update(MemoryJob)
            .where(
                MemoryJob.status == "processing",
                MemoryJob.started_at < stale,
                MemoryJob.attempts >= 3,
            )
            .values(status="failed", error="Worker stopped before completing")
        )
        job = await session.scalar(
            select(MemoryJob)
            .where(
                or_(
                    MemoryJob.status == "queued",
                    (MemoryJob.status == "processing") & (MemoryJob.started_at < stale),
                )
            )
            .where(MemoryJob.attempts < 3)
            .order_by(MemoryJob.created_at)
            .with_for_update(skip_locked=True)
            .limit(1)
        )
        if job is None:
            return False
        job.status = "processing"
        job.started_at = datetime.now(UTC)
        job.attempts += 1
        job_id = job.id

    async with async_session_factory() as session:
        job = await session.scalar(
            select(MemoryJob).where(MemoryJob.id == job_id).with_for_update()
        )
        if job is None:
            return True
        try:
            await remember(job.user_id, job.content)
            await session.delete(job)
        except Exception as exc:
            logger.exception("Memory write failed for job %s", job_id)
            job.status = "queued" if job.attempts < 3 else "failed"
            job.error = str(exc)[:1000]
            job.started_at = None
        await session.commit()
    return True


async def work_loop(process, name: str) -> None:
    while True:
        try:
            if await process():
                continue
        except Exception:
            logger.exception("%s worker cycle failed", name)
        await asyncio.sleep(3)


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    await asyncio.gather(
        work_loop(process_one, "Document"),
        work_loop(process_memory_one, "Memory"),
    )


if __name__ == "__main__":
    asyncio.run(main())
