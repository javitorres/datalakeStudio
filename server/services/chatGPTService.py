import csv as _csv
import io
import json
import re

import openai
import requests
from openai import OpenAI

from config import Config
from services import preferencesService

# Models, overridable in config.yml (aiModel, aiTranscriptionModel, aiSpeechModel)
DEFAULT_MODEL = "gpt-5.4-mini"
DEFAULT_TRANSCRIPTION_MODEL = "gpt-4o-mini-transcribe"
DEFAULT_SPEECH_MODEL = "gpt-4o-mini-tts"
# ElevenLabs reads the answers aloud when elevenlabs_api_key is set (higher quality than OpenAI), unless the
# user picks OpenAI in the app settings: model and voice per language overridable in config.yml
# (elevenLabsModel, elevenLabsVoices)
ELEVENLABS_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice}"
DEFAULT_ELEVENLABS_MODEL = "eleven_v4"
# Public voices: Cristina (Spanish from Spain) and George (British English)
DEFAULT_ELEVENLABS_VOICES = {"es": "dNjJKg63Fr5AXwIdkATa", "en": "JBFqnCBsd6RMkjVDRZzb"}

# App languages: the assistant answers, speaks and listens in the one the user picks
LANGUAGES = {"en": "English", "es": "Spanish from Spain"}
SPEECH_LIMIT = 400
TOO_LONG = {"en": "... I'll stop here because it is too long.", "es": "... paro aquí porque es demasiado largo."}

SQL_INSTRUCTIONS = """You are a SQL assistant, you only have to answer with SQL queries, no other text, only SQL.
Use exactly the table names provided. If the user asks for a chart, write the query that returns its data: a column for the
labels or the x axis and the numeric columns to plot, ordered so that it reads well. Don't put any other text that are not in the question or any other text that could break de SQL
syntax. Don't use any other character or context than the query itself. For example, don't include ```sql header in the response
"""
DATA_INSTRUCTIONS = """You are a data assistant, you have to read the user question and the data provided and return a response
to help the user. You can use any text, but you have to return a response that is useful for the user.
"""


RESULT_INSTRUCTIONS = """You are a data assistant. Read the user question, the SQL that answered it and its result (CSV), and
answer the question using that data, in Markdown.
Also choose a chart for the result in "chart":
- When the user asks for a chart, use the type they ask for (pie, bar, horizontalBar, line, area or scatter) or the best one.
- When they don't, propose one only if it clearly helps: several rows with a label and a numeric column. Otherwise type is "none".
- x is the column with the labels or the x axis, y the numeric columns to plot. Use exact column names from the CSV header.
- pie takes one y column; scatter takes a numeric x.
Don't describe the chart in the answer: the app draws it below.
"""
CHART_TYPES = ["none", "pie", "bar", "horizontalBar", "line", "area", "scatter"]
RESULT_FORMAT = {"format": {"type": "json_schema", "name": "result_answer", "strict": True, "schema": {
    "type": "object", "additionalProperties": False, "required": ["answer", "chart"],
    "properties": {
        "answer": {"type": "string"},
        "chart": {"type": "object", "additionalProperties": False, "required": ["type", "title", "x", "y"], "properties": {
            "type": {"type": "string", "enum": CHART_TYPES},
            "title": {"type": "string"},
            "x": {"type": "string"},
            "y": {"type": "array", "items": {"type": "string"}},
        }},
    },
}}}
# CSV characters sent to explain a result: fewer characters, fewer tokens
RESULT_CSV_LIMIT = 20000

# The same text as DASHBOARD_SYSTEM_PROMPT in client/src/ai/prompts.js
DASHBOARD_INSTRUCTIONS = """You design data dashboards for Datalake Studio. From the user's tables and their instruction, answer with a
dashboard specification in JSON. The app runs the SQL on DuckDB and draws the widgets itself.
- datasets: named DuckDB SELECT queries with the rows the widgets aggregate. Keep them simple: usually "SELECT * FROM table",
  adding the computed columns the widgets need (date_trunc('month', ts) AS month, CASE buckets...). Don't aggregate in a
  dataset: the widgets aggregate. One statement each, no trailing semicolon. Use exactly the table and column names given.
- widgets, in reading order, on a 12-column grid (width 3, 4, 6, 8 or 12):
  - kpi: one to four headline numbers (measures), no dimension.
  - bar, horizontalBar, pie: measures grouped by a categorical dimension.
  - line, area: measures along an ordered dimension (dates, numbers), with sort "dimension".
  - histogram: the distribution of the numeric column in dimension.
  - table: rows of the dataset; columns lists the ones to show (empty for all).
  - text: a short Markdown note in text.
  - measures: column, agg (count, countDistinct, sum, avg, min, max or median) and a short label. Column "*" with count
    counts the rows.
  - sort: "value" (largest first) or "dimension". limit: maximum groups or rows (0 for the default).
  - Fields a widget doesn't use: empty string, empty array or 0.
- filters: controls that filter every dataset that has that column: select (categories), range (numbers) or dateRange
  (dates and timestamps). Add the 2 to 4 most useful ones. The user can also click bars and pie slices to filter by them.
Start with the KPIs, then the charts: 5 to 9 widgets unless asked otherwise. When there is a current dashboard, apply the
instruction to it and return the whole updated specification, keeping what the user didn't ask to change.
summary: one or two sentences telling the user what you built or changed.
"""
DASHBOARD_WIDGETS = ["kpi", "bar", "horizontalBar", "line", "area", "pie", "histogram", "table", "text"]
DASHBOARD_AGGREGATIONS = ["count", "countDistinct", "sum", "avg", "min", "max", "median"]


def _object(properties):
    return {"type": "object", "additionalProperties": False, "required": list(properties), "properties": properties}


_STRING = {"type": "string"}
DASHBOARD_FORMAT = {"format": {"type": "json_schema", "name": "dashboard", "strict": True, "schema": _object({
    "title": _STRING,
    "summary": _STRING,
    "datasets": {"type": "array", "items": _object({"id": _STRING, "sql": _STRING})},
    "filters": {"type": "array", "items": _object({
        "column": _STRING, "type": {"type": "string", "enum": ["select", "range", "dateRange"]}, "label": _STRING})},
    "widgets": {"type": "array", "items": _object({
        "type": {"type": "string", "enum": DASHBOARD_WIDGETS},
        "title": _STRING,
        "dataset": _STRING,
        "dimension": _STRING,
        "measures": {"type": "array", "items": _object({
            "column": _STRING, "agg": {"type": "string", "enum": DASHBOARD_AGGREGATIONS}, "label": _STRING})},
        "columns": {"type": "array", "items": _STRING},
        "text": _STRING,
        "width": {"type": "integer", "enum": [3, 4, 6, 8, 12]},
        "sort": {"type": "string", "enum": ["value", "dimension"]},
        "limit": {"type": "integer"},
    })},
})}}

TITLE_INSTRUCTIONS = """Give a short title, of 2 to 6 words, to a conversation that starts with the user question below.
Answer only with the title: no quotes, no final period, no prefix.
"""
TITLE_LIMIT = 60


class AssistantError(Exception):
    """The assistant can't answer: no API key, or OpenAI refused or failed. status_code is the HTTP status to return."""

    def __init__(self, message, status_code=502):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _setting(name, default):
    return (Config.get_instance().get_config or {}).get(name) or default


def _chat_model():
    """The model the user chose in the app settings, else the one in config.yml, else the default."""
    return preferencesService.get().get("aiModel") or _setting("aiModel", DEFAULT_MODEL)


def _client():
    apikey = (Config.get_instance().get_secrets or {}).get("openai_api_key")
    if not apikey or apikey == "YOUR_OPENAI_API_KEY":
        raise AssistantError("The AI assistant needs an OpenAI API key: set openai_api_key in server/secrets.yml", 503)
    return OpenAI(api_key=apikey)


def _call(model, request):
    """Runs an OpenAI request and turns its errors into an AssistantError with a message for the user."""
    try:
        return request()
    except openai.AuthenticationError:
        raise AssistantError("OpenAI rejected the API key in server/secrets.yml")
    except openai.PermissionDeniedError:
        raise AssistantError(f"The OpenAI API key has no access to the model {model}")
    except openai.NotFoundError:
        raise AssistantError(f"The model {model} is not available for this OpenAI API key")
    except openai.RateLimitError:
        raise AssistantError("OpenAI rate limit or quota exceeded, try again later", 429)
    except (openai.APIConnectionError, openai.APITimeoutError):
        raise AssistantError("Could not reach OpenAI", 504)
    except openai.APIStatusError as e:
        raise AssistantError(f"OpenAI error {e.status_code}: {e.message}")


def _ask(instructions, question):
    client = _client()
    model = _chat_model()
    response = _call(model, lambda: client.responses.create(model=model, instructions=instructions, input=question))
    return response.output_text


def askGpt(questionForChatGPT):
    print("Sending question to GPT: " + questionForChatGPT)
    answer = _ask(SQL_INSTRUCTIONS, questionForChatGPT)
    print("GPT response: " + answer)
    # Remove ```sql header and footer and trailing semicolon
    response = answer.replace("```sql", "").replace("```", "").strip()
    if (response.endswith(";")):
        response = response[:-1]
    return response

####################################################

def language_or_none(language):
    return language if language in LANGUAGES else None


def transcribeAudioFile(file, language=None):
    client = _client()
    model = _setting("aiTranscriptionModel", DEFAULT_TRANSCRIPTION_MODEL)
    # The language helps with short questions, which are otherwise often taken for another language
    extra = {"language": language} if language_or_none(language) else {}
    with open(file, "rb") as audio_file:
        return _call(model, lambda: client.audio.transcriptions.create(
            model=model,
            file=audio_file,
            response_format="text",
            **extra
        ))

####################################################

def elevenlabs_available():
    apikey = (Config.get_instance().get_secrets or {}).get("elevenlabs_api_key")
    return None if not apikey or apikey == "YOUR_ELEVENLABS_API_KEY" else apikey


def _elevenlabs_speech(text, file, apikey, language):
    model = _setting("elevenLabsModel", DEFAULT_ELEVENLABS_MODEL)
    voices = {**DEFAULT_ELEVENLABS_VOICES, **(_setting("elevenLabsVoices", None) or {})}
    voice = voices.get(language or "es")
    # Normalization reads numbers as words in the text's language ("2.63" -> "dos coma sesenta y tres")
    request = {"text": text, "model_id": model, "apply_text_normalization": "on"}
    if language:
        request["language_code"] = language
    try:
        response = requests.post(ELEVENLABS_URL.format(voice=voice), params={"output_format": "mp3_44100_128"},
                                 headers={"xi-api-key": apikey}, json=request, timeout=60)
    except requests.RequestException:
        raise AssistantError("Could not reach ElevenLabs", 504)
    if response.status_code == 401:
        raise AssistantError("ElevenLabs rejected the API key in server/secrets.yml")
    if response.status_code in (402, 429):
        raise AssistantError("ElevenLabs quota or rate limit exceeded, try again later", 429)
    if response.status_code == 404:
        raise AssistantError(f"ElevenLabs voice {voice} not found")
    if not response.ok:
        raise AssistantError(f"ElevenLabs error {response.status_code}: {response.text[:200]}")
    with open(file, "wb") as f:
        f.write(response.content)


def speakable(text, language=None):
    """The answer as it should be read aloud: no markdown marks, list items as sentences, and cut if too long."""
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"[*`]+", "", text)
    text = re.sub(r"^\s*(?:#+|>|[-+]|\d+[.)])\s+", "", text, flags=re.M)
    text = text.replace("_", " ")
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    text = " ".join(line if line[-1] in ".:;!?," else line + "." for line in lines)
    if len(text) > SPEECH_LIMIT:
        text = text[:SPEECH_LIMIT].rsplit(" ", 1)[0] + TOO_LONG[language or "es"]
    return text


def text2speech(text, file, language=None, provider="auto"):
    """provider: "auto" (ElevenLabs when it has a key, else OpenAI), "elevenlabs" or "openai"."""
    language = language_or_none(language)
    text = speakable(text, language)

    elevenlabs_key = elevenlabs_available()
    if provider != "openai" and elevenlabs_key:
        return _elevenlabs_speech(text, file, elevenlabs_key, language)
    if provider == "elevenlabs":
        raise AssistantError("ElevenLabs is not configured: set elevenlabs_api_key in server/secrets.yml", 503)

    client = _client()
    model = _setting("aiSpeechModel", DEFAULT_SPEECH_MODEL)
    extra = {"instructions": f"Speak in {LANGUAGES[language]}."} if language else {}

    def speak():
        with client.audio.speech.with_streaming_response.create(model=model, voice="alloy", input=text,
                                                                **extra) as response:
            response.stream_to_file(file)

    _call(model, speak)

####################################################
def askGptGenericQuestion(question, language=None):
    print("Sending question to GPT: " + question)
    instructions = DATA_INSTRUCTIONS
    if language_or_none(language):
        instructions += f"\nAlways answer in {LANGUAGES[language]}.\n"
    response = _ask(instructions, question)
    print("GPT response: " + response)
    return response


####################################################
def conversationTitle(question, language=None):
    """A short title for a conversation, from its first question."""
    instructions = TITLE_INSTRUCTIONS
    if language_or_none(language):
        instructions += f"Write the title in {LANGUAGES[language]}.\n"
    title = _ask(instructions, question[:1000]).strip().strip('"\'«»“”').rstrip(".").strip()
    return title[:TITLE_LIMIT].strip() or question[:TITLE_LIMIT].strip()


####################################################
def _chart(chart, columns):
    """The chart the AI chose, if it plots columns of the result."""
    if not isinstance(chart, dict) or chart.get("type") not in CHART_TYPES[1:]:
        return None
    y = [c for c in chart.get("y") or [] if c in columns]
    if chart.get("x") not in columns or not y:
        return None
    if chart["type"] == "pie":
        y = y[:1]
    return {"type": chart["type"], "title": str(chart.get("title") or ""), "x": chart["x"], "y": y}


def explainResult(question, sql, csv, language=None):
    """Answers the question from the query result, and chooses a chart for it: {answer, chart or None}."""
    instructions = RESULT_INSTRUCTIONS
    if language_or_none(language):
        instructions += f"\nAlways answer in {LANGUAGES[language]}, also the chart title.\n"
    if len(csv) > RESULT_CSV_LIMIT:
        csv = csv[:RESULT_CSV_LIMIT].rsplit("\n", 1)[0] + "\n(... more rows)"
    columns = next(iter(_csv.reader(io.StringIO(csv))), [])
    request = f"User question: {question}\n\nSQL:\n{sql}\n\nResult (CSV):\n{csv}"

    client = _client()
    model = _chat_model()
    output = _call(model, lambda: client.responses.create(
        model=model, instructions=instructions, input=request, text=RESULT_FORMAT)).output_text
    try:
        parsed = json.loads(output)
    except ValueError:
        # Not JSON: the answer alone
        return {"answer": output, "chart": None}
    return {"answer": str(parsed.get("answer") or ""), "chart": _chart(parsed.get("chart"), columns)}


####################################################
def dashboardRequest(tables, instruction, current=None, previous=None, errors=None):
    """What the model is asked: the tables, the dashboard to change (if any), the instruction and, on a
    retry, its previous answer with what was wrong in it."""
    request = (f"You have the following tables: {tables}.\n\n" if tables else "")
    if current:
        request += f"Current dashboard:\n{current}\n\n"
    request += f"Instruction: {instruction}"
    if errors:
        request += (f"\n\nYour previous answer was:\n{previous or ''}\n\nIt had these problems, fix them:\n"
                    + "\n".join("- " + error for error in errors))
    return request


def dashboard(tables, instruction, current=None, previous=None, errors=None, language=None):
    """A dashboard specification for the instruction, as the model wrote it: the app validates it."""
    instructions = DASHBOARD_INSTRUCTIONS
    if language_or_none(language):
        instructions += f"\nAlways write the titles, the labels and the summary in {LANGUAGES[language]}.\n"
    client = _client()
    model = _chat_model()
    output = _call(model, lambda: client.responses.create(
        model=model, instructions=instructions, input=dashboardRequest(tables, instruction, current, previous, errors),
        text=DASHBOARD_FORMAT)).output_text
    try:
        parsed = json.loads(output)
    except ValueError:
        parsed = None
    if not isinstance(parsed, dict):
        raise AssistantError("The AI didn't answer with a dashboard, try again")
    return parsed


####################################################
# Models that can't answer text with the Responses API, or snapshots of another one (gpt-5-2025-08-07)
_NOT_CHAT = re.compile(r"audio|realtime|tts|transcribe|image|search|embedding|moderation|instruct|-\d{4}-\d{2}-\d{2}$")
_CHAT = re.compile(r"(gpt-\d|o\d)")


def models():
    """The text models of the OpenAI key, to choose from in the app: {current, configured, models, error}."""
    configured = _setting("aiModel", DEFAULT_MODEL)
    found, error = [], None
    try:
        client = _client()
        found = sorted((m.id for m in _call("list", lambda: client.models.list())
                        if _CHAT.match(m.id) and not _NOT_CHAT.search(m.id)), reverse=True)
    except AssistantError as e:
        error = e.message
    current = _chat_model()
    for model in (configured, current):
        if model not in found:
            found.insert(0, model)
    return {"current": current, "configured": configured, "models": found, "error": error}
