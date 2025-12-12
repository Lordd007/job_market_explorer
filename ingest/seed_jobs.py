# ingest/seed_jobs.py
from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Iterable, Dict, Any, Optional, List

from ingest.location_utils import normalize_location


SEED_PATH_DEFAULT = Path("data/seed_jobs.json")


def _parse_dt(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    try:
        # ISO 8601 fallback (accepts “...Z”)
        return datetime.fromisoformat(s.replace("Z", "+00:00")).replace(tzinfo=None)
    except Exception:
        return None


def iter_seed_jobs(
    days: int = 90, path: Path | str = SEED_PATH_DEFAULT
) -> List[Dict[str, Any]]:
    """
    Read seed jobs from data/seed_jobs.json and return a list of dicts:
      {title, company, description_text, url, city, region, country, posted_at (datetime|None), source}
    Only include rows within the last `days` if `posted_at` is present.
    """
    p = Path(path)
    if not p.exists():
        # Minimal, already-normalized sample (no mutation needed)
        return [{
            "title": "Sample Data Analyst",
            "company": "Demo Co",
            "description_text": "Analyze data. SQL, Python, dashboards.",
            "url": None,
            "city": "Remote",
            "region": None,
            "country": "US",
            "posted_at": datetime.utcnow(),  # datetime here
            "source": "seed",
        }]

    with p.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    cutoff = datetime.utcnow() - timedelta(days=days)
    out: List[Dict[str, Any]] = []

    for r in raw:
        # Normalize location fields (supports both new and old JSON)
        c_city, c_region, c_country = normalize_location(
            r.get("location"),
            r.get("city"),
            r.get("region"),
            r.get("country"),
        )

        posted_at = _parse_dt(r.get("posted_at"))
        if posted_at and posted_at < cutoff:
            continue  # skip too-old items when date present

        out.append({
            "title": (r.get("title") or "").strip(),
            "company": (r.get("company") or "Seed").strip(),
            "description_text": (r.get("description_text") or r.get("description") or "").strip()[:200000],
            "url": r.get("url"),
            "city": c_city or "N/A",
            "region": c_region,
            "country": c_country,
            "posted_at": posted_at,   # Optional[datetime]
            "source": r.get("source") or "seed",
        })

    return out
