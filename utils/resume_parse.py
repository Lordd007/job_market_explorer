from __future__ import annotations
import re, json
from typing import Any, Dict, List, Tuple
import spacy

_EMAIL  = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)
_PHONE  = re.compile(r"(\+?\d[\d \-().]{8,}\d)")
_LINK   = re.compile(r"(https?://[^\s)]+)", re.I)
_POSTAL = re.compile(r"\b\d{5}(?:-\d{4})?\b")  # US zip; extend for CA if needed

_nlp = None
def nlp():
    global _nlp
    if _nlp is None:
        _nlp = spacy.load("en_core_web_sm", disable=["lemmatizer","parser"])
    return _nlp

def _first_match(rx, s: str|None) -> str|None:
    if not s: return None
    m = rx.search(s)
    return m.group(0) if m else None

def _header_info(text: str) -> dict:
    """Best-effort header block: first ~8 lines."""
    lines = text.splitlines()
    head = "\n".join(lines[:8])
    email = _first_match(_EMAIL, head) or _first_match(_EMAIL, text)
    phone = _first_match(_PHONE, head) or _first_match(_PHONE, text)
    links = _LINK.findall(head)
    linkedin = next((u for u in links if "linkedin.com" in u.lower()), None)

    # location from first GPE/LOC entities in header
    doc = nlp()(head)
    cities = [e.text for e in doc.ents if e.label_ in ("GPE","LOC")]
    city = cities[0] if cities else None
    postal = _first_match(_POSTAL, head)

    # name: first PERSON in header (or first line if looks like a name)
    persons = [e.text for e in doc.ents if e.label_ == "PERSON"]
    full_name = persons[0] if persons else (lines[0].strip() if len(lines[0].split()) in (2,3) else None)

    # Attempt region/country from header tokens
    region, country = None, None
    if city and "," in city:
        parts = [p.strip() for p in city.split(",")]
        if len(parts) >= 2:
            city = parts[0]
            region = parts[1]
    return {
        "full_name": full_name, "email": email, "phone": phone,
        "city": city, "region": region, "country": None, "postal_code": postal,
        "linkedin": linkedin,
    }

def _find_section_indices(text: str, keys: List[str]) -> List[Tuple[str,int]]:
    lines = text.splitlines()
    out = []
    for i, line in enumerate(lines):
        low = line.lower().strip(" :")
        for k in keys:
            if k in low:
                out.append((k, i))
                break
    return out

def _extract_section(text: str, start_key_variants: List[str], stop_keys: List[str]) -> str:
    lines = text.splitlines()
    idxs = _find_section_indices(text, start_key_variants)
    if not idxs: return ""
    start = idxs[0][1] + 1
    # stop at next top-level section
    for i in range(start, len(lines)):
        low = lines[i].lower().strip(" :")
        if any(k in low for k in stop_keys):
            return "\n".join(lines[start:i]).strip()
    return "\n".join(lines[start:]).strip()

def parse_resume_text(text: str) -> Dict[str, Any]:
    info = _header_info(text)

    # summary
    summary = _extract_section(
        text,
        ["summary", "professional summary", "profile"],
        ["experience", "work history", "education", "skills", "certifications"]
    )

    # experience
    exp_block = _extract_section(
        text,
        ["experience", "work experience", "work history", "professional experience"],
        ["education", "skills", "certifications"]
    )
    experiences = []
    if exp_block:
        # crude splitter: blank lines separate positions
        for chunk in re.split(r"\n\s*\n", exp_block):
            lines = [l.strip() for l in chunk.splitlines() if l.strip()]
            if not lines: continue
            header = lines[0]
            # try "Title – Company – Location"
            parts = re.split(r"\s+[-–]\s+|\s•\s", header)
            title = parts[0] if parts else header
            company = parts[1] if len(parts) > 1 else None
            location = parts[2] if len(parts) > 2 else None
            # bullets are the rest
            bullets = [l.lstrip("•- ").strip() for l in lines[1:]]
            experiences.append({
                "title": title, "company": company, "location": location,
                "start": None, "end": None, "bullets": [b for b in bullets if b]
            })

    # education
    edu_block = _extract_section(text, ["education", "training"], ["skills", "certifications", "projects"])
    educations = []
    if edu_block:
        for line in edu_block.splitlines():
            li = line.strip("•- ").strip()
            if not li: continue
            # crude split: "Degree | School | Year"
            parts = [p.strip() for p in re.split(r"\||,|•|-{2,}", li) if p.strip()]
            degree, school, year = None, None, None
            if parts:
                degree = parts[0]
                if len(parts) > 1: school = parts[1]
                m = re.search(r"(20\d{2}|19\d{2})", li)
                if m: year = m.group(1)
            educations.append({"degree": degree, "school": school, "year": year})

    # years of exp heuristic
    yrs = re.findall(r"(\d+(?:\.\d+)?)\s+years", text, flags=re.I)
    years_experience = None
    if yrs:
        try: years_experience = max(float(x) for x in yrs)
        except: pass

    return {
        "contact": info,
        "summary": summary or None,
        "experience": experiences,
        "education": educations,
        "years_experience": years_experience,
        "links": [{"kind":"linkedin","url":info["linkedin"]}] if info.get("linkedin") else [],
    }
