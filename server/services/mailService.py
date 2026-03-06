import smtplib
import logging as log
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

_smtp_host = None
_smtp_port = None
_smtp_user = None
_smtp_password = None
_smtp_from = None

def init(secrets):
    global _smtp_host, _smtp_port, _smtp_user, _smtp_password, _smtp_from
    _smtp_host = secrets.get("smtp_host", "")
    _smtp_port = int(secrets.get("smtp_port", 587))
    _smtp_user = secrets.get("smtp_user", "")
    _smtp_password = secrets.get("smtp_password", "")
    _smtp_from = secrets.get("smtp_from", _smtp_user)
    if is_configured():
        log.info(f"Mail service initialized. SMTP: {_smtp_host}:{_smtp_port}")
    else:
        log.info("Mail service not configured. Email verification disabled.")

def is_configured():
    return bool(_smtp_host and _smtp_user and _smtp_password)

def send(to, subject, html_body):
    if not is_configured():
        return False
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = _smtp_from
    msg["To"] = to
    msg.attach(MIMEText(html_body, "html"))
    try:
        with smtplib.SMTP(_smtp_host, _smtp_port) as server:
            server.starttls()
            server.login(_smtp_user, _smtp_password)
            server.sendmail(_smtp_from, to, msg.as_string())
        log.info(f"Email sent to {to}: {subject}")
        return True
    except Exception as e:
        log.error(f"Failed to send email to {to}: {e}")
        return False
