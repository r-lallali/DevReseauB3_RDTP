"""
test_message.py

Tests unitaires pour l'envoi et la diffusion de messages (MSG / MSG_BROADCAST).

Les tests utilisent socket.socketpair pour simuler une communication
client / serveur sans réseau réel.
"""

import unittest
import socket
from server.server import ChatServer, ClientContext
from client.client import send_message
from common.protocol import *


class TestMessage(unittest.TestCase):

    def setUp(self):
        """Préparation avant chaque test."""
        self.server = ChatServer()
        
        # Créer deux clients dans le même salon
        self.srv_sock1, self.cli_sock1 = socket.socketpair()
        self.srv_sock2, self.cli_sock2 = socket.socketpair()
        
        # Client 1 : Alice dans le salon "général"
        self.alice = ClientContext(self.srv_sock1)
        self.alice.pseudo = "Alice"
        self.alice.state = STATE_IN_ROOM
        self.alice.room = "général"
        self.server.clients["Alice"] = self.alice
        
        # Client 2 : Bob dans le salon "général"
        self.bob = ClientContext(self.srv_sock2)
        self.bob.pseudo = "Bob"
        self.bob.state = STATE_IN_ROOM
        self.bob.room = "général"
        self.server.clients["Bob"] = self.bob
        
        # Créer le salon avec les deux clients
        self.server.rooms["général"] = {"Alice", "Bob"}

    def tearDown(self):
        """Nettoyage après chaque test."""
        self.srv_sock1.close()
        self.cli_sock1.close()
        self.srv_sock2.close()
        self.cli_sock2.close()


    def test_send_message_ok(self):
        """Un client dans un salon peut envoyer un message."""
        
        # Alice envoie un message
        self.server.handle_msg(self.alice, pack_string("Bonjour tout le monde !"))
        
        # Alice et Bob doivent recevoir le broadcast
        # Vérifier pour Alice
        header = self.cli_sock1.recv(5)
        msg_type, length = unpack_header(header)
        self.assertEqual(msg_type, MSG_BROADCAST)
        
        # Vérifier pour Bob
        header = self.cli_sock2.recv(5)
        msg_type, length = unpack_header(header)
        self.assertEqual(msg_type, MSG_BROADCAST)


    def test_broadcast_contains_pseudo_and_message(self):
        """Le broadcast contient le pseudo de l'expéditeur et le message."""
        
        # Alice envoie un message
        self.server.handle_msg(self.alice, pack_string("Hello !"))
        
        # Bob reçoit le broadcast
        header = self.cli_sock2.recv(5)
        msg_type, length = unpack_header(header)
        payload = self.cli_sock2.recv(length)
        
        # Décoder le payload
        pseudo = unpack_string(payload)
        pseudo_len = 2 + len(pseudo.encode('utf-8'))
        message = unpack_string(payload[pseudo_len:])
        
        self.assertEqual(pseudo, "Alice")
        self.assertEqual(message, "Hello !")


    def test_message_not_in_room(self):
        """Un client hors salon ne peut pas envoyer de message."""
        
        # Charlie est authentifié mais pas dans un salon
        srv_sock3, cli_sock3 = socket.socketpair()
        charlie = ClientContext(srv_sock3)
        charlie.pseudo = "Charlie"
        charlie.state = STATE_AUTHENTICATED  # Pas dans un salon !
        charlie.room = None
        self.server.clients["Charlie"] = charlie
        
        # Charlie essaie d'envoyer un message
        self.server.handle_msg(charlie, pack_string("Test"))
        
        # Charlie doit recevoir une erreur
        header = cli_sock3.recv(5)
        msg_type, _ = unpack_header(header)
        
        self.assertEqual(msg_type, ERROR)
        
        cli_sock3.close()
        srv_sock3.close()


    def test_empty_message_rejected(self):
        """Un message vide est rejeté."""
        
        self.server.handle_msg(self.alice, pack_string(""))
        
        # Alice doit recevoir une erreur
        header = self.cli_sock1.recv(5)
        msg_type, _ = unpack_header(header)
        
        self.assertEqual(msg_type, ERROR)


    def test_message_too_long_rejected(self):
        """Un message trop long est rejeté."""
        
        # Créer un message de plus de 1024 caractères
        long_message = "A" * 1025
        
        self.server.handle_msg(self.alice, pack_string(long_message))
        
        # Alice doit recevoir une erreur
        header = self.cli_sock1.recv(5)
        msg_type, _ = unpack_header(header)
        
        self.assertEqual(msg_type, ERROR)


    def test_broadcast_only_to_same_room(self):
        """Le broadcast n'est envoyé qu'aux clients du même salon."""
        
        # Créer un 3ème client dans un AUTRE salon
        srv_sock3, cli_sock3 = socket.socketpair()
        charlie = ClientContext(srv_sock3)
        charlie.pseudo = "Charlie"
        charlie.state = STATE_IN_ROOM
        charlie.room = "autre_salon"
        self.server.clients["Charlie"] = charlie
        self.server.rooms["autre_salon"] = {"Charlie"}
        
        # Alice envoie un message dans "général"
        self.server.handle_msg(self.alice, pack_string("Message privé"))
        
        # Alice et Bob reçoivent (même salon)
        self.cli_sock1.recv(100)  # Alice
        self.cli_sock2.recv(100)  # Bob
        
        # Charlie ne doit RIEN recevoir
        cli_sock3.setblocking(False)
        try:
            data = cli_sock3.recv(1)
            self.fail("Charlie ne devrait rien recevoir !")
        except BlockingIOError:
            pass  # Correct, rien à recevoir
        
        cli_sock3.close()
        srv_sock3.close()


if __name__ == "__main__":
    unittest.main()
