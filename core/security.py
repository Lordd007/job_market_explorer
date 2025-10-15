import os, datetime as dt, jwt
from typing import Dict, Any

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me")
JWT_ALG = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))

def create_access_token(sub: str, extra: Dict[str, Any] | None = None) -> str:
    now = dt.datetime.utcnow()
    exp = now + dt.timedelta(minutes=JWT_EXPIRE_MINUTES)
    payload = {"sub": sub, "iat": int(now.timestamp()), "exp": int(exp.timestamp())}
    if extra:
        payload.update(extra)
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)

def decode_token(token: str) -> Dict[str, Any]:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
