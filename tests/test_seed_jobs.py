# tests/test_seed_jobs.py
from __future__ import annotations
from datetime import datetime, timedelta
import json

from ingest.seed_jobs import iter_seed_jobs


def test_iter_seed_jobs_reads_new_shape(tmp_path):
    seed = [
        {
            "title": "Data Scientist",
            "company": "Acme",
            "description_text": "Build models",
            "url": "https://ex/1",
            "city": "Seattle",
            "region": "WA",
            "country": "US",
            "posted_at": datetime.utcnow().strftime("%Y-%m-%d"),
            "source": "seed"
        }
    ]
    p = tmp_path / "seed_jobs.json"
    p.write_text(json.dumps(seed), encoding="utf-8")

    rows = iter_seed_jobs(days=90, path=p)
    assert isinstance(rows, list) and len(rows) == 1

    r = rows[0]
    assert r["title"] == "Data Scientist"
    assert r["company"] == "Acme"
    assert r["city"] == "Seattle"
    assert r["region"] == "WA"
    assert r["country"] == "US"
    assert isinstance(r["posted_at"], (datetime, type(None)))  # should be datetime here
    assert r["source"] == "seed"


def test_iter_seed_jobs_supports_old_location_field(tmp_path):
    seed = [
        {
            "title": "ML Engineer",
            "company": "Beta",
            "description_text": "NLP, CV",
            "url": "https://ex/2",
            "location": "Austin, TX",
            "posted_at": datetime.utcnow().strftime("%Y-%m-%d"),
        },
        {
            "title": "Remote SRE",
            "company": "Gamma",
            "description_text": "SRE",
            "url": "https://ex/3",
            "location": "Remote",
            "posted_at": datetime.utcnow().strftime("%Y-%m-%d"),
        }
    ]
    p = tmp_path / "seed_jobs.json"
    p.write_text(json.dumps(seed), encoding="utf-8")

    rows = iter_seed_jobs(days=90, path=p)
    assert len(rows) == 2

    austin = next(r for r in rows if r["title"] == "ML Engineer")
    assert austin["city"] == "Austin"
    assert austin["region"] == "TX"
    assert austin["country"] is None  # not provided in "City, ST"

    remote = next(r for r in rows if r["title"] == "Remote SRE")
    assert remote["city"] == "Remote"
    assert remote["region"] is None


def test_iter_seed_jobs_filters_by_days(tmp_path):
    old_date = (datetime.utcnow() - timedelta(days=365)).strftime("%Y-%m-%d")
    new_date = datetime.utcnow().strftime("%Y-%m-%d")

    seed = [
        {"title": "Old", "company": "X", "description_text": "", "url": None, "city": "NYC", "region": "NY", "country": "US", "posted_at": old_date},
        {"title": "New", "company": "Y", "description_text": "", "url": None, "city": "NYC", "region": "NY", "country": "US", "posted_at": new_date},
    ]
    p = tmp_path / "seed_jobs.json"
    p.write_text(json.dumps(seed), encoding="utf-8")

    rows = iter_seed_jobs(days=90, path=p)
    titles = [r["title"] for r in rows]
    assert "New" in titles
    assert "Old" not in titles  # filtered out


def test_iter_seed_jobs_missing_file_returns_sample(tmp_path):
    # Path that doesn't exist
    p = tmp_path / "nope.json"
    rows = iter_seed_jobs(days=90, path=p)
    assert len(rows) >= 1
    r = rows[0]
    # minimal invariants of the built-in sample
    assert "title" in r and "company" in r and "description_text" in r
    assert isinstance(r["posted_at"], (datetime, type(None)))
