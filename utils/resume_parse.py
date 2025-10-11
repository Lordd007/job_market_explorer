from __future__ import annotations
import re, json
from typing import Any, Dict, List, Tuple, Optional
import spacy

# ----------------- regexes -----------------
EMAIL  = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)
PHONE  = re.compile(r"(\+?1[\s\-\.]?)?\(?\d{3}\)?[\s\-\.]?\d{3}[\s\-\.]?\d{4}")
LINK   = re.compile(r"(https?://[^\s)]+)", re.I)
# City, ST  or  City, ST ZIP
LOC_US = re.compile(r"([A-Za-z][A-Za-z .'\-]+),\s*([A-Z]{2})(?:\s+(\d{5}(?:-\d{4})?))?")

SECTION_KEYS = {
    "summary": ["summary", "professional summary", "profile"],
    "experience": ["professional experience", "experience", "work experience", "work history"],
    "education": ["education & training", "education", "training"],
    "skills": ["technical skills", "skills"],
}

_nlp = None
def nlp():
    global _nlp
    if _nlp is None:
        _nlp = spacy.load("en_core_web_sm", disable=["lemmatizer","parser"])
    return _nlp

# ----------------- helpers -----------------
def _first_match(rx, s: str) -> Optional[str]:
    if not s: return None
    m = rx.search(s)
    return m.group(0) if m else None

def _find_section_span(lines: List[str], keys: List[str]) -> Tuple[int, int]:
    """Return (start_line, end_line_exclusive) for the first matching section."""
    # find first header line containing any key
    start = -1
    low = [ln.lower().strip(" :") for ln in lines]
    for i, txt in enumerate(low):
        if any(k in txt for k in keys):
            start = i + 1
            break
    if start < 0:
        return (-1, -1)
    # stop at next header that looks like a section
    for j in range(start, len(lines)):
        t = low[j]
        if any(any(k in t for k in ks) for ks in SECTION_KEYS.values()):
            return (start, j)
    return (start, len(lines))

def _header_guess(text: str) -> Dict[str, Any]:
    """
    Use first ~10 lines. Pattern for name on very first line,
    and capture contact (email/phone/linkedin), and US location if present.
    """
    out = {"full_name": None, "email": None, "phone": None,
           "city": None, "region": None, "country": None, "postal_code": None,
           "linkedin": None}
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()][:12]
    head = "\n".join(lines)
    # Name: trust the very first non-empty line if it looks like 2–3 words, capitalized
    if lines:
        maybe_name = lines[0]
        if 2 <= len(maybe_name.split()) <= 4:
            # both words start with capital
            if all(w[:1].isupper() for w in maybe_name.split()):
                out["full_name"] = maybe_name

    out["email"] = _first_match(EMAIL, head) or _first_match(EMAIL, text)
    out["phone"] = _first_match(PHONE, head) or _first_match(PHONE, text)
    links = LINK.findall(head)
    out["linkedin"] = next((u for u in links if "linkedin.com" in u.lower()), None)

    mloc = LOC_US.search(head)
    if not mloc:
        # also try rest of text for City, ST
        mloc = LOC_US.search(text[:2000])
    if mloc:
        out["city"], out["region"], out["postal_code"] = mloc.group(1), mloc.group(2), mloc.group(3)
        out["country"] = "US"
    return out

def _split_blocks(lines: List[str]) -> List[List[str]]:
    """Split section body into chunks by empty line."""
    blocks, cur = [], []
    for ln in lines:
        if ln.strip():
            cur.append(ln.strip())
        elif cur:
            blocks.append(cur); cur = []
    if cur: blocks.append(cur)
    return blocks

def _clean_header_row(row: str) -> str:
    return row.strip("•-—– ").strip()

def _parse_experience(lines: List[str]) -> List[Dict[str, Any]]:
    """
    Expect pairs like:
      Company – Location – YYYY – YYYY/Present
      Role – YYYY – YYYY/Present
      bullets…
    and skip section headers like "Professional Experience".
    """
    out: List[Dict[str, Any]] = []
    blocks = _split_blocks(lines)
    for b in blocks:
        if not b: continue
        head = _clean_header_row(b[0])
        low  = head.lower()
        # skip obvious section header lines
        if low in ("experience", "professional experience", "work experience", "work history"):
            continue

        # Try to pull company/location/daterange from first line
        # e.g., "Hamilton Education - Carmel Valley, CA    2018 – Present"
        company, location, start, end = None, None, None, None
        # split on dash variants
        parts = re.split(r"\s+[–—-]\s+|\t+", head)
        if len(parts) >= 1: company = parts[0]
        # look for a US location pattern anywhere in head
        mloc = LOC_US.search(head)
        if mloc:
            location = f"{mloc.group(1)}, {mloc.group(2)}" + (f" {mloc.group(3)}" if mloc.group(3) else "")
        # date range pattern in any form like "2018 – Present" or "2020 – 2022"
        mdate = re.search(r"(\b20\d{2}|19\d{2})\s*[–—-]\s*(Present|\b20\d{2}|19\d{2})", head, flags=re.I)
        if mdate:
            start, end = mdate.group(1), mdate.group(2)

        # Next line might be a Role – Dates (better dates override)
        role = None
        if len(b) >= 2:
            role_line = _clean_header_row(b[1])
            # If role line contains dates, prefer them
            mdate2 = re.search(r"(\b20\d{2}|19\d{2})\s*[–—-]\s*(Present|\b20\d{2}|19\d{2})", role_line, flags=re.I)
            if mdate2:
                start, end = mdate2.group(1), mdate2.group(2)
                role = re.split(r"\s+[–—-]\s+|\t+", role_line)[0]
            else:
                # treat as role even without dates
                if not role and len(role_line.split()) <= 8:
                    role = role_line

        # gather remaining bullet lines
        bullets = [ _clean_header_row(x) for x in (b[2:] if role else b[1:]) ]
        bullets = [x.lstrip("•- ").strip() for x in bullets if x]

        # Skip if the "company" looks like a leftover header
        bad_titles = {"experience","professional experience","work experience","work history"}
        if (company or role) and (company or role).lower() not in bad_titles:
            out.append({
                "title": role or company,      # choose whichever is job-like
                "company": company if role else None,
                "location": location,
                "start": start, "end": end,
                "bullets": bullets[:20],
            })
    return out

def _parse_education(lines: List[str]) -> List[Dict[str, Any]]:
    out = []
    for ln in lines:
        li = _clean_header_row(ln)
        if not li: continue
        # e.g., "Master of Science in Data Science | University of Colorado, Boulder (completion date: October 2025)"
        # or "Bachelor of Science ... | University of California, Irvine"
        degree = None; school = None; year = None
        # pick year if present
        myear = re.search(r"(19|20)\d{2}", li)
        if myear: year = myear.group(0)
        # split on "|" or "-" to separate degree/school
        parts = [p.strip() for p in re.split(r"\s*\|\s*|—|-{2,}", li) if p.strip()]
        if parts:
            degree = parts[0]
            if len(parts) > 1:
                school = parts[1]
        out.append({"degree": degree, "school": school, "year": year})
    return out

def parse_resume_text(text: str) -> Dict[str, Any]:
    lines = [ln.rstrip() for ln in text.splitlines()]
    # HEAD
    head_info = _header_guess(text)

    # locate sections
    low = [ln.lower().strip(" :") for ln in lines]
    def span(key: str) -> Tuple[int,int]:
        return _find_section_span(lines, SECTION_KEYS[key])

    s_sum  = span("summary")
    s_exp  = span("experience")
    s_edu  = span("education")
    s_sk   = span("skills")

    summary = "\n".join(lines[s_sum[0]:s_sum[1]]).strip() if s_sum != (-1,-1) else None
    exp_lines = lines[s_exp[0]:s_exp[1]] if s_exp != (-1,-1) else []
    edu_lines = lines[s_edu[0]:s_edu[1]] if s_edu != (-1,-1) else []

    experience = _parse_experience(exp_lines)
    education  = _parse_education(edu_lines)

    # heuristics for years exp: prefer explicit phrases; else derive from ranges in experience
    yrs = re.findall(r"(\d+(?:\.\d+)?)\s+years", text, flags=re.I)
    years_experience = None
    if yrs:
        try: years_experience = max(float(x) for x in yrs)
        except: pass
    if years_experience is None:
        # min estimate from explicit year ranges
        rngs = re.findall(r"(19|20)\d{2}\s*[–—-]\s*(Present|(19|20)\d{2})", "\n".join(exp_lines), flags=re.I)
        vals = []
        for a,b,_ in rngs:
            try:
                a = int(a)
                b = (datetime.datetime.now().year if b.lower()=="present" else int(b))
                if 1900 <= a <= 2100 and 1900 <= b <= 2100 and b >= a:
                    vals.append((b-a))
            except: pass
        if vals:
            years_experience = max(vals)  # very rough upper bound

    links = []
    if head_info.get("linkedin"):
        links.append({"kind":"linkedin","url":head_info["linkedin"]})

    return {
        "contact": head_info,
        "summary": summary or None,
        "experience": experience,
        "education": education,
        "years_experience": years_experience,
        "links": links,
    }
