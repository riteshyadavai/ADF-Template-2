"""Docling PDF parser adapter."""

from __future__ import annotations

import asyncio
import importlib
from pathlib import Path
from typing import Any

from factories.parsers.protocol import DocumentParser, ParsedDocument


class DoclingDocumentParser(DocumentParser):
    def __init__(
        self,
        max_pages: int,
        max_file_size_mb: int,
        *,
        enable_ocr: bool,
        enable_table_structure: bool,
    ) -> None:
        self._max_pages = max_pages
        self._max_file_size = max_file_size_mb * 1024 * 1024
        self._enable_ocr = enable_ocr
        self._enable_table_structure = enable_table_structure
        self._converter: Any | None = None

    def _document_converter(self) -> Any:
        if self._converter is not None:
            return self._converter
        try:
            base_models = importlib.import_module("docling.datamodel.base_models")
            pipeline_options_module = importlib.import_module(
                "docling.datamodel.pipeline_options"
            )
            converter_module = importlib.import_module("docling.document_converter")
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "The Docling parser requires the optional 'documents' dependencies. "
                "Install them with: uv sync --extra documents"
            ) from exc

        options = pipeline_options_module.PdfPipelineOptions(
            do_ocr=self._enable_ocr,
            do_table_structure=self._enable_table_structure,
        )
        self._converter = converter_module.DocumentConverter(
            allowed_formats=[base_models.InputFormat.PDF],
            format_options={
                base_models.InputFormat.PDF: converter_module.PdfFormatOption(
                    pipeline_options=options
                )
            },
        )
        return self._converter

    async def parse(self, path: Path) -> ParsedDocument:
        if not path.is_file():
            raise FileNotFoundError(path)
        if path.stat().st_size > self._max_file_size:
            raise ValueError(f"Document exceeds maximum size: {path}")

        def convert() -> Any:
            return self._document_converter().convert(
                path,
                max_num_pages=self._max_pages,
                max_file_size=self._max_file_size,
            )

        result = await asyncio.to_thread(convert)
        document = result.document
        sections: list[dict[str, str]] = []
        current = {"title": "Content", "content": ""}
        for item in document.texts:
            label = str(getattr(item, "label", ""))
            text = getattr(item, "text", "")
            if not text:
                continue
            if "title" in label or "section_header" in label:
                if current["content"].strip():
                    sections.append({**current, "content": current["content"].strip()})
                current = {"title": text.strip(), "content": ""}
            else:
                current["content"] += f"{text}\n"
        if current["content"].strip():
            sections.append({**current, "content": current["content"].strip()})
        return ParsedDocument(
            text=document.export_to_text(),
            sections=sections,
            metadata={"source_path": str(path)},
            parser="docling",
        )
