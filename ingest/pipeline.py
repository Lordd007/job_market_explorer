# ingest/pipeline.py  (PATCHED)
import asyncio
import re
from datetime import datetime, timedelta
from typing import Iterable, List, Dict, Any, Optional, Tuple
import os
import httpx
from bs4 import BeautifulSoup

from sqlalchemy.orm import Session
from sqlalchemy import or_

from db.session import SessionLocal
from db.models import Job, Skill, JobSkill
from core.hashing import text_hash
from ingest.skills_extract import build_matcher, extract

from ingest.dedupe import canonicalize_url, normalize_text, sha256_bytes
from sqlalchemy.exc import IntegrityError
from sqlalchemy.dialects.postgresql import insert
from utils.seniority import infer_seniority
from utils.salary import normalize_salary

HEADERS = {"User-Agent": "JobMarketExplorer/0.1 (academic/portfolio use)"}
CONCURRENCY = 8
REQUEST_TIMEOUT = 20.0
MAX_RETRIES = 3
RETRY_BACKOFF = 0.75  # seconds
RATE_LIMIT_SECONDS = 1.0  # be gentle when hitting public endpoints

# --- NEW: helpers ------------------------------------------------------------

def _rate_limit():
    return asyncio.sleep(RATE_LIMIT_SECONDS)

async def _get_json(client: httpx.AsyncClient, url: str, params: Optional[Dict[str, Any]] = None) -> Any:
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r = await client.get(url, headers=HEADERS, params=params or {}, timeout=REQUEST_TIMEOUT)
            r.raise_for_status()
            return r.json()
        except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.HTTPStatusError, httpx.TransportError):
            if attempt == MAX_RETRIES:
                raise
            await asyncio.sleep(RETRY_BACKOFF * attempt)

async def fetch(client: httpx.AsyncClient, url: str) -> str:
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r = await client.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
            r.raise_for_status()
            return r.text
        except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.HTTPStatusError, httpx.TransportError):
            if attempt == MAX_RETRIES:
                raise
            await asyncio.sleep(RETRY_BACKOFF * attempt)

# --- EXISTING: HTML crawl (fallback/explicit only) ---------------------------

async def crawl_source_html_list(client: httpx.AsyncClient, list_url: str) -> List[Dict[str, str]]:
    # Only use this for sources you’ve confirmed are allowed to fetch.
    html = await fetch(client, list_url)
    soup = BeautifulSoup(html, "html.parser")
    jobs: List[Dict[str, str]] = []
    for a in soup.select("a[href*='/jobs/']"):
        title = a.get_text(strip=True)
        href = a.get("href")
        if not href or not title:
            continue
        if href.startswith("http"):
            url = href
        else:
            url = "https://boards.greenhouse.io" + href
        jobs.append({"title": title, "url": url, "source": "html"})
    return jobs

def _parse_posted_at(soup: BeautifulSoup) -> Optional[datetime]:
    text = soup.get_text(" ", strip=True)
    m = re.search(r"posted\s+on\s+([A-Za-z]{3,9}\s+\d{1,2},\s+\d{4})", text, re.I)
    if m:
        try:
            return datetime.strptime(m.group(1), "%B %d, %Y")
        except ValueError:
            pass
    return None

async def enrich_job_html(client: httpx.AsyncClient, job_stub: Dict[str, Any]) -> Dict[str, Any]:
    html = await fetch(client, job_stub["url"])
    soup = BeautifulSoup(html, "html.parser")
    desc = soup.get_text(separator="\n", strip=True)
    loc_el = soup.select_one(".location, .job-location, [data-qa='job-location']")
    city = loc_el.get_text(strip=True) if loc_el else "N/A"
    return {
        **job_stub,
        "description_text": desc[:200000],
        "city": city,
        "posted_at": _parse_posted_at(soup),
    }

# --- NEW: Greenhouse JSON adapter (per-company) ------------------------------

async def greenhouse_company_jobs(client: httpx.AsyncClient, company_slug: str, days: int) -> List[Dict[str, Any]]:
    # https://boards-api.greenhouse.io/v1/boards/{slug}/jobs
    url = f"https://boards-api.greenhouse.io/v1/boards/{company_slug}/jobs"
    data = await _get_json(client, url, params={"content": "true"})
    cutoff = datetime.utcnow() - timedelta(days=days)
    out: List[Dict[str, Any]] = []
    for j in data.get("jobs", []):
        posted = j.get("updated_at") or j.get("created_at")
        posted_dt = None
        if posted:
            # "2024-09-01T12:34:56Z"
            try:
                posted_dt = datetime.fromisoformat(posted.replace("Z", "+00:00")).replace(tzinfo=None)
            except Exception:
                posted_dt = None
        if posted_dt and posted_dt < cutoff:
            continue

        loc = (j.get("location") or {}).get("name") or ""
        city = (loc.split(",")[0].strip() if loc else None) or None

        out.append({
            "title": j.get("title", "").strip(),
            "company": (j.get("offices") or [{}])[0].get("name")
                       or (j.get("departments") or [{}])[0].get("name")
                       or "Unknown",
            "description_text": (j.get("content") or "")[:200000],
            "url": j.get("absolute_url"),
            "city": city or "N/A",
            "posted_at": posted_dt,
            "source": f"greenhouse:{company_slug}",
        })
        await _rate_limit()
    return out

# --- NEW: Lever JSON adapter (per-company) -----------------------------------

async def lever_company_jobs(client: httpx.AsyncClient, company_slug: str, days: int) -> List[Dict[str, Any]]:
    # https://api.lever.co/v0/postings/{slug}?mode=json
    url = f"https://api.lever.co/v0/postings/{company_slug}"
    data = await _get_json(client, url, params={"mode": "json"})
    cutoff = datetime.utcnow() - timedelta(days=days)
    out: List[Dict[str, Any]] = []
    for j in data:
        posted_ms = j.get("createdAt")
        posted_dt = datetime.utcfromtimestamp(posted_ms / 1000) if posted_ms else None
        if posted_dt and posted_dt < cutoff:
            continue
        loc = (j.get("categories") or {}).get("location") or ""
        city = (loc.split(",")[0].strip() if loc else None) or None
        out.append({
            "title": j.get("text", "").strip(),
            "company": (j.get("categories") or {}).get("team") or "Unknown",
            "description_text": (j.get("descriptionPlain") or j.get("description") or "")[:200000],
            "url": j.get("hostedUrl"),
            "city": city or "N/A",
            "posted_at": posted_dt,
            "source": f"lever:{company_slug}",
        })
        await _rate_limit()
    return out

# --- EXISTING: orchestrate ---------------------------------------------------

async def run_once(source: str = "seed", days: int = 7):
    async with httpx.AsyncClient(follow_redirects=True, headers=HEADERS, timeout=REQUEST_TIMEOUT) as client:

        items: List[Dict[str, Any]] = []

        if source == "seed":
            # You already have your seed helper; keep it.
            from ingest.seed_jobs import iter_seed_jobs
            items = list(iter_seed_jobs(days=days))

        elif source.startswith("greenhouse:"):
            slug = source.split(":", 1)[1]
            items = await greenhouse_company_jobs(client, slug, days)

        elif source.startswith("lever:"):
            slug = source.split(":", 1)[1]
            items = await lever_company_jobs(client, slug, days)

        elif source.startswith("html:"):
            # explicit HTML crawl only when allowed
            list_url = source.split(":", 1)[1]
            stubs = await crawl_source_html_list(client, list_url)
            sem = asyncio.Semaphore(CONCURRENCY)

            async def bound_enrich(stub):
                async with sem:
                    try:
                        return await enrich_job_html(client, stub)
                    except Exception as e:
                        print(f"[warn] enrich failed for {stub.get('url')}: {e}")
                        return None

            details = await asyncio.gather(*(bound_enrich(s) for s in stubs))
            items = [d for d in details if d]

        else:
            raise SystemExit(f"Unknown source {source}")

        save_to_db(items)

def save_to_db(items, db: Optional[Session] = None) -> int:
    """Persist items. If `db` is None, manage our own SessionLocal()."""
    own_session = False
    if db is None:
        db = SessionLocal()
        own_session = True

    try:
        build_matcher(db)

        added = 0
        for it in items:
            if not it.get("company"):
                it["company"] = it.get("source", "crawl").replace("_", " ").title()

            # URL dedupe
            canon_url = canonicalize_url(it.get("url", ""))
            url_hash = sha256_bytes(canon_url) if canon_url else None
            # 1) prefer url_hash if present
            if url_hash and db.query(Job).filter_by(url_hash=url_hash).first():
                continue
            # 2) transition safety: also check by URL (existing rows may have url_hash=NULL)
            raw_url = it.get("url")
            existing = None
            if canon_url or raw_url:
                existing = db.query(Job).filter( or_(Job.url == canon_url, Job.url == raw_url)).first()
                if existing:
                    # backfill missing hashes on the existing row, then skip
                    if url_hash and not existing.url_hash:
                        existing.url_hash = url_hash
                    pass


            if url_hash and db.query(Job).filter_by(url_hash=url_hash).first():
                continue

            # hash dedupe
            desc_bin = sha256_bytes(normalize_text(it.get("description_text", "")))


            if db.query(Job).filter_by(desc_hash=desc_bin).first():
                continue

            if existing:
                if not existing.desc_hash:
                    existing.desc_hash = desc_bin
                continue

            job = Job(
                title=it["title"],
                company=it["company"],
                city=it.get("city"),
                posted_at=it.get("posted_at"),
                source=it.get("source", "crawl"),
                url=it.get("url"),
                url_hash=url_hash,
                description_text=it.get("description_text", ""),
                desc_hash=desc_bin,
                seniority=infer_seniority(it.get("title")),
                salary_usd_annual=normalize_salary(
                    it.get("salary_min"),
                    it.get("salary_max"),
                    it.get("salary_currency"),
                    it.get("salary_period"),
                    ),
            )
            db.add(job)
            #db.flush()

            try:
                db.flush()
            except IntegrityError:
                # Race or leftover duplicates on url — recover by updating existing row
                db.rollback()
                ex = db.query(Job).filter(
                    Job.url == it.get("url")
                ).first()
                if ex:
                    if url_hash and not ex.url_hash:
                        ex.url_hash = url_hash
                    if not ex.desc_hash:
                        ex.desc_hash = desc_bin
                    db.flush()
                    continue
                else:
                    raise

            for name, conf in extract(job.description_text or ""):
                skill = db.query(Skill).filter_by(name_canonical=name).first()
                if not skill:
                    # dictionary not seeded / mismatch — skip or log
                    # logger.warning(f"Unknown skill {name} on job {job.job_id}")
                    continue


                stmt = insert(JobSkill).values(
                    job_id=job.job_id,
                    skill_id=skill.skill_id,
                    confidence=conf,
                    source="dict_v1",
                ).on_conflict_do_update(
                    index_elements=[JobSkill.job_id, JobSkill.skill_id],
                    set_={"confidence": conf, "source": "dict_v1"}
                )
                db.execute(stmt)

            added += 1

        db.commit()
        print(f"Ingested {added} jobs")
        return added
    finally:
        if own_session:
            db.close()

# --- CLI entrypoint ----------------------------------------------------------

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default=os.getenv("JME_SOURCE", "seed"),
                    help="seed | greenhouse:<slug> | lever:<slug> | html:<list_url>")
    ap.add_argument("--days", type=int, default=int(os.getenv("JME_DAYS", "7")))
    args = ap.parse_args()
    asyncio.run(run_once(source=args.source, days=args.days))
