import json
import os
import secrets
import logging as log
from datetime import datetime, timedelta, timezone
import bcrypt
from jose import jwt, JWTError
from services import mailService

_users_file = None
_jwt_secret = None
_google_client_id = None
_frontend_url = None
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 48
RESET_TOKEN_HOURS = 1

def init(config, secrets_cfg):
    global _users_file, _jwt_secret, _google_client_id, _frontend_url
    _users_file = os.path.join(config.get("databasesFolder", "data"), "users.json")
    _jwt_secret = secrets_cfg.get("jwt_secret", "datalake-studio-default-secret-change-in-production")
    _google_client_id = secrets_cfg.get("google_client_id", "")
    _frontend_url = config.get("frontendUrl", "http://localhost:8080")
    if not os.path.exists(_users_file):
        _save_users({})
    log.info(f"Auth service initialized. Users file: {_users_file}")

def get_google_client_id():
    return _google_client_id

def requires_email_verification():
    return mailService.is_configured()

def _load_users():
    if not os.path.exists(_users_file):
        return {}
    with open(_users_file, 'r') as f:
        return json.load(f)

def _save_users(users):
    with open(_users_file, 'w') as f:
        json.dump(users, f, indent=2)

def register(username, password):
    if not username or not password:
        return None, "Username and password required"
    username = username.strip().lower()
    if len(username) < 2 or len(password) < 4:
        return None, "Min 2 chars username, 4 chars password"
    users = _load_users()
    if username in users:
        return None, "User already exists"

    user_data = {
        "password_hash": bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    if mailService.is_configured():
        token = secrets.token_urlsafe(32)
        user_data["email_verified"] = False
        user_data["verification_token"] = token
        users[username] = user_data
        _save_users(users)
        _send_verification_email(username, token)
        log.info(f"User registered (pending verification): {username}")
        return username, "verification_pending"
    else:
        user_data["email_verified"] = True
        users[username] = user_data
        _save_users(users)
        log.info(f"User registered: {username}")
        return username, "ok"

def _send_verification_email(email, token):
    link = f"{_frontend_url}/?verify={token}"
    html = f"""
    <h2>Datalake Studio - Verify your email</h2>
    <p>Click the link below to verify your account:</p>
    <p><a href="{link}" style="display:inline-block;padding:10px 24px;background:#0d6efd;color:white;text-decoration:none;border-radius:6px;">Verify Email</a></p>
    <p>Or copy this URL: {link}</p>
    <p>This link does not expire until used.</p>
    """
    mailService.send(email, "Datalake Studio - Verify your email", html)

def verify_email(token):
    users = _load_users()
    for username, data in users.items():
        if data.get("verification_token") == token:
            data["email_verified"] = True
            data.pop("verification_token", None)
            _save_users(users)
            log.info(f"Email verified: {username}")
            return username
    return None

def authenticate(username, password):
    if not username or not password:
        return None, "Username and password required"
    username = username.strip().lower()
    users = _load_users()
    if username not in users:
        return None, "Invalid credentials"
    user = users[username]
    if not user.get("password_hash"):
        return None, "This account uses Google sign-in"
    if not bcrypt.checkpw(password.encode('utf-8'), user["password_hash"].encode('utf-8')):
        return None, "Invalid credentials"
    if mailService.is_configured() and not user.get("email_verified", True):
        return None, "Email not verified. Check your inbox."
    return username, "ok"

def create_token(username):
    expire = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    payload = {"sub": username, "exp": expire}
    return jwt.encode(payload, _jwt_secret, algorithm=JWT_ALGORITHM)

def verify_token(token):
    try:
        payload = jwt.decode(token, _jwt_secret, algorithms=[JWT_ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None

def find_or_create_google_user(email):
    email = email.strip().lower()
    users = _load_users()
    if email not in users:
        users[email] = {
            "password_hash": None,
            "auth_provider": "google",
            "email_verified": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        _save_users(users)
        log.info(f"Google user created: {email}")
    return email

def verify_google_token(id_token_str):
    if not _google_client_id:
        return None
    try:
        from google.oauth2 import id_token
        from google.auth.transport import requests as google_requests
        idinfo = id_token.verify_oauth2_token(
            id_token_str, google_requests.Request(), _google_client_id
        )
        return idinfo.get("email")
    except Exception as e:
        log.warning(f"Google token verification failed: {e}")
        return None

def request_password_reset(username):
    if not mailService.is_configured():
        return False, "Mail not configured"
    username = username.strip().lower()
    users = _load_users()
    if username not in users:
        return True, "ok"  # Don't reveal if user exists
    user = users[username]
    if not user.get("password_hash"):
        return True, "ok"  # Google-only account, silently ignore
    token = secrets.token_urlsafe(32)
    user["reset_token"] = token
    user["reset_token_expires"] = (datetime.now(timezone.utc) + timedelta(hours=RESET_TOKEN_HOURS)).isoformat()
    _save_users(users)
    link = f"{_frontend_url}/?reset={token}"
    html = f"""
    <h2>Datalake Studio - Reset your password</h2>
    <p>Click the link below to reset your password:</p>
    <p><a href="{link}" style="display:inline-block;padding:10px 24px;background:#0d6efd;color:white;text-decoration:none;border-radius:6px;">Reset Password</a></p>
    <p>Or copy this URL: {link}</p>
    <p>This link expires in {RESET_TOKEN_HOURS} hour(s).</p>
    """
    mailService.send(username, "Datalake Studio - Reset your password", html)
    log.info(f"Password reset requested: {username}")
    return True, "ok"

def reset_password(token, new_password):
    if not new_password or len(new_password) < 4:
        return False, "Password must be at least 4 characters"
    users = _load_users()
    for username, data in users.items():
        if data.get("reset_token") == token:
            expires = data.get("reset_token_expires", "")
            if expires and datetime.fromisoformat(expires) < datetime.now(timezone.utc):
                data.pop("reset_token", None)
                data.pop("reset_token_expires", None)
                _save_users(users)
                return False, "Reset link has expired"
            data["password_hash"] = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            data.pop("reset_token", None)
            data.pop("reset_token_expires", None)
            data["email_verified"] = True
            _save_users(users)
            log.info(f"Password reset completed: {username}")
            return True, username
    return False, "Invalid or expired reset link"
