"""
test_login.py

Tests unitaires de connexion (LOGIN).

Les tests utilisent socket.socketpair pour simuler une communication
client / serveur sans réseau réel.
"""

import unittest
import socket
import threading
import time
from server.server import ChatServer
from client.client import login
from common.protocol import *

# Constantes pour les tests
TEST_THREAD_JOIN_TIMEOUT = 1.0 # temps d'attente pour joindre les threads


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

    def test_user_connected_notification(self):
        """
        Teste qu'un client reçoit une notification quand un autre client se connecte.
        """
        # Créer une deuxième paire de sockets pour le second client
        srv_sock2, cli_sock2 = socket.socketpair()
        
        # Configurer un timeout pour éviter les blocages
        self.cli_sock.settimeout(SOCKET_TIMEOUT)
        cli_sock2.settimeout(SOCKET_TIMEOUT)
        
        try:
            # Connecter le premier client (Donald)
            thread1 = self._run_server()
            msg_type, _ = login(self.cli_sock, "Donald")
            self.assertEqual(msg_type, LOGIN_OK)
            
            # Laisser un peu de temps pour que le serveur soit prêt
            time.sleep(0.1)
            
            # Connecter le deuxième client (Alice) dans un thread séparé
            thread2 = threading.Thread(
                target=self.server.handle_client,
                args=(srv_sock2,)
            )
            thread2.start()
            
            msg_type, _ = login(cli_sock2, "Alice")
            self.assertEqual(msg_type, LOGIN_OK)
            
            # Le premier client (Donald) devrait recevoir une notification USER_CONNECTED
            header = self.cli_sock.recv(5)
            msg_type, length = unpack_header(header)
            payload = self.cli_sock.recv(length)
            
            self.assertEqual(msg_type, USER_CONNECTED)
            pseudo_notified = unpack_string(payload)
            self.assertEqual(pseudo_notified, "Alice")
            
        finally:
            # Fermeture propre
            self.cli_sock.close()
            cli_sock2.close()
            srv_sock2.close()
            thread1.join(timeout=TEST_THREAD_JOIN_TIMEOUT)
            thread2.join(timeout=TEST_THREAD_JOIN_TIMEOUT)


if __name__ == "__main__":
    unittest.main()
