# ingest/pipeline.py
import asyncio
import re
from datetime import datetime
from typing import Iterable, List, Dict, Any, Optional
import httpx
from bs4 import BeautifulSoup

from sqlalchemy.orm import Session
from sqlalchemy import or_

from db.session import SessionLocal
from db.models import Job, Skill, JobSkill
from core.hashing import text_hash
from ingest.skills_extract import build_matcher, extract

HEADERS = {"User-Agent": "JobMarketExplorer/0.1 (academic/portfolio use)"}
CONCURRENCY = 8
REQUEST_TIMEOUT = 20.0
MAX_RETRIES = 3
RETRY_BACKOFF = 0.75  # seconds

SOURCES: List[Dict[str, str]] = [
    # TODO: Replace with boards you’ve confirmed are allowed to fetch
    {"name": "example_greenhouse", "list_url": "https://boards.greenhouse.io/examplecompany"},
]


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


async def crawl_source(client: httpx.AsyncClient, src: Dict[str, str]) -> List[Dict[str, str]]:
    html = await fetch(client, src["list_url"])
    soup = BeautifulSoup(html, "html.parser")
    jobs: List[Dict[str, str]] = []

    # naive: find all <a> links to job detail pages under /jobs/
    for a in soup.select("a[href*='/jobs/']"):
        title = a.get_text(strip=True)
        href = a.get("href")
        if not href or not title:
            continue
        if href.startswith("http"):
            url = href
        else:
            # best-effort join; Greenhouse links are usually absolute or root-relative
            url = "https://boards.greenhouse.io" + href
        jobs.append({"title": title, "url": url, "source": src["name"]})
    return jobs


def _parse_posted_at(soup: BeautifulSoup) -> Optional[datetime]:
    # TODO Many ATS pages have a "posted" label somewhere; this is just a placeholder
    # Improve per-source once you pick real boards
    text = soup.get_text(" ", strip=True)
    m = re.search(r"posted\s+on\s+([A-Za-z]{3,9}\s+\d{1,2},\s+\d{4})", text, re.I)
    if m:
        try:
            return datetime.strptime(m.group(1), "%B %d, %Y")
        except ValueError:
            pass
    return None


async def enrich_job(client: httpx.AsyncClient, job_stub: Dict[str, Any]) -> Dict[str, Any]:
    html = await fetch(client, job_stub["url"])
    soup = BeautifulSoup(html, "html.parser")
    desc = soup.get_text(separator="\n", strip=True)

    # naive location parsing; customize per source
    loc_el = soup.select_one(".location, .job-location, [data-qa='job-location']")
    city = loc_el.get_text(strip=True) if loc_el else "N/A"

    return {
        **job_stub,
        "description_text": desc[:200000],  # keep size in check
        "city": city,
        "posted_at": _parse_posted_at(soup),
    }


async def run_once():
    async with httpx.AsyncClient(follow_redirects=True) as client:
        stubs_nested = await asyncio.gather(*(crawl_source(client, s) for s in SOURCES))
        stubs = [j for group in stubs_nested for j in group]

        # fetch details with bounded concurrency
        sem = asyncio.Semaphore(CONCURRENCY)

        async def bound_enrich(stub):
            async with sem:
                try:
                    return await enrich_job(client, stub)
                except Exception as e:
                    # Log and skip broken pages; don’t fail the whole run
                    print(f"[warn] enrich failed for {stub.get('url')}: {e}")
                    return None

        details = await asyncio.gather(*(bound_enrich(s) for s in stubs))
        items = [d for d in details if d]
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
            # ensure company present
            if not it.get("company"):
                it["company"] = it.get("source", "crawl").replace("_", " ").title()

            # URL dedupe
            if it.get("url") and db.query(Job).filter_by(url=it["url"]).first():
                continue

            # hash dedupe
            h = text_hash(it.get("title"), it.get("company"), it.get("description_text"))
            if db.query(Job).filter_by(desc_hash=h).first():
                continue

            job = Job(
                title=it["title"],
                company=it["company"],
                city=it.get("city"),
                posted_at=it.get("posted_at"),
                source=it.get("source", "crawl"),
                url=it.get("url"),
                description_text=it.get("description_text", ""),
                desc_hash=h,
            )
            db.add(job)
            db.flush()  # populates job.job_id

            # skills
            for name, conf in extract(job.description_text or ""):
                skill = db.query(Skill).filter_by(name_canonical=name).first()
                if not skill:
                    skill = Skill(name_canonical=name)
                    db.add(skill)
                    db.flush()
                db.add(JobSkill(job_id=str(job.job_id), skill_id=skill.skill_id, confidence=conf, source="dict_v1"))

            added += 1

        db.commit()
        print(f"Ingested {added} jobs")
        return added
    finally:
        if own_session:
            db.close()