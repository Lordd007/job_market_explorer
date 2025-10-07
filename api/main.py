from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import jobs, skills
from api import errors
import os, json

app = FastAPI(title="Job Market Explorer")

# Read CORS origins from env (Heroku Config Var), else defaults
_default_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    "https://jme-web-staging.herokuapp.com",
    "https://jme-web-staging-7cea87c089d0.herokuapp.com"  # add your web app host here
]
try:
    _env_origins = json.loads(os.getenv("CORS_ORIGINS", "[]") or "[]")
    if isinstance(_env_origins, list):
        origins = _env_origins or _default_origins
    else:
        origins = _default_origins
except Exception:
    origins = _default_origins

HEROKU_STAGING_REGEX = r"^https://jme-web-staging(?:-[a-z0-9]+)?\.herokuapp\.com$"

# (optional) read a regex from env to make this configurable later
CORS_ORIGIN_REGEX = os.getenv("CORS_ORIGIN_REGEX", HEROKU_STAGING_REGEX)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,               # your exact origins from env/defaults
    allow_origin_regex=CORS_ORIGIN_REGEX,  # <-- add this line
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/")
def root():
    return {"ok": True, "service": "jme-api", "docs": "/docs"}

app.include_router(jobs.router, prefix="/api")
app.include_router(skills.router, prefix="/api")
errors.install(app)
