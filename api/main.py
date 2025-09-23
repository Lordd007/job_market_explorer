from fastapi import FastAPI
from api.routers import jobs

app = FastAPI(title="Job Market Explorer")
@app.get("/health")
def health(): return {"status":"ok"}

app.include_router(jobs.router, prefix="/api")
