# scripts/nightly_ingest.py
from __future__ import annotations
import json, os, asyncio, time
from typing import Dict, Any, List
from ingest.pipeline import run_once

REQUEST_DELAY = float(os.getenv("REQUEST_DELAY", "0.25"))
SOURCES_JSON  = os.getenv("SOURCES_JSON", "data/sources.json")
DEFAULT_DAYS  = int(os.getenv("JME_DAYS", "14"))

def main(path=SOURCES_JSON, days=DEFAULT_DAYS):
    with open(path, "r", encoding="utf-8") as f:
        sources: List[Dict[str, Any]] = json.load(f)

    async def go():
        for src in sources:
            tag = f"{src['provider']}:{src['slug']}"
            print(f"=== {tag} ===")
            await run_once(source=tag, days=days)  # fetch → normalize → save_to_db()
            time.sleep(REQUEST_DELAY)

    asyncio.run(go())

if __name__ == "__main__":
    main()
