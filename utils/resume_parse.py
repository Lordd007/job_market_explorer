from __future__ import annotations
import re, datetime
from typing import Any, Dict, List, Optional, Tuple

EMAIL  = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)
PHONE  = re.compile(r"(\+?1[\s\-\.]?)?\(?\d{3}\)?[\s\-\.]?\d{3}[\s\-\.]?\d{4}")
LINK   = re.compile(r"(https?://[^\s)]+)", re.I)

US_STATES = {
  "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN","IA","KS","KY",
  "LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ","NM","NY","NC","ND",
  "OH","OK","OR","PA","RI","SC","SD","TN","TX","UT","VT","VA","WA","WV","WI","WY","DC"
}
LOC_US = re.compile(r"([A-Za-z][A-Za-z .'\-]+),\s*([A-Z]{2})(?:\s+(\d{5}(?:-\d{4})?))?")
YEAR_RANGE = re.compile(r"(\b19|20)\d{2}\s*-\s*(Present|\b(19|20)\d{2})", re.I)

SECTION_NAMES = {
    "summary": ["summary", "professional summary", "profile"],
    "experience": ["professional experience", "experience", "work experience", "work history"],
    "education": ["education & training", "education", "training"],
    "skills": ["technical skills", "skills"],
}

# date patterns
YEAR_RANGE   = re.compile(r"(\b19|20)\d{2}\s*-\s*(Present|Current|\b(19|20)\d{2})", re.I)
MONTHS       = r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*"
MONTH_RANGE  = re.compile(fr"{MONTHS}\.?\s+(\d{{4}})\s*-\s*(Present|Current|{MONTHS}\.?\s+\d{{4}})", re.I)


def _first(rx: re.Pattern, s: str) -> Optional[str]:
    m = rx.search(s) if s else None
    return m.group(0) if m else None

def _split_top_header(text: str) -> Dict[str, Any]:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()][:20]
    out = {"full_name": None, "city": None, "region": None, "country": None,
           "postal_code": None, "email": None, "phone": None, "linkedin": None}
    if not lines: return out

    # Name: first non-empty line with 2–4 capitalized tokens
    first = lines[0]
    toks = first.split()
    if 2 <= len(toks) <= 4 and all(t[:1].isupper() for t in toks):
        out["full_name"] = first

    head = " ".join(lines)

    # email/phone/linkedin: header first, fallback to whole doc
    out["email"] = (EMAIL.search(head) or EMAIL.search(text) or [None])
    out["email"] = out["email"].group(0) if hasattr(out["email"], "group") else None
    out["phone"] = (PHONE.search(head) or PHONE.search(text) or [None])
    out["phone"] = out["phone"].group(0) if hasattr(out["phone"], "group") else None
    urls = LINK.findall(head) or LINK.findall(text)
    out["linkedin"] = next((u for u in urls if "linkedin.com" in u.lower()), None)

    # location: ONLY accept from the header window, and validate state code
    mloc = LOC_US.search(head)
    if mloc and mloc.group(2) in US_STATES:
        out["city"], out["region"], out["postal_code"] = mloc.group(1), mloc.group(2), mloc.group(3)
        out["country"] = "US"

    return out

def _find_section(lines: List[str], variants: List[str]) -> int:
    low = [ln.lower().strip(" :") for ln in lines]
    for i, s in enumerate(low):
        if any(v in s for v in variants):
            return i
    return -1

def _section_span(lines: List[str], key: str) -> Tuple[int,int]:
    start_hdr = _find_section(lines, SECTION_NAMES[key])
    if start_hdr < 0: return (-1, -1)
    start = start_hdr + 1
    low = [ln.lower().strip(" :") for ln in lines]
    for j in range(start, len(lines)):
        if any(any(v in low[j] for v in vs) for vs in SECTION_NAMES.values()):
            return (start, j)
    return (start, len(lines))

def _clean(s: str) -> str:
    return s.strip("•-—– ").strip()

def _is_company_header(ln: str) -> bool:
    return ("-" in ln or "–" in ln or "—" in ln) and (LOC_US.search(ln) is not None)

def _split_blocks(block_lines: List[str]) -> List[List[str]]:
    out, cur = [], []
    for ln in block_lines:
        s = ln.strip()
        if not s:
            if cur: out.append(cur); cur=[]
            continue
        if cur and _is_company_header(s):
            out.append(cur); cur=[s]
        else:
            cur.append(s)
    if cur: out.append(cur)
    return out

def _parse_experience(lines: List[str]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    blocks = _split_blocks(lines)
    for b in blocks:
        if not b: continue
        head = _clean(b[0]); low = head.lower()
        if low in ("professional experience","experience","work experience","work history"):
            continue

        company, location, start, end, role = None, None, None, None, None

        parts = re.split(r"\s+[–—-]\s+|\t+", head)
        if parts: company = parts[0]
        mloc = LOC_US.search(head)
        if mloc:
            location = f"{mloc.group(1)}, {mloc.group(2)}" + (f" {mloc.group(3)}" if mloc.group(3) else "")

        def _pull_dates(s: str):
            m = YEAR_RANGE.search(s)
            if m: return m.group(1), m.group(2)
            m2 = MONTH_RANGE.search(s)
            if m2:
                start_y = m2.group(2)
                end_g = m2.group(3)  # "Present"/"Current" or month
                if end_g and end_g.lower() in ("present","current"):
                    return start_y, "Present"
                # if month on end, also need year; simplified: return the whole match
                return m2.group(0), None
            return None

        # look ahead 0–3 lines for role & dates
        idx_after_header = 1
        for k in range(min(3, len(b)-1)):
            ln = _clean(b[1+k])
            if not role and len(ln.split()) <= 10 and "education" not in ln.lower():
                role = role or ln
            got = _pull_dates(ln)
            if got:
                start, end = got
            idx_after_header += 1

        bullets = [ _clean(x) for x in b[idx_after_header:] ]
        bullets = [x for x in bullets if x]

        if not (company or role):
            continue
        out.append({
            "title": role or company,
            "company": company if role else None,
            "location": location,
            "start": start, "end": end,
            "bullets": bullets[:25],
        })
    return out


def _looks_like_degree(s: str) -> bool:
    s = s.lower()
    return (
        "master" in s or "bachelor" in s or "degree" in s or "certificate" in s or
        "university" in s or "college" in s or re.search(r"(19|20)\d{2}", s) is not None
    )

def _parse_education(lines: List[str]) -> List[Dict[str, Any]]:
    out = []
    for ln in lines:
        li = _clean(ln)
        if not li: continue
        if not _looks_like_degree(li):
            continue
        degree, school, year = None, None, None
        parts = [p.strip() for p in re.split(r"\s*\|\s*|—|-{2,}", li) if p.strip()]
        if parts:
            degree = parts[0]
            if len(parts) > 1:
                school = parts[1]
        m = re.search(r"(19|20)\d{2}", li)
        if m: year = m.group(0)
        out.append({"degree": degree, "school": school, "year": year})
    return out

def parse_resume_text(text: str) -> Dict[str, Any]:
    lines = [ln.rstrip() for ln in text.splitlines()]
    head = _split_top_header(text)

    s_sum = _section_span(lines, "summary")
    s_exp = _section_span(lines, "experience")
    s_edu = _section_span(lines, "education")
    s_skl = _section_span(lines, "skills")

    summary = "\n".join(lines[s_sum[0]:s_sum[1]]).strip() if s_sum != (-1,-1) else None
    exp_lines = lines[s_exp[0]:s_exp[1]] if s_exp != (-1,-1) else []
    edu_end   = s_skl[0] if s_skl != (-1,-1) else (s_edu[1] if s_edu != (-1,-1) else -1)
    edu_lines = lines[s_edu[0]:edu_end] if s_edu != (-1,-1) else []

    experience = _parse_experience(exp_lines)
    education  = _parse_education(edu_lines)

    years_experience = None
    nums = re.findall(r"(\d+(?:\.\d+)?)\s+years", text, flags=re.I)
    if nums:
        try: years_experience = max(float(x) for x in nums)
        except: pass
    if years_experience is None:
        totals = []
        for m in YEAR_RANGE.finditer("\n".join(exp_lines)):
            a = int(m.group(1))
            b = (datetime.datetime.now().year if m.group(2).lower()=="present" else int(m.group(2)))
            if 1900 <= a <= b <= 2100:
                totals.append(b-a)
        if totals:
            years_experience = max(totals)

    links = []
    if head.get("linkedin"):
        links.append({"kind":"linkedin","url":head["linkedin"]})

    return {
        "contact": head,
        "summary": summary or None,
        "experience": experience,
        "education": education,
        "years_experience": years_experience,
        "links": links,
    }
