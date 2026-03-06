from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from services import authService
from auth import is_auth_enabled

router = APIRouter(prefix="/auth")

class AuthRequest(BaseModel):
    username: str
    password: str

class GoogleAuthRequest(BaseModel):
    credential: str

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
    password: str

@router.post("/register")
def register(req: AuthRequest):
    username, status = authService.register(req.username, req.password)
    if username is None:
        return JSONResponse(content={"error": status}, status_code=409)
    if status == "verification_pending":
        return {"message": "verification_pending", "username": username}
    token = authService.create_token(username)
    return {"token": token, "username": username}

@router.post("/login")
def login(req: AuthRequest):
    username, status = authService.authenticate(req.username, req.password)
    if username is None:
        return JSONResponse(content={"error": status}, status_code=401)
    token = authService.create_token(username)
    return {"token": token, "username": username}

@router.post("/google")
def google_login(req: GoogleAuthRequest):
    email = authService.verify_google_token(req.credential)
    if email is None:
        return JSONResponse(content={"error": "Invalid Google token or Google auth not configured"}, status_code=401)
    username = authService.find_or_create_google_user(email)
    token = authService.create_token(username)
    return {"token": token, "username": username}

@router.get("/google-client-id")
def get_google_client_id():
    client_id = authService.get_google_client_id()
    return {"client_id": client_id if client_id else ""}

@router.get("/verify-email")
def verify_email(token: str):
    username = authService.verify_email(token)
    if username is None:
        return JSONResponse(content={"error": "Invalid or already used verification link"}, status_code=400)
    return {"message": "Email verified successfully", "username": username}

@router.post("/forgot-password")
def forgot_password(req: ForgotPasswordRequest):
    success, _ = authService.request_password_reset(req.email)
    # Always return success to avoid revealing if user exists
    return {"message": "If that email is registered, a reset link has been sent"}

@router.post("/reset-password")
def reset_password(req: ResetPasswordRequest):
    success, result = authService.reset_password(req.token, req.password)
    if not success:
        return JSONResponse(content={"error": result}, status_code=400)
    return {"message": "Password reset successfully"}

@router.get("/mail-configured")
def mail_configured():
    return {"configured": authService.requires_email_verification()}

@router.get("/auth-enabled")
def auth_enabled():
    return {"enabled": is_auth_enabled()}

@router.get("/me")
def me(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(content={"error": "Not authenticated"}, status_code=401)
    token = auth_header.split(" ")[1]
    username = authService.verify_token(token)
    if username is None:
        return JSONResponse(content={"error": "Invalid or expired token"}, status_code=401)
    return {"username": username}
