from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from api.deps.auth import get_current_user, get_db
from db.models import User

router = APIRouter(tags=["account"])

@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {"user_id": str(user.user_id), "email": user.email}
