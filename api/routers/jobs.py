# api/routers/jobs.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text as sql, bindparam, Text, Integer
from db.session import SessionLocal


router = APIRouter(tags=["jobs"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/jobs")
def list_jobs(
    q: str = Query("", description="Free-text search over title/company/desc/url"),
    city: str | None = Query(None, description="Normalized city (e.g., 'Remote, US', 'London, UK')"),
    mode: str | None = Query(None, description="'Remote' | 'Hybrid' | 'On-site' | 'In-Office'"),
    skill: str = Query("", description="Simple contains match on description or job_skills.skill"),
    days: int = Query(90, ge=1, le=3650),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Jobs with normalized city + mode; respects Mode and City filters
    and returns newest first.
    """

    # Canonicalize Mode from UI strings
    mode_canon = None
    if mode:
        m = mode.strip().lower()
        if m in ("on-site", "onsite", "in-office", "in office"):
            mode_canon = "On-site"
        elif m == "remote":
            mode_canon = "Remote"
        elif m == "hybrid":
            mode_canon = "Hybrid"

    q_like = f"%{q.strip()}%" if q else "%"
    skill_like = f"%{skill.strip()}%" if skill else "%"
    offset = (page - 1) * page_size

    stmt = sql("""
    WITH base AS (
      SELECT
        j.job_id,
        j.title,
        j.company,
        j.city,
        j.region,
        j.country,
        j.posted_at,
        j.created_at,
        j.url,
        COALESCE(j.remote_flag, false)         AS remote_flag_src,
        COALESCE(j.description_text, '')       AS description,
        /* single “newest” sort key (uses posted_at first, then created_at) */
        COALESCE(j.posted_at, j.created_at)    AS ts
      FROM jobs j
      WHERE COALESCE(j.posted_at, j.created_at) >= (NOW() - (:days || ' days')::interval)
    ),
    loc_base AS (
      SELECT
        job_id, title, company, city, region, country, posted_at, created_at, url, remote_flag_src, description, ts,
        LOWER(COALESCE(city,''))   AS city_l,
        UPPER(COALESCE(region,'')) AS region_u,
        CASE WHEN UPPER(COALESCE(country,''))='GB' THEN 'UK' ELSE UPPER(COALESCE(country,'')) END AS country_u
      FROM base
    ),
    flags AS (
      SELECT
        *,
        (city_l ~* '\\y(remote|distributed|home\\s*based)\\y') AS has_remote_kw,
        (city_l ~* '\\yhybrid\\y')                            AS has_hybrid_kw
      FROM loc_base
    ),
    step1 AS (
      SELECT
        job_id, title, company, region_u, country_u, posted_at, created_at, url, remote_flag_src, description, ts,
        has_remote_kw, has_hybrid_kw,
        REGEXP_REPLACE(city_l, '\s*\((remote|hybrid|in-?office|distributed|home\s*based)\)\s*$', '', 'i') AS s1
      FROM flags
    ),
    step2 AS (
      SELECT
        job_id, title, company, region_u, country_u, posted_at, created_at, url, remote_flag_src, description, ts,
        has_remote_kw, has_hybrid_kw,
        REGEXP_REPLACE(s1,'^\\s*(remote|hybrid|in-?office|office|distributed|home\\s*based)\\y\\s*([-—–:,/]|to|and)?\\s*', '','i') AS s2      
      FROM step1
    ),
    tokens AS (
      SELECT
        job_id, title, company, region_u, country_u, posted_at, created_at, url, remote_flag_src, description, ts,
        has_remote_kw, has_hybrid_kw,
        NULLIF(TRIM(SUBSTRING(s2 FROM '^[^,;/|]+')), '') AS ccity_raw
      FROM step2
    ),
    city_like AS (
      SELECT
        *,
        NOT COALESCE(
          ccity_raw ~* '^(us|usa|united\\s*states|uk|gb|de|germany|in|india|ca|canada|au|australia|nz|new\\s*zealand|eu|europe|emea|apac|na|latam|global|worldwide|anywhere|remote)$',
          FALSE
        ) AS is_city
      FROM tokens
    ),
    norm AS (
      SELECT
        job_id, title, company, posted_at, created_at, url, region_u, country_u, description, ts,
        CASE
          WHEN is_city AND country_u='US' AND region_u ~ '^[A-Z]{2}$' THEN INITCAP(ccity_raw) || ', ' || region_u
          WHEN is_city AND country_u<>''                             THEN INITCAP(ccity_raw) || ', ' || country_u
          WHEN is_city                                              THEN INITCAP(ccity_raw)
          WHEN NOT is_city AND has_remote_kw AND country_u<>''      THEN 'Remote, ' || country_u
          WHEN NOT is_city AND has_remote_kw                        THEN 'Remote'
          WHEN region_u<>'' AND country_u<>''                       THEN INITCAP(region_u) || ', ' || country_u
          WHEN region_u<>''                                         THEN INITCAP(region_u)
          WHEN country_u<>''                                        THEN country_u
          ELSE NULL
        END::text AS city_norm,
        CASE
          WHEN remote_flag_src OR has_remote_kw THEN 'Remote'
          WHEN has_hybrid_kw                    THEN 'Hybrid'
          ELSE 'On-site'
        END::text AS mode_norm,
        (remote_flag_src OR has_remote_kw) AS remote_flag
      FROM city_like
    ),
    filtered AS (
      SELECT *
      FROM norm
      WHERE
        (:q = '' OR title ILIKE :q_like OR company ILIKE :q_like OR description ILIKE :q_like OR url ILIKE :q_like)
        AND (
          :skill = ''
          OR EXISTS (
          SELECT 1 FROM job_skills js 
          JOIN skills s ON s.skill_id = js.skill_id
          WHERE js.job_id = norm.job_id 
            AND (
            s.name_canonical ILIKE :skill_like
            OR s.category ILIKE :skill_like
            OR s.aliases_json::text ILIKE :skill_like
            )
          )
          OR description ILIKE :skill_like
        )
        AND (NULLIF(:mode_canon, '') IS NULL OR mode_norm = :mode_canon)
        AND (NULLIF(:city, '')       IS NULL OR city_norm  = :city)
    )
    SELECT
      filtered.job_id::text           AS job_id,
      filtered.title,
      filtered.company,
      /* return original vendor strings for display */
      (SELECT city    FROM jobs j2 WHERE j2.job_id = filtered.job_id) AS city,
      (SELECT region  FROM jobs j2 WHERE j2.job_id = filtered.job_id) AS region,
      (SELECT country FROM jobs j2 WHERE j2.job_id = filtered.job_id) AS country,
      filtered.posted_at,
      filtered.created_at,
      (SELECT url FROM jobs j2 WHERE j2.job_id = filtered.job_id)     AS url,
      filtered.remote_flag,
      COUNT(*) OVER()::int AS total,
      filtered.ts            -- DEBUG: keep to prove sorting key exists
    FROM filtered
    ORDER BY filtered.ts DESC NULLS LAST
    LIMIT :limit OFFSET :offset;
    """).bindparams(
    bindparam("mode_canon", type_=Text()),
    bindparam("city",       type_=Text()),
    bindparam("q",          type_=Text()),
    bindparam("skill",      type_=Text()),
    bindparam("limit",      type_=Integer()),
    bindparam("offset",     type_=Integer()),
    bindparam("days",       type_=Integer()),
)

    rows = db.execute(
        stmt,
        {
            "days": days,
            "q": q.strip(),
            "q_like": q_like,
            "skill": skill.strip(),
            "skill_like": skill_like,
            "mode_canon": mode_canon,
            "city": city,
            "limit": page_size,
            "offset": offset,
        },
    ).mappings().all()

    total = rows[0]["total"] if rows else 0
    items = [
        {
            "job_id": r["job_id"],
            "title": r["title"],
            "company": r["company"],
            "city": r["city"],
            "region": r["region"],
            "country": r["country"],
            "posted_at": r["posted_at"].isoformat() if r["posted_at"] else None,
            "created_at": r["created_at"].isoformat() if r["created_at"] else None,
            "url": r["url"],
            "remote_flag": bool(r["remote_flag"]),
        }
        for r in rows
    ]
    return {"total": total, "page": page, "page_size": page_size, "items": items}
