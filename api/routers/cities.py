# api/routers/cities.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text as sql
from db.session import SessionLocal

router = APIRouter(tags=["cities"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/cities")
def cities(
    min_count: int = Query(10, ge=0, le=100000),
    limit: int = Query(200, ge=1, le=10000),
    db: Session = Depends(get_db)
):
    """
    Returns normalized 'city' options with counts from jobs.

    Goals:
    - Keep real cities.
    - When the entry is *remote-only*, emit "Remote, {CC}" (e.g., "Remote, US").
    - For non-US cities, append country code: "London, UK", "Bengaluru, IN", "Munich, DE".
    - For US with a 2-letter region: "San Francisco, CA".
    - Strip mode words (Remote/Hybrid/In-Office/Office/Distributed/Home based).
    """
    q = sql("""
    WITH raw AS (
      SELECT
        TRIM(COALESCE(city, ''))   AS city,
        TRIM(COALESCE(region,''))  AS region,
        TRIM(COALESCE(country,'')) AS country
      FROM jobs
    ),
    base AS (
      SELECT
        LOWER(city) AS city_l,
        UPPER(region) AS region_u,
        /* Map GB->UK (common expectation) */
        CASE WHEN UPPER(country) = 'GB' THEN 'UK' ELSE UPPER(country) END AS country_u
      FROM raw
    ),
    flags AS (
      SELECT
        city_l, region_u, country_u,
        (city_l ~* '\\b(remote|distributed|home\\s*based)\\b') AS has_remote_kw,
        (city_l ~* '\\bhybrid\\b') AS has_hybrid_kw
      FROM base
    ),
    step1 AS (
      SELECT
        /* remove trailing "(Remote|Hybrid|...)" */
        REGEXP_REPLACE(city_l, '\\s*\\((?:remote|hybrid|in-?office|distributed|home\\s*based)\\)\\s*$', '', 'i') AS s1,
        region_u, country_u, has_remote_kw
      FROM flags
    ),
    step2 AS (
      SELECT
        /* remove leading mode tokens + separators ONLY (keep the city after it) */
        REGEXP_REPLACE(
          s1,
          '^\\s*(?:remote|hybrid|in-?office|office|distributed|home\\s*based)\\b\\s*(?:[-—–:,/]|to|and)?\\s*',
          '',
          'i'
        ) AS s2,
        region_u, country_u, has_remote_kw
      FROM step1
    ),
    tokens AS (
      SELECT
        /* first token before comma/semicolon/slash/pipe */
        NULLIF(TRIM(SUBSTRING(s2 FROM '^[^,;/|]+')), '') AS ccity_raw,
        region_u, country_u, has_remote_kw
      FROM step2
    ),
    city_like AS (
      SELECT
        ccity_raw, region_u, country_u, has_remote_kw,
        /* treat country/region words as NOT a city (e.g. "US only", "EMEA") */
        NOT COALESCE(
          ccity_raw ~* '^(us|usa|united\\s*states|uk|gb|de|germany|in|india|ca|canada|au|australia|nz|new\\s*zealand|eu|europe|emea|apac|na|latam|global|worldwide|anywhere|remote)$',
          FALSE
        ) AS is_city
      FROM tokens
    ),
    normalized AS (
      SELECT
        CASE
          /* A: real city extracted */
          WHEN is_city AND country_u = 'US' AND region_u ~ '^[A-Z]{2}$'
            THEN INITCAP(ccity_raw) || ', ' || region_u                             -- San Francisco, CA
          WHEN is_city AND country_u <> ''
            THEN INITCAP(ccity_raw) || ', ' || country_u                             -- London, UK / Bengaluru, IN / Munich, DE
          WHEN is_city
            THEN INITCAP(ccity_raw)                                                  -- City with no country available

          /* B: remote-only (had remote keywords AND no usable city) */
          WHEN NOT is_city AND has_remote_kw AND country_u <> ''
            THEN 'Remote, ' || country_u                                             -- Remote, US / Remote, DE / ...
          WHEN NOT is_city AND has_remote_kw
            THEN 'Remote'                                                            -- Remote (no country captured)

          /* C: fallbacks when nothing else works */
          WHEN region_u <> '' AND country_u <> ''
            THEN INITCAP(region_u) || ', ' || country_u
          WHEN region_u <> ''
            THEN INITCAP(region_u)
          WHEN country_u <> ''
            THEN country_u
          ELSE NULL
        END AS city_norm
      FROM city_like
    ),
    filtered AS (
      SELECT city_norm
      FROM normalized
      WHERE city_norm IS NOT NULL
        AND LENGTH(city_norm) >= 2
        AND LOWER(city_norm) NOT IN ('n/a','na','none','-')
    )
    SELECT city_norm AS city, COUNT(*)::int AS cnt
    FROM filtered
    GROUP BY city_norm
    HAVING COUNT(*) >= :min_count
    ORDER BY cnt DESC, city ASC
    LIMIT :limit;
    """)

    rows = db.execute(q, {"min_count": min_count, "limit": limit}).mappings().all()
    return [{"city": r["city"], "count": r["cnt"]} for r in rows]
