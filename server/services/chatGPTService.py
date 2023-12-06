import openai
from services.duckDbService import getTableDescriptionForChatGpt

def askGpt(questionForChatGPT, organization, apikey):
    openai.organization = organization
    openai.api_key = apikey

    print("Sending question to GPT-3: " + questionForChatGPT)
    completion = openai.ChatCompletion.create(model="gpt-4-1106-preview", messages=[
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