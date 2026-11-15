"""Size-bounded extraction for text PDFs, DOCX paragraphs/tables and UTF text."""

import io
import zipfile
from pathlib import Path

from docx import Document
from lxml.etree import XMLSyntaxError
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.errors import AnalysisError

MAX_BYTES = 2 * 1024 * 1024
MAX_TEXT = 100_000


def validate_text(text: str) -> str:
    """Normalize whitespace without destroying the line evidence coordinates."""
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\x00", "")
    if len(text) > MAX_TEXT:
        raise AnalysisError("text_too_large", "Use a resume with fewer than 100,000 characters.")
    if len(text.strip()) < 20:
        raise AnalysisError(
            "empty_document", "No usable text. Paste text or upload a text-based PDF."
        )
    if sum(char.isprintable() or char.isspace() for char in text) / len(text) < 0.95:
        raise AnalysisError("invalid_text", "The document contains binary data, not readable text.")
    return text.strip()


def extract_document(filename: str, content: bytes) -> tuple[str, str]:
    """Extract supported formats without trusting the extension as a content signature."""
    if len(content) > MAX_BYTES:
        raise AnalysisError("file_too_large", "Maximum resume upload size is 2 MiB.", 413)
    if not content:
        raise AnalysisError("empty_document", "The uploaded file is empty.")
    suffix = Path(filename).suffix.lower()
    if suffix == ".txt":
        try:
            text = content.decode(
                "utf-16" if content.startswith((b"\xff\xfe", b"\xfe\xff")) else "utf-8-sig"
            )
        except UnicodeError as error:
            raise AnalysisError(
                "invalid_encoding", "Save the text file as UTF-8 or UTF-16."
            ) from error
    elif suffix == ".pdf":
        if not content.startswith(b"%PDF-"):
            raise AnalysisError("invalid_pdf", "This file is not a valid PDF.")
        try:
            reader = PdfReader(io.BytesIO(content))
            if reader.is_encrypted:
                raise AnalysisError("encrypted_pdf", "Remove the PDF password before uploading.")
            if len(reader.pages) > 20:
                raise AnalysisError("too_many_pages", "Limit the resume to 20 pages.")
            chunks: list[str] = []
            for page in reader.pages:
                chunks.append(page.extract_text() or "")
                if sum(map(len, chunks)) > MAX_TEXT:
                    raise AnalysisError("text_too_large", "The extracted PDF text is too large.")
            text = "\n".join(chunks)
        except (PdfReadError, ValueError, TypeError, KeyError, OSError) as error:
            raise AnalysisError(
                "invalid_pdf", "The PDF is damaged or could not be read."
            ) from error
    elif suffix == ".docx":
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                if sum(item.file_size for item in archive.infolist()) > 10 * MAX_BYTES:
                    raise AnalysisError(
                        "expanded_file_too_large", "The expanded DOCX is too large."
                    )
                if "word/document.xml" not in archive.namelist():
                    raise AnalysisError("invalid_docx", "The file is not a Word DOCX document.")
            document = Document(io.BytesIO(content))
            # Document.iter_inner_content preserves table/paragraph ordering.
            chunks = [
                p.text for section in document.sections for p in section.header.paragraphs if p.text
            ]
            for block in document.iter_inner_content():
                if hasattr(block, "rows"):
                    chunks.extend(" | ".join(cell.text for cell in row.cells) for row in block.rows)
                else:
                    chunks.append(block.text)
            text = "\n".join(chunks)
        except (zipfile.BadZipFile, KeyError, ValueError, OSError, XMLSyntaxError) as error:
            raise AnalysisError(
                "invalid_docx", "The DOCX is damaged or could not be read."
            ) from error
    else:
        raise AnalysisError("unsupported_format", "Upload a .pdf, .docx or .txt file.", 415)
    return validate_text(text), suffix[1:]
