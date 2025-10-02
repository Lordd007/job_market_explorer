from __future__ import annotations
import requests
from typing import Iterable, Dict, Any, Optional
from .base import SourceAdapter, JobDoc

class Lever(SourceAdapter):
    name = "lever"
    API_BASE = "https://api.lever.co/v0/postings"

    def resolve_board(self, company: str, candidates: Iterable[str]) -> Optional[str]:
        # Lever uses a single handle: careers.lever.co/<handle>
        return next(iter(candidates), None)

    def fetch_jobs(self, handle: str):
        r = requests.get(f"{self.API_BASE}/{handle}?mode=json", timeout=30)
        r.raise_for_status()
        return r.json()

    def normalize(self, handle: str, j: Dict[str, Any]) -> JobDoc:
        loc = j.get("categories",{}).get("location","")
        url = j.get("hostedUrl") or j.get("applyUrl") or ""
        return JobDoc(
            board_id=handle,
            job_id=str(j.get("id") or j.get("lever_id") or j.get("internalJobId") or j.get("text","")),
            title=j.get("text",""),
            location=loc,
            absolute_url=url,
            departments=j.get("categories",{}).get("team",""),
            offices=j.get("categories",{}).get("commitment",""),
            updated_at=j.get("createdAt",""),
        )
