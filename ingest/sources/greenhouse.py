import time, json, datetime as dt
from typing import Iterable
import requests
from .base import SourceAdapter, JobDoc

class Greenhouse(SourceAdapter):
    def __init__(self, company_slug: str):
        self.name = f"greenhouse:{company_slug}"
        self.company_slug = company_slug
        self.base = f"https://boards-api.greenhouse.io/v1/boards/{company_slug}/jobs"

    def fetch(self, days: int = 7) -> Iterable[JobDoc]:
        cutoff = dt.datetime.utcnow() - dt.timedelta(days=days)
        params = {"content": "true"}  # include full descriptions when available
        headers = {"User-Agent": "JobMarketExplorer/0.1"}
        r = requests.get(self.base, params=params, headers=headers, timeout=20)
        r.raise_for_status()
        data = r.json()
        for j in data.get("jobs", []):
            posted = j.get("updated_at") or j.get("created_at")
            if posted:
                try:
                    posted_dt = dt.datetime.fromisoformat(posted.replace("Z","+00:00")).replace(tzinfo=None)
                except Exception:
                    posted_dt = None
            else:
                posted_dt = None
            if posted_dt and posted_dt < cutoff:
                continue
            # normalize locations
            loc = (j.get("location") or {}).get("name") or ""
            city, region, country = None, None, None
            parts = [p.strip() for p in loc.split(",") if p.strip()]
            if parts:
                city = parts[0] if parts else None
                if len(parts) >= 2: region = parts[1]
                if len(parts) >= 3: country = parts[-1]

            yield JobDoc(
                title=j.get("title","").strip(),
                company=(j.get("offices") or [{}])[0].get("name") or j.get("departments",[{}])[0].get("name") or "",
                description_text=(j.get("content") or ""),
                url=j.get("absolute_url"),
                city=city, region=region, country=country,
                posted_at_iso=posted,
                source=self.name
            )
            time.sleep(1.0)  # gentle rate limit
