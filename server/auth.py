from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from services import authService
from services import databaseService
from config import Config

security = HTTPBearer(auto_error=False)

DEFAULT_USER = "default"

def is_auth_enabled():
    return Config.get_instance().get_config.get("authEnabled", True)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not is_auth_enabled():
        databaseService.set_current_user(DEFAULT_USER)
        return DEFAULT_USER
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    token = credentials.credentials
    username = authService.verify_token(token)
    if username is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    databaseService.set_current_user(username)
    return username
