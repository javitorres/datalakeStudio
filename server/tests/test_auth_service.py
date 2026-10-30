import asyncio
import tempfile
import unittest
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

import auth
from services import authService, mailService


class AuthServiceTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        mailService.init({})
        authService.init({"databasesFolder": self.tmp.name}, {"jwt_secret": "test-secret-" + "x" * 32})

    def tearDown(self):
        self.tmp.cleanup()

    @staticmethod
    def _bearer(username):
        return HTTPAuthorizationCredentials(scheme="Bearer", credentials=authService.create_token(username))

    def test_register_rejects_names_that_are_not_a_plain_folder_name(self):
        for name in ["jtorres@madiva.com/.", "../other", "a/b", ".hidden", "default"]:
            user, _ = authService.register(name, "secret1")
            self.assertIsNone(user, name)

        self.assertEqual(authService.register("Ana.Garcia@Example.com", "secret1"), ("ana.garcia@example.com", "ok"))

    def test_tokens_naming_an_invalid_user_are_rejected(self):
        with patch.object(auth, "is_auth_enabled", return_value=True):
            with self.assertRaises(HTTPException) as error:
                asyncio.run(auth.get_current_user(self._bearer("jtorres@madiva.com/.")))
            self.assertEqual(error.exception.status_code, 401)

            self.assertEqual(asyncio.run(auth.get_current_user(self._bearer("ana@example.com"))), "ana@example.com")


if __name__ == '__main__':
    unittest.main()
