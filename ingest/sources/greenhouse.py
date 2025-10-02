from __future__ import annotations
import time, requests
from typing import Iterable, Dict, Any, Optional
from .base import SourceAdapter, JobDoc

class Greenhouse(SourceAdapter):
    name = "greenhouse"
    API_BASE = "https://boards-api.greenhouse.io/v1/boards"

    def _valid(self, slug: str) -> bool:
        try:
            r = requests.get(f"{self.API_BASE}/{slug}/jobs", timeout=20)
            return r.status_code == 200
        except requests.RequestException:
            return False

    def resolve_board(self, company: str, candidates: Iterable[str]) -> Optional[str]:
        for c in candidates:
            if self._valid(c):
                return c
            time.sleep(self.request_delay)
        return None

    def fetch_jobs(self, board_id: str):
        r = requests.get(f"{self.API_BASE}/{board_id}/jobs", timeout=30)
        r.raise_for_status()
        return r.json().get("jobs", [])

    def normalize(self, board_id: str, j: Dict[str, Any]) -> JobDoc:
        return JobDoc(
            board_id=board_id,
            job_id=str(j["id"]),
            title=j.get("title",""),
            location=(j.get("location") or {}).get("name",""),
            absolute_url=j.get("absolute_url",""),
            departments="; ".join(d["name"] for d in j.get("departments",[])),
            offices="; ".join(o["name"] for o in j.get("offices",[])),
            updated_at=j.get("updated_at",""),
        )
