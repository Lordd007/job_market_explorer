from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from sqlalchemy import text as sql
from db.session import SessionLocal
from db.models import User
from api.services.emailer import send_email
from core.security import create_access_token
import datetime as dt, random, html
import os, uuid

router = APIRouter(tags=["auth"])

def db_session():
    db = SessionLocal()
    try: yield db
    finally: db.close()

class RequestCodeIn(BaseModel):
    email: EmailStr

class VerifyCodeIn(BaseModel):
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6)

@router.post("/auth/request_code")
def request_code(payload: RequestCodeIn):
    email = str(payload.email).lower().strip()
    code = f"{random.randint(0, 999999):06d}"
    now = dt.datetime.now(dt.timezone.utc)
    expires = now + dt.timedelta(minutes=10)

    with SessionLocal() as db:
        # rate limit: max 5 active codes/hour for this email
        n = db.execute(sql("""
          SELECT COUNT(*) FROM auth_login_code
          WHERE email=:e AND created_at >= (now() - interval '1 hour')
        """), {"e": email}).scalar()
        if n and int(n) >= 5:
            raise HTTPException(429, "Too many attempts. Try again later.")
        # upsert (keep one row per email)
        db.execute(sql("""
          INSERT INTO auth_login_code(email, code, created_at, expires_at, attempts, used_at)
          VALUES (:e, :c, now(), :x, 0, NULL)
          ON CONFLICT (email) DO UPDATE
          SET code=:c, created_at=now(), expires_at=:x, attempts=0, used_at=NULL
        """), {"e": email, "c": code, "x": expires})
        db.commit()

    subj = "JME login code"
    body = f"Your code is: {code}\nThis code expires in 10 minutes."
    html_body = f"<p>Your code is: <b>{html.escape(code)}</b></p><p>It expires in 10 minutes.</p>"
    # send (reply-to set to the email so you can reply if needed)
    send_email(subject=subj, text=body, html=html_body, to_addrs=email, reply_to=os.getenv("ALERT_TO", email))

    return {"ok": True}


@router.post("/auth/verify_code")
def verify_code(payload: VerifyCodeIn):
    email = str(payload.email).lower().strip()
    code = payload.code.strip()
    now = dt.datetime.now(dt.timezone.utc)

    with SessionLocal() as db:
        row = db.execute(sql("""
          SELECT email, code, expires_at, used_at, attempts
          FROM auth_login_code WHERE email = :e
        """), {"e": email}).mappings().first()
        if not row:
            raise HTTPException(400, "No code requested for this email")

        if row["used_at"] is not None or row["expires_at"] < now:
            raise HTTPException(400, "Code expired. Request a new one.")

        if row["code"] != code:
            db.execute(sql("UPDATE auth_login_code SET attempts = attempts + 1 WHERE email=:e"), {"e": email})
            db.commit()
            raise HTTPException(400, "Invalid code")

        # mark used
        db.execute(sql("UPDATE auth_login_code SET used_at = now() WHERE email = :e"), {"e": email})

        # ensure user exists (race-safe + email unique)
        user = db.query(User).filter(User.email == email).first()
        if not user:
            new_id = uuid.uuid4()
            db.execute(sql("""
              INSERT INTO users (user_id, auth_sub, email, created_at)
              VALUES (:uid, :sub, :email, now())
              ON CONFLICT (email) DO NOTHING
            """), {"uid": str(new_id), "sub": email, "email": email})
            user = db.query(User).filter(User.email == email).first()

        db.commit()

        token = create_access_token(sub=str(user.user_id), extra={"email": email})
        return {"access_token": token, "token_type": "bearer",
                "user": {"user_id": str(user.user_id), "email": email}}

