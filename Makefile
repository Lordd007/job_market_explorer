# -------- Makefile: "Startup" workflow for Job Market Explorer --------
# Usage:
#   make startup        # migrate + start API and Web (each in its own terminal where supported)
#   make migrate        # alembic upgrade head
#   make api            # run uvicorn in the foreground
#   make api-bg         # run uvicorn in a new terminal (Windows) / background (Unix)
#   make web            # run Next.js dev in the foreground
#   make web-bg         # run Next.js dev in a new terminal (Windows) / background (Unix)
#   make seed           # ingest seed jobs
#   make psql           # open psql to app DB
#   make psql-test      # open psql to test DB
#   make counts         # quick row counts
# ---------------------------------------------------------------------

# -------------------- Common config --------------------
API_BASE ?= http://127.0.0.1:8000
APP_DB   ?= postgresql+psycopg://jme:jme@localhost:5432/jme
TEST_DB  ?= postgresql+psycopg://jme:jme@localhost:5432/jme_test

# -------------------- OS-specific shell ----------------
ifeq ($(OS),Windows_NT)
SHELL := powershell.exe
.SHELLFLAGS := -NoLogo -Command
PY_ACT := .\venv\Scripts\Activate.ps1
# # Full path to psql; change if you installed a different version
# PSQL_EXE := "C:\Program Files\PostgreSQL\17\bin\psql.exe"

# run uvicorn (foreground)
RUN_API := uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# open a new PowerShell window for long-running processes
define RUN_IN_NEW_PS
Start-Process powershell -ArgumentList '-NoLogo','-NoExit','-Command', "cd '$(CURDIR)'; $$env:DATABASE_URL='$(APP_DB)'; . $(PY_ACT); $(1)"
endef

define RUN_WEB_PS
cd web; $$env:NEXT_PUBLIC_API_BASE='$(API_BASE)'; npm install; npm run dev -- -p 3001
endef

else
SHELL := bash
PY_ACT := source venv/bin/activate
PSQL_EXE := psql
RUN_API := uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

define RUN_IN_NEW_PS
# On Unix we just background with nohup; logs go to ./logs
mkdir -p logs; ( $(PY_ACT); $(1) ) > logs/bg.log 2>&1 &
endef

define RUN_WEB_PS
cd web && NEXT_PUBLIC_API_BASE="$(API_BASE)" npm install && npm run dev -- -p 3001
endef
endif

# -------------------- Targets --------------------------
.PHONY: startup migrate api api-bg web web-bg seed psql psql-test counts env

startup: migrate api-bg web-bg ## Migrate DB, start API & Web (background/new terminals)
	@echo "✅ Startup complete: API on :8000, Web on :3001"

migrate: ## Alembic upgrade head against APP_DB
	@echo "🔧 Migrating database to head..."
	$${env:DATABASE_URL}='$(APP_DB)'; . $(PY_ACT); alembic -c alembic.ini upgrade head

api: ## Run FastAPI (foreground)
	@echo "🚀 Starting API on :8000 ..."
	$${env:DATABASE_URL}='$(APP_DB)'; . $(PY_ACT); $(RUN_API)

api-bg: ## Run FastAPI in a new terminal / background
	@echo "🚀 Starting API (background/new terminal)..."
	$(call RUN_IN_NEW_PS,$(RUN_API))

web: ## Run Next.js dev (foreground)
	@echo "🌐 Starting Web on :3001 ..."
	$(RUN_WEB_PS)

web-bg: ## Run Next.js in a new terminal / background
	@echo "🌐 Starting Web (background/new terminal)..."
	$(call RUN_IN_NEW_PS,$(RUN_WEB_PS))

seed: ## Ingest seed jobs
	@echo "🌱 Seeding jobs ..."
	$${env:DATABASE_URL}='$(APP_DB)'; . $(PY_ACT); python -m ingest.pipeline --source=seed --days=90 --verbose

psql: ## Open psql to APP_DB
	$(PSQL_EXE) "postgresql://jme:jme@localhost:5432/jme"

psql-test: ## Open psql to TEST_DB
	$(PSQL_EXE) "postgresql://jme:jme@localhost:5432/jme_test"

counts: ## Quick row counts
	@echo "📊 Counting rows (jobs, job_skills, skills)..."
	$$env:DATABASE_URL="$(APP_DB)"; . $(PY_ACT); python scripts/dev_sql.py "SELECT COUNT(*) AS jobs FROM jobs; SELECT COUNT(*) AS links FROM job_skills; SELECT COUNT(*) AS skills FROM skills;"

env: ## Print key env
	@echo "API_BASE=$(API_BASE)"
	@echo "APP_DB=$(APP_DB)"
	@echo "TEST_DB=$(TEST_DB)"
