from __future__ import annotations
import json, os, asyncio, time
from typing import Dict, Any, List
from ingest.sources import REGISTRY
from ingest import pipeline
from db.session import SessionLocal

REQUEST_DELAY = float(os.getenv("REQUEST_DELAY", "0.25"))
SOURCES_JSON = os.getenv("SOURCES_JSON", "data/sources.json")

async def run_once(source: str, days: int = 14):
    provider, board = source.split(":", 1)
    adapter = REGISTRY[provider](request_delay=REQUEST_DELAY)

    raw = adapter.fetch_jobs(board)
    items = [  # map to pipeline’s expected dict
        {
            "title": j.get("title") or j.get("text",""),
            "company": j.get("company") or (j.get("categories") or {}).get("team") or board,
            "description_text": j.get("description_text") or j.get("description") or j.get("content","") or "",
            "url": j.get("absolute_url") or j.get("hostedUrl") or j.get("applyUrl") or "",
            "city": (j.get("location") or {}).get("name") or (j.get("categories") or {}).get("location") or "N/A",
            "posted_at": None,  # fill if you parse it
            "source": f"{provider}:{board}",
        }
        for j in raw
    ]

    # Option 1: let save_to_db create Session
    pipeline.save_to_db(items)

    # Option 2: manage Session explicitly
    # with SessionLocal() as db:
    #     pipeline.save_to_db(items, db=db)

def main(path=SOURCES_JSON, days=int(os.getenv("JME_DAYS", "14"))):
    with open(path, "r", encoding="utf-8") as f:
        sources: List[Dict[str, Any]] = json.load(f)

    async def go():
        for src in sources:
            tag = f"{src['provider']}:{src['slug']}"
            print(f"=== {tag} ===")
            await run_once(tag, days=days)
            time.sleep(REQUEST_DELAY)

    asyncio.run(go())

if __name__ == "__main__":
    main()
