from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, Field
from api.services.emailer import send_email
import html

router = APIRouter(tags=["feedback"])

class FeedbackIn(BaseModel):
    name: str = Field(..., max_length=100)
    email: EmailStr
    subject: str = Field(..., max_length=150)
    message: str = Field(..., max_length=5000)
    category: str | None = Field(None, max_length=50)  # e.g., bug, idea, data-issue

@router.post("/feedback")
def submit_feedback(payload: FeedbackIn):
    try:
        subj = f"[JME Feedback] {payload.subject}"
        text = (
            f"Name: {payload.name}\n"
            f"Email: {payload.email}\n"
            f"Category: {payload.category or '-'}\n\n"
            f"{payload.message}\n"
        )
        html_body = f"""
        <h3>JME Feedback</h3>
        <p><b>Name:</b> {html.escape(payload.name)}</p>
        <p><b>Email:</b> {html.escape(str(payload.email))}</p>
        <p><b>Category:</b> {html.escape(payload.category or '-')}</p>
        <pre style="white-space:pre-wrap">{html.escape(payload.message)}</pre>
        """
        # reply-to set to the user's email so you can reply quickly
        send_email(subject=subj, text=text, html=html_body, reply_to=str(payload.email))
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send feedback: {e}")
