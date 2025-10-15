#GMAIL has a limit of 500 emails per day for personal accounts.
import os, datetime as dt
from sqlalchemy import text as sql
from db.session import SessionLocal
from scripts.notify_email import send_email

DEMO_USER = "00000000-0000-0000-0000-000000000001"

HTML_TMPL = """\
<h3>New jobs for you this week</h3>
<p>Here are {n} new postings that match your preferences.</p>
<table border="1" cellspacing="0" cellpadding="6">
  <tr><th>Title</th><th>Company</th><th>City</th><th>Salary (USD)</th><th>Posted</th><th>Link</th></tr>
  {rows}
</table>
"""

def main(user_id: str = DEMO_USER, days: int = 7, limit: int = 20):
    db = SessionLocal()
    try:
        prefs = db.execute(sql("""
            SELECT cities, remote_mode, target_skills FROM user_preferences WHERE user_id = :uid
        """), {"uid": user_id}).mappings().first()
        if not prefs:
            print("no prefs set; aborting"); return

        cities = prefs["cities"] or []
        targets = [t.lower() for t in (prefs["target_skills"] or [])]

        query = sql("""
        WITH recent AS (
            SELECT j.job_id, j.title, j.company, j.city, j.salary_usd_annual, j.url, j.posted_at
            FROM jobs j
            WHERE j.posted_at >= (CURRENT_DATE - INTERVAL :days || ' day')
              AND (COALESCE(:use_cities,false) = false OR j.city = ANY(:cities))
        ),
        overlaps AS (
            SELECT r.*, COUNT(*) AS hits
            FROM recent r
            JOIN job_skills js ON js.job_id = r.job_id
            JOIN skills s ON s.skill_id = js.skill_id
            WHERE s.name_canonical = ANY(:targets)
            GROUP BY r.job_id, r.title, r.company, r.city, r.salary_usd_annual, r.url, r.posted_at
        )
        SELECT * FROM overlaps
        ORDER BY hits DESC, salary_usd_annual DESC NULLS LAST
        LIMIT :lim
        """)

        rows = db.execute(query, {
            "days": days,
            "cities": cities,
            "use_cities": bool(cities),
            "targets": targets,
            "lim": limit
        }).mappings().all()

        if not rows:
            send_email("Weekly jobs: none found", "No matches this week.")
            return

        html_rows = []
        for r in rows:
            posted = (r["posted_at"].date().isoformat() if r["posted_at"] else "")
            url = r["url"] or "#"
            html_rows.append(f"<tr><td>{r['title']}</td><td>{r['company']}</td>"
                             f"<td>{r['city'] or ''}</td><td>{r['salary_usd_annual'] or ''}</td>"
                             f"<td>{posted}</td><td><a href='{url}'>Apply</a></td></tr>")

        html = HTML_TMPL.format(n=len(rows), rows="\n".join(html_rows))
        text = f"{len(rows)} new jobs for you this week."
        send_email("Weekly matches from JME", text, html)

    finally:
        db.close()

if __name__ == "__main__":
    main()
