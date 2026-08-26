"""Document parser factory."""

from __future__ import annotations

from config.settings import Settings, get_settings
from factories.parsers.docling.client import DoclingDocumentParser
from factories.parsers.protocol import DocumentParser


def make_document_parser(settings: Settings | None = None) -> DocumentParser:
    settings = settings or get_settings()
    if settings.pdf.backend == "docling":
        return DoclingDocumentParser(
            max_pages=settings.pdf.max_pages,
            max_file_size_mb=settings.pdf.max_file_size_mb,
            enable_ocr=settings.pdf.enable_ocr,
            enable_table_structure=settings.pdf.enable_table_structure,
        )
    raise ValueError(f"Unsupported document parser backend: {settings.pdf.backend}")
