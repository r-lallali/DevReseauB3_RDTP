"""
test_login.py

Tests unitaires de connexion (LOGIN).

Les tests utilisent socket.socketpair pour simuler une communication
client / serveur sans réseau réel.
"""

import unittest
import socket
import threading
from server.server import ChatServer
from client.client import login
from common.protocol import *


class TestLogin(unittest.TestCase):

    def setUp(self):
        # Création du serveur et d'une paire de sockets connectées
        self.server = ChatServer()
        self.srv_sock, self.cli_sock = socket.socketpair()

    def tearDown(self):
        # Fermeture des sockets après chaque test
        self.srv_sock.close()
        self.cli_sock.close()

    def _run_server(self):
        """Lance le serveur dans un thread."""
        thread = threading.Thread(
            target=self.server.handle_client,
            args=(self.srv_sock,)
        )
        thread.start()
        return thread


    def test_login_ok(self):
        thread = self._run_server()

        msg_type, _ = login(self.cli_sock, "Donald")
        self.cli_sock.close()   # Provoque la sortie de la boucle serveur
        thread.join()

        self.assertEqual(msg_type, LOGIN_OK)

    def test_login_empty_pseudo(self):
        thread = self._run_server()

        msg_type, _ = login(self.cli_sock, "")
        self.cli_sock.close()
        thread.join()

        self.assertEqual(msg_type, LOGIN_ERR)

    def test_login_duplicate_pseudo(self):
        self.server.clients["Bob"] = object()

        thread = self._run_server()

        msg_type, _ = login(self.cli_sock, "Bob")
        self.cli_sock.close()
        thread.join()

        self.assertEqual(msg_type, LOGIN_ERR)

    def test_action_without_login(self):
        thread = self._run_server()

        # Envoi d'un message interdit avant LOGIN
        self.cli_sock.send(pack_message(0x99))

        header = self.cli_sock.recv(5)
        msg_type, _ = unpack_header(header)

        self.cli_sock.close()
        thread.join()

        self.assertEqual(msg_type, LOGIN_ERR)


if __name__ == "__main__":
    unittest.main()
