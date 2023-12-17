from fastapi import APIRouter
from services import duckDbService
from fastapi import Response
from fastapi.responses import JSONResponse
import services.chatGPTService as chatGPTService

from config import Config

router = APIRouter()

@router.get("/askGPT")
def askGPT(question: str):
    tables = duckDbService.getTableList()

    if (tables is not None and len(tables) > 0):
        questionForChatGPT = " You have the following tables:"
        for table in tables:
            #if (table != "__lastQuery"):
            questionForChatGPT += " " + duckDbService.getTableDescriptionForChatGpt(table)
        questionForChatGPT += ". The query I need is:" + question

        chatGPTResponse = chatGPTService.askGpt(questionForChatGPT, 
                                                Config.get_instance().get_secrets.get("openai_organization"),
                                                Config.get_instance().get_secrets.get("openai_api_key"))
        print("GPT response: " + chatGPTResponse)
    
    return JSONResponse(content=chatGPTResponse, status_code=200)

