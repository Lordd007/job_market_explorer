# api/errors.py
from fastapi import Request
from fastapi.responses import JSONResponse
import traceback, uuid

def install(app):
  @app.exception_handler(Exception)
  async def all_exceptions(_: Request, exc: Exception):
    rid = str(uuid.uuid4())[:8]
    # log traceback here if you want
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error", "request_id": rid})
