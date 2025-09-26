## 📜 Project Blueprint (Full Details)

<details>
<summary><strong>1) Problem, Audience, Uniqueness</strong></summary>

**Problem:** It’s hard for job seekers and training programs to see which skills are actually in demand, how they change by city/industry, and what salaries align with those skills.

**Audience:**
- Job seekers & career switchers
- University career centers & bootcamps
- Workforce boards and local governments

**What’s unique:**
- Skill extraction with **NLP + embeddings**, not just keyword counts
- **Normalized salary & seniority** across vendors/titles (clean cross-site comparisons)
- **Cohort tracking:** e.g., “How did *GenAI tool* mentions trend after Jan 2025?”
- **Actionable insights:** “If you learn X + Y, you unlock Z% more postings in your area.”
</details>

<details>
<summary><strong>2) Core Features (MVP → V2)</strong></summary>

### MVP
1. **Ingestion & Deduplication**
   - Scrapers for company career systems (e.g., **Greenhouse**, **Lever**), plus selected public boards that permit crawling per robots.txt/TOS.
   - Title, company, location, salary (if present), posting date, description, URL.
   - Robust **duplicate detection** (URL hash + shingled text hash).

2. **Skill Extraction & Standardization**
   - NER + phrase mining to extract skills (e.g., “Kubernetes”, “PyTorch”, “Looker”).
   - Canonicalize via a **skills ontology** (your curated dictionary + alias map).
   - Confidence score per extracted skill.

3. **Trend Dashboards**
   - Interactive charts: top skills, growth/decline over time, by city/industry.
   - Salary distribution by role & skill (where available).
   - “Rising skills” ranker (week-over-week or month-over-month delta).

4. **Search & Filters**
   - Full-text search across postings.
   - Filters: location, remote vs onsite, posted date, skills, industry.

### V2 / Stretch
- **Embedding-based similarity** (“find me roles similar to this one”).
- **Seniority classifier** (entry/mid/senior) from title + description.
- **Skill gap analysis** given a user profile/CSV of skills.
- **Alerting:** weekly email: “Top 10 skill movers in Data/AI in San Diego.”
</details>

<details>
<summary><strong>3) System Architecture</strong></summary>

**Frontend:** Next.js (React) + Tailwind + server-side rendering (SEO-friendly); Charting with Recharts or ECharts.  
**Backend API:** FastAPI (Python) for REST + batch inference endpoints.  
**Ingestion:** Python workers (Celery + Redis) scheduled via Celery Beat or cloud cron.  
**Storage:**
- **PostgreSQL** for normalized job + skills tables
- **Elasticsearch/OpenSearch** (or Postgres + pg_trgm) for search
- **Object store** (S3 compatible) for raw HTML snapshots (optional)

**ML/NLP:** spaCy + HuggingFace Transformers; sentence-transformers for embeddings; scikit-learn/XGBoost for classifiers.  
**Vector Store (optional):** FAISS or pgvector for similar job/skill search.  
**Orchestration:** Docker Compose locally; deploy via Docker to Render/Fly.io/AWS.  
**Observability:** Prometheus + Grafana (or OpenTelemetry + vendor) for pipelines; Sentry for errors.
</details>

<details>
<summary><strong>4) Data Model (relational core)</strong></summary>

**jobs**  
- `job_id` (PK), `title`, `company`, `location_raw`, `city`, `region`, `country`, `remote_flag`, `employment_type`, `salary_min`, `salary_max`, `salary_currency`, `salary_period`, `posted_at`, `source`, `url`, `description_text`, `desc_hash`, `created_at`, `updated_at`

**skills**  
- `skill_id` (PK), `name_canonical`, `aliases` (JSONB), `category` (e.g., “ML”, “DevOps”, “BI”)

**job_skills** (many-to-many)  
- `job_id`, `skill_id`, `confidence`

**vendors** (optional for source analytics)  
- `vendor_id`, `name`, `base_url`, `ats_type` (greenhouse/lever/workday/etc.)

**indexes:**  
- `jobs(desc_hash)` for dedupe; `jobs(posted_at)` for time series; trigram index on `title`/`company` for fuzzy search.
</details>

<details>
<summary><strong>5) Ingestion & Compliance</strong></summary>

- Respect **robots.txt / rate limits / TOS**. Keep per-domain rate controls (e.g., 1 req/sec).  
- Prefer **public ATS endpoints** (many Greenhouse/Lever boards expose JSON or well-structured HTML).  
- Store **raw HTML** (optional) for reproducibility and better label audits.  
- **Dedup** with: (a) URL hash; (b) MinHash/SimHash over normalized text to catch clones.
</details>

<details>
<summary><strong>6) NLP / ML Components</strong></summary>

1. **Skill Extraction Pipeline**
   - Preprocess: lowercase, strip boilerplate, sentence split.
   - **Seed dictionary** (hand-curated list of 500–1,500 skills) + alias map.
   - **Matcher**: spaCy PhraseMatcher for high-precision hits.
   - **ML augmenter**: NER or sequence tagger (fine-tuned transformer).
   - Merge hits; assign **confidence** (dictionary = high, NER-only = medium).
   - Optional: few-shot prompt to an LLM for tricky phrases → post-filter with rules.

2. **Seniority Classifier (V2)**
   - Label ~1–2k titles/descriptions (entry/mid/senior).
   - Features: TF-IDF + n-grams + keywords, or transformer fine-tune.
   - Target F1 ≥ 0.80.

3. **Salary Normalization**
   - Parse ranges & periodicity; normalize to **annual USD**.
   - Handle outliers (winsorize p1–p99).

4. **Trend Analysis**
   - Weekly rollups: `skill x city x week` counts + median salary.
   - “Rising skills” = compute %Δ over last N weeks with minimum base support.
</details>

<details>
<summary><strong>7) Key User Stories & Acceptance Criteria</strong></summary>

- **Search & filter**  
  *As a user, I can search jobs and filter by city, remote, and skills.*  
  **AC:** Query returns in <700ms p95; correct facet counts.

- **Skill trends**  
  *As a user, I can view top skills and their 12-week trend in my metro.*  
  **AC:** Line charts update within 24h; tooltips show counts + Δ%.

- **Rising skills**  
  *As a user, I can see “rising skills” this month vs last.*  
  **AC:** Exclude skills with <50 postings; show Δ% and absolute change.

- **Salary by skill**  
  *As a user, I can compare salary distributions for roles requiring “Kubernetes”.*  
  **AC:** Box/violin chart with min/median/p75; sample size shown.
</details>

<details>
<summary><strong>8) API Design (selected endpoints)</strong></summary>

- `GET /api/jobs` — query params: `q, city, remote, skills[], posted_after, page, per_page`  
- `GET /api/skills/top` — params: `city, weeks=12, category`  
- `GET /api/skills/rising` — params: `city, baseline_weeks=4`  
- `GET /api/metrics/skill_salary` — params: `skill, role, city`  
- `POST /api/ingest/run` — protected; triggers a refresh job  
- `GET /api/jobs/{job_id}` — detailed view
</details>

<details>
<summary><strong>9) Data Pipeline (daily)</strong></summary>

1. **Fetch:** Celery task per source with rate limits  
2. **Normalize:** clean fields, map locations with geocoder  
3. **Dedup:** URL + near-duplicate text  
4. **NLP:** skill extraction → canonicalization → confidence  
5. **Store:** upsert jobs, link skills  
6. **Aggregate:** weekly skill counts & salaries  
7. **Index:** refresh search/embedding indexes  
8. **QC:** anomaly checks (e.g., sudden spikes)
</details>

<details>
<summary><strong>10) Evaluation & QA</strong></summary>

- **Extraction precision/recall:** Manually label 300–500 postings; target P ≥ 0.9, R ≥ 0.8.  
- **Trend stability:** Backtest 8–12 weeks; flag noisy sources.  
- **Latency SLOs:** API p95 <800ms; 24h data freshness.
</details>

<details>
<summary><strong>11) UI/UX Sketch</strong></summary>

- **Hero search** (role, city, remote toggle) + quick filters  
- **Insights tiles:** top skills, median salary, hiring companies  
- **Trend view:** line charts, compare up to 3 skills  
- **Skill profile:** description, aliases, related skills, top cities, salaries  
- **Job detail:** scraped posting, extracted skills, similar jobs
</details>

<details>
<summary><strong>12) Ethics, Legal, and Reliability</strong></summary>

- Respect **robots.txt and TOS**.  
- **Attribution:** keep source links visible.  
- **PII:** avoid scraping names/emails.  
- **Bias warnings:** note data coverage and sampling bias.
</details>

<details>
<summary><strong>13) Roadmap (8–10 weeks)</strong></summary>

- **Week 1–2:** Ingestion MVP, schema, dedup  
- **Week 3:** Skill dictionary v1, spaCy matcher, evals  
- **Week 4:** Trend rollups + dashboards  
- **Week 5:** Search, filters, salary normalization  
- **Week 6:** Deployment + monitoring + QC  
- **Week 7–8:** Polish, tests, demo seed, writeup  
- **Stretch:** Seniority classifier, embeddings, alerts
</details>

<details>
<summary><strong>14) Portfolio Deliverables</strong></summary>

- **Live demo URL** with demo data  
- **Repo** with `infra/`, `ingest/`, `api/`, `web/`, `models/`, `Makefile`  
- **Architecture diagram** (1 page)  
- **Model cards** for extraction & classifier  
- **Short blog post**: “What’s really rising in AI hiring in 2025?”
</details>
