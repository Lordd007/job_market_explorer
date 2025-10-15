import os, smtplib
from email.message import EmailMessage

def send_email(subject: str, text: str, html: str | None = None,
               to_addrs: str | list[str] | None = None,
               reply_to: str | None = None):
    user = os.environ["GMAIL_USER"]
    pwd  = os.environ["GMAIL_PASS"]

    if to_addrs is None:
        to_addrs = os.environ.get("ALERT_TO", user)
    if isinstance(to_addrs, str):
        to_addrs = [x.strip() for x in to_addrs.split(",") if x.strip()]

    msg = EmailMessage()
    msg["From"] = user
    msg["To"]   = ", ".join(to_addrs)
    msg["Subject"] = subject
    if reply_to:
        msg["Reply-To"] = reply_to
    msg.set_content(text or "")
    if html:
        msg.add_alternative(html, subtype="html")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(user, pwd)
        s.send_message(msg)
