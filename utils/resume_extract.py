# utils/resume_extract.py
from __future__ import annotations
from pypdf import PdfReader
from docx import Document as DocxDocument
import io, re

def _clean(text: str) -> str:
    s = re.sub(r"\r\n?", "\n", text)
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()

def extract_text_from_pdf(data: bytes) -> str:
    reader = PdfReader(io.BytesIO(data))
    parts = []
    for page in reader.pages:
        parts.append(page.extract_text() or "")
    return _clean("\n".join(parts))

def extract_text_from_docx(data: bytes) -> str:
    doc = DocxDocument(io.BytesIO(data))
    texts = [p.text for p in doc.paragraphs]
    return _clean("\n".join(texts))

def extract_text_from_file(name: str, mime: str, data: bytes) -> str:
    n = (name or "").lower()
    m = (mime or "").lower()
    if m.startswith("application/pdf") or n.endswith(".pdf"):
        return extract_text_from_pdf(data)
    if m in ("application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword") \
        or n.endswith(".docx"):
        return extract_text_from_docx(data)
    # plaintext fallback
    try:
        return _clean(data.decode("utf-8", errors="ignore"))
    except Exception:
        return ""
