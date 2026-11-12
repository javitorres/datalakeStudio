from fastapi import APIRouter
from services import databaseService
from fastapi import Response
from fastapi.responses import JSONResponse, StreamingResponse
import services.chatGPTService as chatGPTService

from fastapi import FastAPI, File, UploadFile
from typing import List, Optional

from pydantic import BaseModel, Field
from pydub import AudioSegment
import io
import os
import tempfile


router = APIRouter(prefix="/gpt")


def _assistant_error(e):
    # Never 401: the client logs the user out on it
    return JSONResponse(content={"status": "error", "message": e.message}, status_code=e.status_code)


def _tables_description():
    tables = databaseService.getTableList()
    return " ".join(databaseService.getTableDescriptionForChatGpt(table) for table in tables or [])


@router.get("/askGPT")
def askGPT(question: str):
    tables = _tables_description()

    if tables:
        questionForChatGPT = " You have the following tables: " + tables
        questionForChatGPT += ". The query I need, for DuckDB is:" + question
    else:
        questionForChatGPT = "The query I need, for DuckDB is:" + question

    try:
        chatGPTResponse = chatGPTService.askGpt(questionForChatGPT)
    except chatGPTService.AssistantError as e:
        return _assistant_error(e)

    return JSONResponse(content=chatGPTResponse, status_code=200)

####################################################

@router.post("/askGPTWhisper")
async def askGPTWhisper(file: UploadFile = File(...), language: str = None):
    print("askGPTWhisper")
    if file.content_type != "audio/wav":
        content = {"error": "File is not WAV"}
        return JSONResponse(content=content, status_code=400)
    else:
        print("File is:" + str(file))
    
    # Read WAV
    audio_data = file.file.read()
    audio = AudioSegment.from_file(io.BytesIO(audio_data), format="wav")

    # To MP3
    output = io.BytesIO()
    audio.export(output, format="mp3")
    output.seek(0)

    # Write the audio to a unique temp file so concurrent requests don't clash.
    fd, filename = tempfile.mkstemp(suffix=".mp3")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(output.read())
        output.seek(0)

        transcription = chatGPTService.transcribeAudioFile(filename, language)
    except chatGPTService.AssistantError as e:
        return _assistant_error(e)
    finally:
        if os.path.exists(filename):
            os.remove(filename)


    # Remove \n and trailing semicolon if present
    transcription = transcription.replace("\n", "").strip()
    print("Transcription: '" + transcription + "'")

    # Why "you"?: Because this is the answer when empty audio is sent. TODO: Detect if audio es empty (mic muted, etc)
    if (transcription is not None and transcription != "you"):
        return JSONResponse(content={"transcription" : transcription}, status_code=200)
    elif (transcription == "you"):
        return JSONResponse(content={"transcription" : "EMPTY_AUDIO"}, status_code=200)
    else:
        return JSONResponse(content="Could not get transcription", status_code=500)

####################################################
@router.get("/genericQuestion")
def genericQuestion(question: str, language: str = None):
    if (question is None or question == ""):
        return JSONResponse(content="Empty question", status_code=400)
    elif (len(question) > 1000):
        # To avoid sent GPT a huge question due some error in the data provided by the user
        return JSONResponse(content={"answer": "Question too long"}, status_code=200)
        
    try:
        chatGPTResponse = chatGPTService.askGptGenericQuestion(question, language)
    except chatGPTService.AssistantError as e:
        return _assistant_error(e)
    
    return JSONResponse(content={"answer": chatGPTResponse}, status_code=200)


####################################################
class ExplainResultRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    sql: str = Field(max_length=20000)
    csv: str = Field(max_length=200000)
    language: Optional[str] = None


@router.post("/explainResult")
def explainResult(request: ExplainResultRequest):
    try:
        result = chatGPTService.explainResult(request.question, request.sql, request.csv, request.language)
    except chatGPTService.AssistantError as e:
        return _assistant_error(e)
    return JSONResponse(content=result, status_code=200)


####################################################
class DashboardRequest(BaseModel):
    instruction: str = Field(min_length=1, max_length=4000)
    # The dashboard to change and, on a retry, the previous answer and its problems
    current: Optional[str] = Field(default=None, max_length=60000)
    previous: Optional[str] = Field(default=None, max_length=60000)
    errors: List[str] = Field(default_factory=list, max_length=30)
    language: Optional[str] = None


@router.post("/dashboard")
def dashboard(request: DashboardRequest):
    try:
        result = chatGPTService.dashboard(_tables_description(), request.instruction, request.current,
                                          request.previous, request.errors, request.language)
    except chatGPTService.AssistantError as e:
        return _assistant_error(e)
    return JSONResponse(content=result, status_code=200)


####################################################
@router.get("/conversationTitle")
def conversationTitle(question: str, language: str = None):
    if not question.strip():
        return JSONResponse(content={"status": "error", "message": "Empty question"}, status_code=400)
    try:
        title = chatGPTService.conversationTitle(question, language)
    except chatGPTService.AssistantError as e:
        return _assistant_error(e)
    return JSONResponse(content={"title": title}, status_code=200)


####################################################
@router.get("/text2speech")
def text2speech(text: str, language: str = None, provider: str = "auto"):
    # Use a unique temp file so concurrent requests don't overwrite each other.
    fd, tmp_path = tempfile.mkstemp(suffix=".mp3")
    os.close(fd)
    try:
        chatGPTService.text2speech(text, tmp_path, language, provider)
    except chatGPTService.AssistantError as e:
        os.remove(tmp_path)
        return _assistant_error(e)

    def iterfile():
        try:
            with open(tmp_path, "rb") as f:
                yield from f
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    return StreamingResponse(iterfile(), media_type="audio/mpeg")


    