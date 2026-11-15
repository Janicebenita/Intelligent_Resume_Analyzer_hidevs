"""Real generated format fixtures plus damaged, encrypted and oversized inputs."""

import io
import zipfile

import pytest
from docx import Document
from pypdf import PdfWriter
from reportlab.pdfgen.canvas import Canvas

from app.demo import DEMO_RESUME
from app.documents import MAX_BYTES, extract_document, validate_text
from app.errors import AnalysisError


def pdf_bytes(text=DEMO_RESUME):
    stream = io.BytesIO()
    canvas = Canvas(stream)
    y = 800
    for line in text.splitlines():
        canvas.drawString(40, y, line)
        y -= 20
    canvas.save()
    return stream.getvalue()


def docx_bytes():
    document = Document()
    document.add_paragraph("Alex Morgan")
    document.add_paragraph("alex.morgan@example.com")
    document.add_paragraph("SKILLS")
    table = document.add_table(rows=1, cols=2)
    table.cell(0, 0).text = "Python"
    table.cell(0, 1).text = "Docker"
    stream = io.BytesIO()
    document.save(stream)
    return stream.getvalue()


@pytest.mark.parametrize("encoding", ["utf-8", "utf-8-sig", "utf-16"])
def test_text_encodings(encoding):
    text, kind = extract_document("resume.txt", DEMO_RESUME.encode(encoding))
    assert "Alex Morgan" in text
    assert kind == "txt"


def test_real_pdf_and_docx_tables():
    text, kind = extract_document("resume.pdf", pdf_bytes())
    assert "alex.morgan@example.com" in text and kind == "pdf"
    text, kind = extract_document("resume.docx", docx_bytes())
    assert "Python | Docker" in text and kind == "docx"


@pytest.mark.parametrize(
    "filename,content,code",
    [
        ("x.txt", b"", "empty_document"),
        ("x.txt", b"x" * (MAX_BYTES + 1), "file_too_large"),
        ("x.exe", b"binary-data-and-other-data", "unsupported_format"),
        ("x.txt", b"\xff\x80\xff broken", "invalid_encoding"),
        ("x.pdf", b"pretending to be a pdf", "invalid_pdf"),
        ("x.pdf", b"%PDF-1.4\nbroken", "invalid_pdf"),
        ("x.docx", b"not a zip", "invalid_docx"),
        ("x.txt", b"a", "empty_document"),
    ],
)
def test_file_error_codes(filename, content, code):
    with pytest.raises(AnalysisError) as error:
        extract_document(filename, content)
    assert error.value.code == code


def test_encrypted_and_image_only_pdf():
    writer = PdfWriter()
    writer.add_blank_page(612, 792)
    blank = io.BytesIO()
    writer.write(blank)
    with pytest.raises(AnalysisError, match="No usable text"):
        extract_document("scan.pdf", blank.getvalue())
    writer.encrypt("secret")
    locked = io.BytesIO()
    writer.write(locked)
    with pytest.raises(AnalysisError, match="password"):
        extract_document("locked.pdf", locked.getvalue())


def test_zip_expansion_and_wrong_docx():
    for huge in [False, True]:
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("junk", b"0" * (21 * 1024 * 1024) if huge else b"wrong")
        with pytest.raises(AnalysisError):
            extract_document("x.docx", stream.getvalue())


def test_text_limits_and_binary_rejection():
    with pytest.raises(AnalysisError):
        validate_text("x" * 100001)
    with pytest.raises(AnalysisError):
        validate_text("\x01" * 50)


def test_pdf_page_limit():
    writer = PdfWriter()
    for _ in range(21):
        writer.add_blank_page(612, 792)
    stream = io.BytesIO()
    writer.write(stream)
    with pytest.raises(AnalysisError, match="20 pages"):
        extract_document("long.pdf", stream.getvalue())
