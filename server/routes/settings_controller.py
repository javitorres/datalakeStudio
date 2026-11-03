from typing import Any, Dict

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from services import chatGPTService, preferencesService, settingsService

router = APIRouter(prefix="/settings")


@router.get("/status")
def status():
    return settingsService.status()


@router.get("/preferences")
def getPreferences():
    return preferencesService.get()


@router.patch("/preferences")
def updatePreferences(changes: Dict[str, Any]):
    try:
        return preferencesService.update(changes)
    except ValueError as e:
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=400)


@router.get("/models")
def models():
    return chatGPTService.models()
