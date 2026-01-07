"""
test_login.py

Tests unitaires de connexion (LOGIN).

Les tests utilisent socket.socketpair pour simuler une communication
client / serveur sans réseau réel.
"""

import unittest
import socket
import threading
from .server import ChatServer
from .client import login
from .protocol import *


class TestLogin(unittest.TestCase):

    def setUp(self):
        # Création du serveur et d'une paire de sockets connectées
        self.server = ChatServer()
        self.srv_sock, self.cli_sock = socket.socketpair()

    def tearDown(self):
        # Fermeture des sockets après chaque test
        self.srv_sock.close()
        self.cli_sock.close()


    def test_login_ok(self):
        # Connexion avec un pseudo valide
        thread = threading.Thread(target=self.server.handle_client, args=(self.srv_sock,))
        thread.start()
        msg_type, _ = login(self.cli_sock, "Donald")
        thread.join()

        self.assertEqual(msg_type, LOGIN_OK)

    def test_login_empty_pseudo(self):
        # Connexion avec un pseudo vide
        thread = threading.Thread(target=self.server.handle_client, args=(self.srv_sock,))
        thread.start()
        msg_type, _ = login(self.cli_sock, "")
        thread.join()

        self.assertEqual(msg_type, LOGIN_ERR)

    def test_login_duplicate_pseudo(self):
        # Connexion avec un pseudo déjà utilisé
        self.server.clients["Bob"] = object()

        thread = threading.Thread(target=self.server.handle_client, args=(self.srv_sock,))
        thread.start()
        msg_type, _ = login(self.cli_sock, "Bob")
        thread.join()

        self.assertEqual(msg_type, LOGIN_ERR)

    def test_action_without_login(self):
        # Envoi d'un message non autorisé avant le LOGIN
        thread = threading.Thread(target=self.server.handle_client, args=(self.srv_sock,))
        thread.start()
        self.cli_sock.send(pack_message(0x99))

        header = self.cli_sock.recv(5)
        msg_type, _ = unpack_header(header)
        thread.join()

        self.assertEqual(msg_type, LOGIN_ERR)


if __name__ == "__main__":
    unittest.main()
