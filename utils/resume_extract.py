# utils/resume_extract.py
from __future__ import annotations
from pypdf import PdfReader
from docx import Document as DocxDocument
import io, re


WS_BAD = re.compile(r"[\u00A0\u200B\u200C\u200D\uFEFF]")  # NBSP & zero-widths
DASHES = re.compile(r"[–—]")                              # long dashes

def normalize_for_parse(s: str) -> str:
    if not s:
        return ""
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = WS_BAD.sub(" ", s)
    s = DASHES.sub("-", s)
    s = re.sub(r"[ \t]+", " ", s)
    # fix pdf-broken emails/domains
    s = re.sub(r"\s*@\s*", "@", s)
    s = re.sub(r"\s*\.\s*(com|edu|net)\b", r".\1", s, flags=re.I)
    # fix broken phone number digit runs
    s = re.sub(r"\(\s*(\d{3})\s*\)", r"(\1)", s)
    s = re.sub(r"(\d)\s+(\d)", r"\1\2", s)
    return s.strip()


def extract_text_from_pdf(data: bytes) -> str:
    reader = PdfReader(io.BytesIO(data))
    parts = []
    for page in reader.pages:
        parts.append(page.extract_text() or "")
    return normalize_for_parse("\n".join(parts))

def extract_text_from_docx(data: bytes) -> str:
    doc = DocxDocument(io.BytesIO(data))
    texts = [p.text for p in doc.paragraphs]
    return normalize_for_parse("\n".join(texts))

def extract_text_from_file(name: str, mime: str, data: bytes) -> str:
    n = (name or "").lower()
    m = (mime or "").lower()

    # PDF
    if m.startswith("application/pdf") or n.endswith(".pdf"):
        return extract_text_from_pdf(data)

    # DOCX only
    if n.endswith(".docx") or m == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return extract_text_from_docx(data)

    # Explicitly reject legacy .doc ( Word 97–2003 )
    if n.endswith(".doc") or m == "application/msword":
        # raise here so the endpoint can return a friendly 400:
        # "Please upload a PDF or DOCX"
        raise ValueError("Unsupported .doc format; please upload PDF or DOCX")

    # Plaintext fallback
    try:
        return normalize_for_parse(data.decode("utf-8", errors="ignore"))
    except Exception:
        return ""
