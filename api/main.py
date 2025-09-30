from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import jobs, skills

app = FastAPI(title="Job Market Explorer")

# CORS middleware (dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

app.include_router(jobs.router, prefix="/api")
app.include_router(skills.router, prefix="/api")
