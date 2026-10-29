import hashlib
import secrets
from functools import lru_cache
from io import BytesIO
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}


def file_path(key: str) -> Path:
    return Path(settings.ai_storage_path).resolve() / key


async def save_upload(upload: UploadFile) -> tuple[str, int, str]:
    filename = Path(upload.filename or "").name
    if Path(filename).suffix.lower() not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Unsupported file type"
        )
    key = secrets.token_hex(24)
    path = file_path(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    size = 0
    try:
        with path.open("xb") as output:
            while chunk := await upload.read(1024 * 1024):
                size += len(chunk)
                if size > settings.ai_max_upload_bytes:
                    raise HTTPException(
                        status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "File is too large"
                    )
                digest.update(chunk)
                output.write(chunk)
        if size == 0:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "File is empty")
        return key, size, digest.hexdigest()
    except BaseException:
        path.unlink(missing_ok=True)
        raise


@lru_cache(maxsize=1)
def document_converter():
    from docling.datamodel.base_models import InputFormat
    from docling.document_converter import DocumentConverter

    return DocumentConverter(allowed_formats=[InputFormat.PDF, InputFormat.DOCX])


def extract_pages(path: Path, filename: str) -> list[tuple[int, str]]:
    suffix = Path(filename).suffix.lower()
    if suffix in {".pdf", ".docx"}:
        from docling.datamodel.base_models import DocumentStream

        # Uploads use extensionless storage keys; retain the original file type.
        result = document_converter().convert(
            DocumentStream(name=Path(filename).name, stream=BytesIO(path.read_bytes()))
        )
        document = result.document
        if suffix == ".pdf":
            return [
                (
                    page,
                    document.export_to_markdown(page_no=page, image_placeholder=""),
                )
                for page in sorted(document.pages)
            ]
        # Word documents do not have stable rendered page boundaries.
        return [(1, document.export_to_markdown(image_placeholder=""))]
    return [(1, path.read_text(encoding="utf-8"))]


def chunks(
    pages: list[tuple[int, str]], width: int = 1300, overlap: int = 180
) -> list[tuple[int, str]]:
    result: list[tuple[int, str]] = []
    for page, text in pages:
        clean = " ".join(text.split())
        start = 0
        while start < len(clean):
            end = min(start + width, len(clean))
            if end < len(clean):
                boundary = clean.rfind(" ", start + width // 2, end)
                if boundary > start:
                    end = boundary
            part = clean[start:end].strip()
            if part:
                result.append((page, part))
            if end == len(clean):
                break
            start = max(start + 1, end - overlap)
    return result
