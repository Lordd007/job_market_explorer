from fastapi import FastAPI
from api.routers import jobs, skills

app = FastAPI(title="Job Market Explorer")
@app.get("/health")
def health(): return {"status":"ok"}

app.include_router(jobs.router, prefix="/api")
app.include_router(skills.router, prefix="/api")
