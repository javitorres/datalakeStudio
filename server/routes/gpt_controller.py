from fastapi import APIRouter
from services import databaseService
from fastapi import Response
from fastapi.responses import JSONResponse, StreamingResponse
import services.chatGPTService as chatGPTService

from fastapi import FastAPI, File, UploadFile
from pydub import AudioSegment
import io
import os
import tempfile

from config import Config

router = APIRouter(prefix="/gpt")

@router.get("/askGPT")
def askGPT(question: str):
    tables = databaseService.getTableList()

    if (tables is not None and len(tables) > 0):
        questionForChatGPT = " You have the following tables:"
        for table in tables:
            #if (table != "__lastQuery"):
            questionForChatGPT += " " + databaseService.getTableDescriptionForChatGpt(table)
        questionForChatGPT += ". The query I need, for DuckDB is:" + question
    else:
        questionForChatGPT = "The query I need, for DuckDB is:" + question

    chatGPTResponse = chatGPTService.askGpt(questionForChatGPT, Config.get_instance().get_secrets.get("openai_api_key"))
    print("GPT response: " + chatGPTResponse)

    return JSONResponse(content=chatGPTResponse, status_code=200)

####################################################

@router.post("/askGPTWhisper")
async def askGPTWhisper(file: UploadFile = File(...)):
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

        transcription = chatGPTService.transcribeAudioFile(filename, Config.get_instance().get_secrets.get("openai_api_key"))
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
def genericQuestion(question: str):
    if (question is None or question == ""):
        return JSONResponse(content="Empty question", status_code=400)
    elif (len(question) > 1000):
        # To avoid sent GPT a huge question due some error in the data provided by the user
        return JSONResponse(content={"answer": "Question too long"}, status_code=200)
        
    chatGPTResponse = chatGPTService.askGptGenericQuestion(question, Config.get_instance().get_secrets.get("openai_api_key"))
    print("GPT response: " + chatGPTResponse)
    
    return JSONResponse(content={"answer": chatGPTResponse}, status_code=200)


####################################################
@router.get("/text2speech")
def text2speech(text):
    # Use a unique temp file so concurrent requests don't overwrite each other.
    fd, tmp_path = tempfile.mkstemp(suffix=".mp3")
    os.close(fd)
    chatGPTService.text2speech(text, tmp_path, Config.get_instance().get_secrets.get("openai_api_key"))

    def iterfile():
        try:
            with open(tmp_path, "rb") as f:
                yield from f
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    return StreamingResponse(iterfile(), media_type="audio/mpeg")


    