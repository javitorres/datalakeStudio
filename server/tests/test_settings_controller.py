import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from config import Config
from routes import settings_controller
from services import chatGPTService, databaseService, settingsService


class SettingsControllerTest(unittest.TestCase):
    def setUp(self):
        self.previous_config = Config._instance
        config = Config.__new__(Config)
        config.config = {"authEnabled": True}
        config.secrets = {}
        Config._instance = config
        for name, value in (("_aws_credential_chain", False),):
            patcher = patch.object(settingsService, name, return_value=value)
            patcher.start()
            self.addCleanup(patcher.stop)
        mail = patch.object(settingsService.mailService, "is_configured", return_value=False)
        mail.start()
        self.addCleanup(mail.stop)

    def tearDown(self):
        Config._instance = self.previous_config

    def _status(self):
        return {i["id"]: i for i in settings_controller.status()["integrations"]}

    def test_nothing_configured(self):
        status = settings_controller.status()

        self.assertEqual(status["files"], {"config": True, "secrets": False})
        self.assertTrue(status["authEnabled"])
        self.assertFalse(any(i["configured"] for i in status["integrations"]))

    def test_defined_keys_and_placeholders(self):
        with tempfile.NamedTemporaryFile() as pgpass:
            Config._instance.secrets = {"openai_api_key": "sk-real", "elevenlabs_api_key": "YOUR_ELEVENLABS_API_KEY",
                                        "mapbox_access_token": "pk.real", "google_client_id": "  ",
                                        "pgpass_file": pgpass.name, "s3_access_key_id": "id", "s3_secret_access_key": "secret"}
            status = self._status()

        self.assertTrue(status["openai"]["configured"])
        self.assertFalse(status["elevenlabs"]["configured"])
        self.assertTrue(status["mapbox"]["configured"])
        self.assertFalse(status["google"]["configured"])
        self.assertTrue(status["postgres"]["configured"])
        self.assertEqual((status["s3"]["configured"], status["s3"]["source"]), (True, "secrets"))

    def test_missing_pgpass_file_and_aws_chain(self):
        Config._instance.secrets = {"pgpass_file": os.path.join(tempfile.gettempdir(), "no-such-pgpass")}
        with patch.object(settingsService, "_aws_credential_chain", return_value=True):
            status = self._status()

        self.assertFalse(status["postgres"]["configured"])
        self.assertEqual((status["s3"]["configured"], status["s3"]["source"]), (True, "aws"))

    def test_never_returns_values(self):
        Config._instance.secrets = {"openai_api_key": "sk-secret-value", "mapbox_access_token": "pk.secret-value"}

        self.assertNotIn("secret-value", repr(settings_controller.status()))


if __name__ == "__main__":
    unittest.main()


class PreferencesTest(unittest.TestCase):
    def setUp(self):
        self.previous_config = Config._instance
        config = Config.__new__(Config)
        config.config = {"aiModel": "gpt-configured"}
        config.secrets = {"openai_api_key": "sk-test"}
        Config._instance = config
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.previous_db_config = databaseService._config
        databaseService._config = {"databasesFolder": self.folder.name, "downloadFolder": self.folder.name}
        databaseService.set_current_user("test_user")

    def tearDown(self):
        Config._instance = self.previous_config
        databaseService._config = self.previous_db_config
        databaseService.set_current_user(None)

    def test_preferences_are_saved_per_user(self):
        self.assertEqual(settings_controller.getPreferences(), {})

        settings_controller.updatePreferences({"locale": "es", "aiModel": "gpt-5.4"})
        saved = settings_controller.updatePreferences({"voiceProvider": "openai"})

        self.assertEqual(saved, {"locale": "es", "aiModel": "gpt-5.4", "voiceProvider": "openai"})
        self.assertEqual(settings_controller.getPreferences(), saved)
        self.assertTrue(os.path.exists(os.path.join(self.folder.name, "test_user", "preferences.json")))
        databaseService.set_current_user("other_user")
        self.assertEqual(settings_controller.getPreferences(), {})

    def test_invalid_preferences_are_refused(self):
        for changes in ({"locale": "fr"}, {"voiceProvider": "siri"}, {"aiModel": "../../x y"}, {"theme": "dark"}):
            self.assertEqual(settings_controller.updatePreferences(changes).status_code, 400, changes)
        self.assertEqual(settings_controller.getPreferences(), {})

    def test_the_users_model_is_used_by_the_assistant(self):
        self.assertEqual(chatGPTService._chat_model(), "gpt-configured")

        settings_controller.updatePreferences({"aiModel": "gpt-5.4"})
        self.assertEqual(chatGPTService._chat_model(), "gpt-5.4")

        settings_controller.updatePreferences({"aiModel": None})
        self.assertEqual(chatGPTService._chat_model(), "gpt-configured")

    def test_models_lists_the_text_models_of_the_key(self):
        ids = ["gpt-5.4-mini", "gpt-4o-mini-tts", "gpt-5.4", "gpt-5-2025-08-07", "o3", "dall-e-3",
               "gpt-4o-realtime-preview", "text-embedding-3-small", "gpt-4o-mini-transcribe"]

        class FakeModels:
            def __init__(self, api_key):
                self.models = SimpleNamespace(list=lambda: [SimpleNamespace(id=i) for i in ids])

        settings_controller.updatePreferences({"aiModel": "gpt-5.4"})
        with patch.object(chatGPTService, "OpenAI", FakeModels):
            models = settings_controller.models()

        self.assertEqual(models, {"current": "gpt-5.4", "configured": "gpt-configured", "error": None,
                                  "models": ["gpt-configured", "o3", "gpt-5.4-mini", "gpt-5.4"]})

    def test_models_without_a_key(self):
        Config._instance.secrets = {}

        models = settings_controller.models()

        self.assertEqual(models["models"], ["gpt-configured"])
        self.assertIn("openai_api_key", models["error"])
