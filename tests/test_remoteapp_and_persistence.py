import configparser
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.servidores import ServidorManager


class FakeCrypto:
    def __init__(self, unlocked=True):
        self.unlocked = unlocked

    def is_unlocked(self):
        return self.unlocked

    def decrypt_password(self, value, context):
        return "secret"

    def encrypt_password(self, value, context):
        return f"encrypted-{context}"


class RemoteAppPersistenceTests(unittest.TestCase):
    def manager(self, path, unlocked=True):
        manager = ServidorManager.__new__(ServidorManager)
        manager.ini_path = Path(path)
        manager.config = configparser.ConfigParser()
        manager.crypto_manager = FakeCrypto(unlocked)
        manager.config.read(path, encoding="utf-8")
        return manager

    def write(self, path, values):
        config = configparser.ConfigParser()
        for section, data in values.items():
            config[section] = data
        with open(path, "w", encoding="utf-8") as stream:
            config.write(stream)

    def test_remoteapps_are_not_servers_and_follow_rename_and_delete(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "servidores.ini"
            self.write(path, {"Servidor A": {"ip": "host:3389", "usuario": "user"}})
            manager = self.manager(path)

            app_id = manager.salvar_remoteapp("Servidor A", "Easy ERP", "||easyerp")
            self.assertEqual(["Servidor A"], manager.listar_servidores())
            self.assertEqual("||easyerp", manager.listar_remoteapps("Servidor A")[0]["programa"])

            self.assertTrue(manager.renomear_servidor("Servidor A", "Servidor B"))
            self.assertEqual("Easy ERP", manager.listar_remoteapps("Servidor B")[0]["nome"])
            self.assertEqual([], manager.listar_remoteapps("Servidor A"))

            self.assertTrue(manager.remover_servidor("Servidor B"))
            self.assertEqual([], manager.listar_remoteapps("Servidor B"))
            self.assertNotIn(f"RemoteApp:Servidor B:{app_id}", manager.config)

    def test_rename_with_locked_password_is_rejected_without_data_loss(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "servidores.ini"
            self.write(path, {
                "Servidor A": {
                    "ip": "host:3389",
                    "usuario": "user",
                    "senha_encrypted": "ciphertext",
                }
            })
            manager = self.manager(path, unlocked=False)
            manager.salvar_remoteapp("Servidor A", "App", "||app")

            self.assertFalse(manager.renomear_servidor("Servidor A", "Servidor B"))
            manager.recarregar()
            self.assertIn("Servidor A", manager.config)
            self.assertEqual("ciphertext", manager.config["Servidor A"]["senha_encrypted"])
            self.assertNotIn("Servidor B", manager.config)
            self.assertEqual("App", manager.listar_remoteapps("Servidor A")[0]["nome"])


if __name__ == "__main__":
    unittest.main()
