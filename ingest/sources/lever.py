import time, datetime as dt, requests
from typing import Iterable
from .base import SourceAdapter, JobDoc

class Lever(SourceAdapter):
    def __init__(self, company_slug: str):
        self.name = f"lever:{company_slug}"
        self.base = f"https://api.lever.co/v0/postings/{company_slug}"

    def fetch(self, days: int = 7) -> Iterable[JobDoc]:
        cutoff = dt.datetime.utcnow() - dt.timedelta(days=days)
        headers = {"User-Agent": "JobMarketExplorer/0.1"}
        r = requests.get(self.base, params={"mode":"json"}, headers=headers, timeout=20)
        r.raise_for_status()
        for j in r.json():
            posted_ms = j.get("createdAt")
            posted_dt = dt.datetime.utcfromtimestamp(posted_ms/1000) if posted_ms else None
            if posted_dt and posted_dt < cutoff:
                continue
            loc = (j.get("categories") or {}).get("location") or ""
            city, region, country = None, None, None
            parts = [p.strip() for p in loc.split(",") if p.strip()]
            if parts:
                city = parts[0]
                if len(parts) >= 2: region = parts[1]
                if len(parts) >= 3: country = parts[-1]
            yield JobDoc(
                title=j.get("text","").strip(),
                company=(j.get("categories") or {}).get("team") or "",
                description_text=j.get("descriptionPlain","") or j.get("description",""),
                url=j.get("hostedUrl"),
                city=city, region=region, country=country,
                posted_at_iso=posted_dt.isoformat() if posted_dt else None,
                source=self.name
            )
            time.sleep(1.0)
