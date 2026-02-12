import openai
from services.databaseService import getTableDescriptionForChatGpt
from openai import OpenAI
import os



def askGpt(questionForChatGPT, apikey):
    client = OpenAI(
        #api_key=os.environ.get("OPENAI_API_KEY"),
        api_key=apikey,
    )
    #openai.organization = organization
    #openai.api_key = apikey

    print("Sending question to GPT-3: " + questionForChatGPT)
    completion = client.chat.completions.create(model="gpt-4-1106-preview", messages=[
        {"role": "system", "content": """You are a SQL assistant, you only have to answer with SQL queries, no other text, only SQL. 
         Use exactly the table names provided. Don't put any other text that are not in the question or any other text that could break de SQL 
         syntax. Don't use any other character or context than the query itself. For example, don't include ```sql header in the response
        """},
        {"role": "user", "content": questionForChatGPT, "name": "DatalakeStudio"}
        ])
    print("GPT response: " + completion.choices[0].message.content)
    # Remove ```sql header and footer and trailing semicolon
    response = completion.choices[0].message.content.replace("```sql", "").replace("```", "").strip()
    # Remove trailing semicolon if present
    if (response.endswith(";")):
        response = response[:-1]
    return response

####################################################

def transcribeAudioFile(file, apikey) :
    client = OpenAI(
        #api_key=os.environ.get("OPENAI_API_KEY"),
        api_key=apikey,
    )
    audio_file = open(file, "rb")
    transcript = client.audio.transcriptions.create(
        model="whisper-1", 
        file=audio_file, 
        response_format="text"
        )
    return transcript

####################################################

def text2speech(text, file, apikey) :
    client = OpenAI(
        #api_key=os.environ.get("OPENAI_API_KEY"),
        api_key=apikey,
    )

    if len(text) > 200:
        text = text[:200]
        text += "...paro aquí porque es demasiado largo"

    response = client.audio.speech.create(
        model = "tts-1",
        voice = "alloy",
        input = text
        )

    response.stream_to_file(file)

####################################################
def askGptGenericQuestion(question, apikey):
    client = OpenAI(
        #api_key=os.environ.get("OPENAI_API_KEY"),
        api_key=apikey,
    )

    print("Sending question to GPT: " + question)
    completion = client.chat.completions.create(model="o3-mini", messages=[
        {"role": "system", "content": """You are a data assistant, you have to read the user question and the data provided and return a response 
         to help the user. You can use any text, but you have to return a response that is useful for the user. 
        """},
        {"role": "user", "content": question, "name": "DatalakeStudio"}
        ])
    response = completion.choices[0].message.content
    print("GPT response: " + response)
    return response    