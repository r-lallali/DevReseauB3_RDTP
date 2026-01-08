"""
test_room.py

Tests unitaires pour les salons (JOIN / LEAVE).

Les tests utilisent socket.socketpair pour simuler une communication
client / serveur sans réseau réel.
"""

import unittest
import socket
from server.server import ChatServer, ClientContext
from client.client import join_room, leave_room
from common.protocol import *


class TestRoom(unittest.TestCase):

    def setUp(self):
        """Préparation avant chaque test."""
        self.server = ChatServer()
        self.srv_sock, self.cli_sock = socket.socketpair()
        
        # Créer un client déjà authentifié (on simule qu'il a fait LOGIN)
        self.client = ClientContext(self.srv_sock)
        self.client.pseudo = "Alice"
        self.client.state = STATE_AUTHENTICATED
        self.server.clients["Alice"] = self.client

    def tearDown(self):
        """Nettoyage après chaque test."""
        self.srv_sock.close()
        self.cli_sock.close()


    def test_join_room_ok(self):
        """Un client authentifié peut rejoindre un salon."""
        
        # Le client envoie JOIN
        import threading
        thread = threading.Thread(
            target=self.server.handle_join,
            args=(self.client, pack_string("général"))
        )
        thread.start()
        thread.join()
        
        # Lire la réponse
        header = self.cli_sock.recv(5)
        msg_type, _ = unpack_header(header)
        
        # Vérifications
        self.assertEqual(msg_type, JOIN_OK)
        self.assertEqual(self.client.state, STATE_IN_ROOM)
        self.assertEqual(self.client.room, "général")
        self.assertIn("Alice", self.server.rooms["général"])


    def test_join_creates_room(self):
        """Rejoindre un salon inexistant le crée automatiquement."""
        
        self.server.handle_join(self.client, pack_string("nouveau_salon"))
        
        # Le salon doit exister maintenant
        self.assertIn("nouveau_salon", self.server.rooms)


    def test_join_switches_room(self):
        """Rejoindre un autre salon quitte l'ancien automatiquement."""
        
        # D'abord rejoindre "salon1"
        self.server.handle_join(self.client, pack_string("salon1"))
        self.cli_sock.recv(100)  # Vider le buffer (JOIN_OK)
        
        # Puis rejoindre "salon2"
        self.server.handle_join(self.client, pack_string("salon2"))
        
        # Vérifications
        self.assertEqual(self.client.room, "salon2")
        self.assertNotIn("Alice", self.server.rooms.get("salon1", set()))
        self.assertIn("Alice", self.server.rooms["salon2"])


    def test_leave_room_ok(self):
        """Un client dans un salon peut le quitter."""
        
        # D'abord rejoindre un salon
        self.server.handle_join(self.client, pack_string("général"))
        self.cli_sock.recv(100)  # Vider le buffer
        
        # Puis quitter
        self.server.handle_leave(self.client)
        
        # Vérifications
        self.assertEqual(self.client.state, STATE_AUTHENTICATED)
        self.assertIsNone(self.client.room)


    def test_leave_when_not_in_room(self):
        """Quitter sans être dans un salon renvoie une erreur."""
        
        # Le client est AUTHENTIFIÉ mais pas dans un salon
        self.server.handle_leave(self.client)
        
        # Lire la réponse (devrait être ERROR)
        header = self.cli_sock.recv(5)
        msg_type, _ = unpack_header(header)
        
        self.assertEqual(msg_type, ERROR)


    def test_empty_room_is_deleted(self):
        """Un salon vide est supprimé automatiquement."""
        
        # Rejoindre puis quitter
        self.server.handle_join(self.client, pack_string("temp_room"))
        self.cli_sock.recv(100)  # Vider le buffer
        
        self.server.handle_leave(self.client)
        
        # Le salon ne doit plus exister
        self.assertNotIn("temp_room", self.server.rooms)


if __name__ == "__main__":
    unittest.main()
