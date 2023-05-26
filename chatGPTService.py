import openai
from duckDbService import getTableDescriptionForChatGpt

def askGpt(question, tables, organization, apikey):
    openai.organization = organization
    openai.api_key = apikey

    tableListArray = None
    if (tables is not None):
        tableList = tables.df()
        tableListArray = tableList["name"].to_list()

    if (tableListArray is not None and len(tableListArray) > 0):
        questionForChatGPT = " You have the following tables:"
        for table in tableListArray:
            questionForChatGPT += " " + getTableDescriptionForChatGpt(table)
        
        questionForChatGPT += ". The query I need is:" + question
        print("Sending question to GPT-3: " + questionForChatGPT)
        completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=[
            {"role": "system", "content": """You are a SQL assistant, you only have to answer with SQL queries, no other text, only SQL. Use exactly the table names provided. Don't put any other text that are not in the question or any other text that could break de SQL sintax
            """},
            {"role": "user", "content": questionForChatGPT, "name": "DatalakeStudio"}
            ])
        print("GPT-3 response: " + completion.choices[0].message.content)
        return completion.choices[0].message.content