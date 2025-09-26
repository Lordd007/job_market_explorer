import asyncio, re, hashlib
from datetime import datetime
from typing import Iterable
import httpx
from bs4 import BeautifulSoup

from sqlalchemy.orm import Session
from db.session import SessionLocal
from db.models import Job, Skill, JobSkill
from core.hashing import text_hash
from ingest.skills_extract import build_matcher, extract

HEADERS = {"User-Agent": "JobMarketExplorer/0.1 (academic/portfolio use)"}

SOURCES = [
    # TODO Replace with specific boards you’ve confirmed are allowed to fetch
    {"name": "example_greenhouse", "list_url": "https://boards.greenhouse.io/examplecompany"},
]

async def fetch(client: httpx.AsyncClient, url: str) -> str:
    r = await client.get(url, headers=HEADERS, timeout=20.0)
    r.raise_for_status()
    return r.text

async def crawl_source(client: httpx.AsyncClient, src) -> Iterable[dict]:
    html = await fetch(client, src["list_url"])
    soup = BeautifulSoup(html, "html.parser")
    jobs = []
    # naive: find all <a> links to job detail pages under /jobs/
    for a in soup.select("a[href*='/jobs/']"):
        title = a.get_text(strip=True)
        href = a.get("href")
        if not href or not title:
            continue
        url = href if href.startswith("http") else f"https://boards.greenhouse.io{href}"
        jobs.append({"title": title, "url": url, "source": src["name"]})
    return jobs

async def enrich_job(client: httpx.AsyncClient, job_stub: dict) -> dict:
    html = await fetch(client, job_stub["url"])
    soup = BeautifulSoup(html, "html.parser")
    desc = soup.get_text(separator="\n", strip=True)
    # naive location/title parsing; improve later
    location = soup.select_one(".location")
    return {
        **job_stub,
        "description_text": desc[:200000],
        "city": location.get_text(strip=True) if location else "N/A",
        "posted_at": None  # unknown here; many ATS pages include it—parse when available
    }

async def run_once():
    async with httpx.AsyncClient(follow_redirects=True) as client:
        # crawl lists
        stubs_nested = await asyncio.gather(*(crawl_source(client, s) for s in SOURCES))
        stubs = [j for group in stubs_nested for j in group]

        # fetch details (limit concurrency)
        sem = asyncio.Semaphore(8)
        async def bound_enrich(stub):
            async with sem:  # rate limit
                return await enrich_job(client, stub)

        details = await asyncio.gather(*(bound_enrich(s) for s in stubs))
        save_to_db(details)

def save_to_db(items):
    db: Session = SessionLocal()
    build_matcher(db)

    added = 0
    for it in items:
        if not it.get("title") or not it.get("company"):
            # Some ATS lists don’t show company; you can hardcode per source, or skip.
            # For demo, derive company from domain token:
            it["company"] = it["source"].replace("_", " ").title()

        # dedupe by URL
        if it.get("url") and db.query(Job).filter_by(url=it["url"]).first():
            continue

        h = text_hash(it["title"], it["company"], it.get("description_text"))
        job = Job(
            title=it["title"],
            company=it["company"],
            city=it.get("city"),
            posted_at=it.get("posted_at"),
            source=it.get("source", "crawl"),
            url=it.get("url"),
            description_text=it.get("description_text", ""),
            desc_hash=h
        )
        db.add(job)
        db.flush()  # get job_id

        # skill extraction
        skills = extract(job.description_text or "")
        for name, conf in skills:
            skill = db.query(Skill).filter_by(name_canonical=name).first()
            if not skill:
                #TODO Optional: create unseen skills with low confidence
                skill = Skill(name_canonical=name)
                db.add(skill); db.flush()
            db.add(JobSkill(job_id=str(job.job_id), skill_id=skill.skill_id, confidence=conf, source="dict_v1"))

        added += 1

    db.commit()
    print(f"Ingested {added} jobs")

if __name__ == "__main__":
    asyncio.run(run_once())
