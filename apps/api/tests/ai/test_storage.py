from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.modules.ai import storage


@pytest.mark.parametrize("suffix", [".txt", ".md"])
def test_plain_text_uploads_do_not_load_docling(tmp_path, monkeypatch, suffix):
    path = tmp_path / "storage-key"
    path.write_text("Hello 中文\nSecond line", encoding="utf-8")
    converter = Mock(side_effect=AssertionError("Text must not load Docling"))
    monkeypatch.setattr(storage, "document_converter", converter)

    assert storage.extract_pages(path, f"notes{suffix}") == [
        (1, "Hello 中文\nSecond line")
    ]


def test_docling_pdf_keeps_original_filename_and_page_numbers(tmp_path, monkeypatch):
    path = tmp_path / "extensionless-storage-key"
    path.write_bytes(b"%PDF-test")
    document = Mock()
    document.pages = {3: object(), 1: object(), 2: object()}
    content = {1: "# Heading\nText", 2: "", 3: "| Table | Value |"}
    document.export_to_markdown.side_effect = lambda *, page_no, image_placeholder: (
        content[page_no]
    )
    converter = Mock()
    converter.convert.return_value = SimpleNamespace(document=document)
    monkeypatch.setattr(storage, "document_converter", lambda: converter)

    pages = storage.extract_pages(path, "report.PDF")
    assert pages == list(content.items())
    source = converter.convert.call_args.args[0]
    assert source.name == "report.PDF"
    assert source.stream.getvalue() == b"%PDF-test"
    assert {page for page, _ in storage.chunks(pages)} == {1, 3}


def test_docling_docx_exports_tables_and_text(tmp_path, monkeypatch):
    path = tmp_path / "storage-key"
    path.write_bytes(b"docx-test")
    document = Mock()
    document.export_to_markdown.return_value = "# Heading\n\n| Cell | Value |"
    converter = Mock()
    converter.convert.return_value = SimpleNamespace(document=document)
    monkeypatch.setattr(storage, "document_converter", lambda: converter)

    assert storage.extract_pages(path, "notes.docx") == [
        (1, "# Heading\n\n| Cell | Value |")
    ]
    document.export_to_markdown.assert_called_once_with(image_placeholder="")


def test_docling_conversion_error_reaches_worker(tmp_path, monkeypatch):
    path = tmp_path / "storage-key"
    path.write_bytes(b"invalid-pdf")
    converter = Mock()
    converter.convert.side_effect = ValueError("Cannot convert document")
    monkeypatch.setattr(storage, "document_converter", lambda: converter)

    with pytest.raises(ValueError, match="Cannot convert"):
        storage.extract_pages(path, "broken.pdf")
