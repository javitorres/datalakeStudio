import asyncio
import json
import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import openai

from config import Config
from routes import gpt_controller
from services import chatGPTService


def _openai_error(cls):
    # The SDK builds these from an HTTP response; the service only looks at the type
    error = cls.__new__(cls)
    error.status_code, error.message = 500, "boom"
    return error


class FakeOpenAI:
    """Stands in for openai.OpenAI: records the requests and answers with `answer` or raises `error`."""
    answer = "SELECT 1"
    error = None
    calls = []

    def __init__(self, api_key):
        self.api_key = api_key
        self.responses = SimpleNamespace(create=self._create)

    def _create(self, **request):
        FakeOpenAI.calls.append(request)
        if FakeOpenAI.error:
            raise FakeOpenAI.error
        return SimpleNamespace(output_text=FakeOpenAI.answer)


class GptControllerTest(unittest.TestCase):
    def setUp(self):
        self.previous_config = Config._instance
        config = Config.__new__(Config)
        config.config = {}
        config.secrets = {"openai_api_key": "sk-test"}
        Config._instance = config
        FakeOpenAI.answer, FakeOpenAI.error, FakeOpenAI.calls = "SELECT 1", None, []
        patcher = patch.object(chatGPTService, "OpenAI", FakeOpenAI)
        patcher.start()
        self.addCleanup(patcher.stop)
        tables = patch.object(gpt_controller.databaseService, "getTableList", return_value=[])
        tables.start()
        self.addCleanup(tables.stop)

    def tearDown(self):
        Config._instance = self.previous_config

    @staticmethod
    def _json(response):
        return json.loads(response.body.decode("utf-8"))

    def test_sql_answer_without_markdown_or_semicolon(self):
        FakeOpenAI.answer = "```sql\nSELECT count(*) FROM trips;\n```"

        response = gpt_controller.askGPT("how many trips?")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._json(response), "SELECT count(*) FROM trips")
        self.assertEqual(FakeOpenAI.calls[0]["model"], chatGPTService.DEFAULT_MODEL)
        self.assertIn("how many trips?", FakeOpenAI.calls[0]["input"])

    def test_model_from_config(self):
        Config._instance.config = {"aiModel": "gpt-test"}

        gpt_controller.genericQuestion("what is this data?")

        self.assertEqual(FakeOpenAI.calls[0]["model"], "gpt-test")

    def test_generic_question(self):
        FakeOpenAI.answer = "Most trips start in Manhattan"

        response = gpt_controller.genericQuestion("where do trips start?")

        self.assertEqual(self._json(response), {"answer": "Most trips start in Manhattan"})

    def _explain(self, answer, csv="zone,trips,fare\nBronx,3,10.5\nQueens,5,12\n", language=None):
        FakeOpenAI.answer = answer if isinstance(answer, str) else json.dumps(answer)
        request = gpt_controller.ExplainResultRequest(question="trips per zone as a pie", sql="SELECT 1", csv=csv,
                                                      language=language)
        return self._json(gpt_controller.explainResult(request))

    def test_explain_result_with_a_chart(self):
        result = self._explain({"answer": "**Queens** leads", "chart": {
            "type": "pie", "title": "Trips per zone", "x": "zone", "y": ["trips", "fare"]}}, language="es")

        self.assertEqual(result, {"answer": "**Queens** leads", "chart": {
            "type": "pie", "title": "Trips per zone", "x": "zone", "y": ["trips"]}})
        request = FakeOpenAI.calls[0]
        self.assertEqual(request["text"]["format"]["type"], "json_schema")
        self.assertIn("Bronx,3,10.5", request["input"])
        self.assertIn("Spanish from Spain", request["instructions"])

    def test_explain_result_drops_charts_that_do_not_fit_the_result(self):
        for chart in ({"type": "none", "title": "", "x": "", "y": []},
                      {"type": "bar", "title": "t", "x": "borough", "y": ["trips"]},
                      {"type": "bar", "title": "t", "x": "zone", "y": ["nope"]},
                      {"type": "radar", "title": "t", "x": "zone", "y": ["trips"]}):
            self.assertIsNone(self._explain({"answer": "ok", "chart": chart})["chart"], chart)

    def test_explain_result_without_json_and_long_results(self):
        self.assertEqual(self._explain("Plain answer"), {"answer": "Plain answer", "chart": None})

        csv = "n\n" + "\n".join(str(i) for i in range(20000))
        self._explain({"answer": "ok", "chart": None}, csv=csv)
        sent = FakeOpenAI.calls[-1]["input"]
        self.assertLess(len(sent), chatGPTService.RESULT_CSV_LIMIT + 200)
        self.assertTrue(sent.endswith("(... more rows)"))

    def test_conversation_title(self):
        FakeOpenAI.answer = '"Viajes por barrio."\n'

        response = gpt_controller.conversationTitle("¿Cuántos viajes empiezan en cada barrio?", language="es")

        self.assertEqual(self._json(response), {"title": "Viajes por barrio"})
        self.assertIn("Spanish from Spain", FakeOpenAI.calls[0]["instructions"])

    def test_conversation_title_falls_back_to_the_question(self):
        FakeOpenAI.answer = "  "

        response = gpt_controller.conversationTitle("x" * 80)

        self.assertEqual(self._json(response), {"title": "x" * chatGPTService.TITLE_LIMIT})

    def test_missing_api_key(self):
        for secrets in ({}, {"openai_api_key": "YOUR_OPENAI_API_KEY"}):
            Config._instance.secrets = secrets

            response = gpt_controller.askGPT("how many trips?")

            self.assertEqual(response.status_code, 503)
            self.assertIn("openai_api_key", self._json(response)["message"])
        self.assertEqual(FakeOpenAI.calls, [])

    def test_openai_errors_become_messages_never_401(self):
        cases = [(openai.AuthenticationError, 502, "rejected the API key"),
                 (openai.NotFoundError, 502, "not available"),
                 (openai.RateLimitError, 429, "rate limit"),
                 (openai.APIConnectionError, 504, "Could not reach OpenAI"),
                 (openai.InternalServerError, 502, "OpenAI error 500")]
        for cls, status, message in cases:
            with self.subTest(cls.__name__):
                FakeOpenAI.error = _openai_error(cls)

                response = gpt_controller.askGPT("how many trips?")

                self.assertEqual(response.status_code, status)
                self.assertIn(message, self._json(response)["message"])

    def test_text2speech_error_removes_temp_file(self):
        Config._instance.secrets = {}
        before = set(os.listdir(tempfile.gettempdir()))

        response = gpt_controller.text2speech("hello")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(set(os.listdir(tempfile.gettempdir())) - before, set())

    def _speak_with_elevenlabs(self, status_code=200, content=b"ID3 fake mp3"):
        Config._instance.secrets = {"openai_api_key": "sk-test", "elevenlabs_api_key": "el-test"}
        Config._instance.config = {"elevenLabsVoices": {"es": "voice-1"}}
        reply = SimpleNamespace(status_code=status_code, ok=status_code < 400, content=content, text="error")
        with patch.object(chatGPTService.requests, "post", return_value=reply) as post:
            response = gpt_controller.text2speech("hello")
        return response, post

    def test_text2speech_prefers_elevenlabs(self):
        response, post = self._speak_with_elevenlabs()

        self.assertEqual(response.media_type, "audio/mpeg")
        body = b"".join(asyncio.run(self._read(response)))
        self.assertEqual(body, b"ID3 fake mp3")
        url, = post.call_args.args
        self.assertTrue(url.endswith("/v1/text-to-speech/voice-1"))
        self.assertEqual(post.call_args.kwargs["headers"], {"xi-api-key": "el-test"})
        self.assertEqual(post.call_args.kwargs["json"], {"text": "hello.", "model_id": chatGPTService.DEFAULT_ELEVENLABS_MODEL,
                                                         "apply_text_normalization": "on"})

    def test_elevenlabs_voice_and_language_follow_the_app_language(self):
        Config._instance.secrets = {"elevenlabs_api_key": "el-test"}
        Config._instance.config = {"elevenLabsVoices": {"en": "voice-en"}}
        reply = SimpleNamespace(status_code=200, ok=True, content=b"mp3", text="")
        for language, voice in (("en", "voice-en"), ("es", chatGPTService.DEFAULT_ELEVENLABS_VOICES["es"])):
            with patch.object(chatGPTService.requests, "post", return_value=reply) as post:
                gpt_controller.text2speech("hola", language=language)

            self.assertTrue(post.call_args.args[0].endswith("/" + voice))
            self.assertEqual(post.call_args.kwargs["json"]["language_code"], language)

    def test_provider_openai_skips_elevenlabs(self):
        Config._instance.secrets = {"elevenlabs_api_key": "el-test"}
        with patch.object(chatGPTService.requests, "post") as post:
            response = gpt_controller.text2speech("hello", provider="openai")

        self.assertEqual(response.status_code, 503)   # no OpenAI key in this test
        post.assert_not_called()

    def test_provider_elevenlabs_without_key(self):
        response = gpt_controller.text2speech("hello", provider="elevenlabs")

        self.assertEqual(response.status_code, 503)
        self.assertIn("elevenlabs_api_key", self._json(response)["message"])

    def test_speakable_drops_markdown(self):
        text = "La media por especie es:\n\n- **Iris-virginica:** 5.552\n- **Iris-setosa:** 1.464\n\n## Nota\nUsa `tip_amount`"

        self.assertEqual(chatGPTService.speakable(text, "es"),
                         "La media por especie es: Iris-virginica: 5.552. Iris-setosa: 1.464. Nota. Usa tip amount.")
        long_text = chatGPTService.speakable("palabra " * 200, "en")
        self.assertTrue(long_text.endswith(chatGPTService.TOO_LONG["en"]))
        self.assertLessEqual(len(long_text), chatGPTService.SPEECH_LIMIT + len(chatGPTService.TOO_LONG["en"]))

    def test_generic_question_answers_in_the_app_language(self):
        gpt_controller.genericQuestion("what is this?", language="es")
        gpt_controller.genericQuestion("what is this?", language="xx")

        self.assertIn("Spanish from Spain", FakeOpenAI.calls[0]["instructions"])
        self.assertNotIn("Always answer", FakeOpenAI.calls[1]["instructions"])

    @staticmethod
    async def _read(response):
        return [chunk async for chunk in response.body_iterator]

    def test_elevenlabs_errors_become_messages(self):
        for status, expected_status, message in ((401, 502, "rejected the API key"), (402, 429, "quota"),
                                                 (404, 502, "voice voice-1 not found"), (500, 502, "ElevenLabs error 500")):
            with self.subTest(status):
                response, _ = self._speak_with_elevenlabs(status)

                self.assertEqual(response.status_code, expected_status)
                self.assertIn(message, self._json(response)["message"])

    def test_text2speech_without_elevenlabs_key_uses_openai(self):
        Config._instance.secrets = {"elevenlabs_api_key": "YOUR_ELEVENLABS_API_KEY"}
        with patch.object(chatGPTService.requests, "post") as post:
            response = gpt_controller.text2speech("hello")

        # No OpenAI key either: the OpenAI path asks for it
        self.assertEqual(response.status_code, 503)
        self.assertIn("openai_api_key", self._json(response)["message"])
        post.assert_not_called()


if __name__ == "__main__":
    unittest.main()
