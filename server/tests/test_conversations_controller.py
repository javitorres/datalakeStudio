import json
import os
import tempfile
import unittest
from unittest.mock import patch

from model.ConversationDTO import ConversationDTO, ConversationTitleDTO
from routes import conversations_controller
from services import conversationsService, databaseService

TEST_USER = "test_user"
MESSAGES = [{"role": "user", "text": "How many trips?"},
            {"role": "assistant", "sql": "SELECT count(*) FROM trips", "text": "**3** trips"}]


class ConversationsControllerTest(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.previous_config = databaseService._config
        databaseService._config = {"databasesFolder": self.folder.name, "downloadFolder": self.folder.name}
        databaseService.set_current_user(TEST_USER)
        database = patch.object(databaseService, "get_current_database_name", return_value="taxis")
        database.start()
        self.addCleanup(database.stop)

    def tearDown(self):
        databaseService._config = self.previous_config

    @staticmethod
    def _json(response):
        return json.loads(response.body.decode("utf-8"))

    def _save(self, conversation_id, title="Trips", messages=MESSAGES):
        return conversations_controller.saveConversation(conversation_id, ConversationDTO(title=title, messages=messages))

    def test_save_list_and_get(self):
        saved = self._save("conv-aaaa1")
        self._save("conv-bbbb2", title="Zones")

        self.assertEqual((saved["title"], saved["database"]), ("Trips", "taxis"))
        self.assertNotIn("messages", saved)
        self.assertEqual([c["title"] for c in conversations_controller.listConversations()], ["Zones", "Trips"])
        conversation = conversations_controller.getConversation("conv-aaaa1")
        self.assertEqual(conversation["messages"], MESSAGES)
        self.assertTrue(os.path.exists(os.path.join(self.folder.name, TEST_USER, "conversations", "conv-aaaa1.json")))

    def test_saving_again_keeps_the_creation_date(self):
        first = self._save("conv-aaaa1")
        second = self._save("conv-aaaa1", messages=MESSAGES * 2)

        self.assertEqual(second["created"], first["created"])
        self.assertGreaterEqual(second["updated"], first["updated"])
        self.assertEqual(len(conversations_controller.getConversation("conv-aaaa1")["messages"]), 4)

    def test_rename_and_delete(self):
        self._save("conv-aaaa1")

        renamed = conversations_controller.renameConversation("conv-aaaa1", ConversationTitleDTO(title="  Mis viajes "))
        self.assertEqual(renamed["title"], "Mis viajes")
        self.assertEqual(conversations_controller.getConversation("conv-aaaa1")["messages"], MESSAGES)

        self.assertEqual(conversations_controller.deleteConversation("conv-aaaa1"), {"status": "ok"})
        self.assertEqual(conversations_controller.listConversations(), [])
        self.assertEqual(conversations_controller.deleteConversation("conv-aaaa1").status_code, 404)
        self.assertEqual(conversations_controller.getConversation("conv-aaaa1").status_code, 404)

    def test_ids_cannot_reach_other_files(self):
        for bad in ("../../etc", "a/b/c/d/e", "short", ""):
            response = conversations_controller.getConversation(bad)
            self.assertEqual(response.status_code, 400, bad)
        self.assertEqual(self._save("../secrets-x").status_code, 400)

    def test_only_the_most_recent_are_kept(self):
        with patch.object(conversationsService, "MAX_CONVERSATIONS", 2):
            for i in range(3):
                self._save(f"conv-0000{i}", title=str(i))

        self.assertEqual([c["title"] for c in conversations_controller.listConversations()], ["2", "1"])

    def test_each_user_has_their_own(self):
        self._save("conv-aaaa1")
        databaseService.set_current_user("other_user")

        self.assertEqual(conversations_controller.listConversations(), [])


if __name__ == "__main__":
    unittest.main()
