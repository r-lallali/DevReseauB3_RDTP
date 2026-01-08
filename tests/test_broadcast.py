"""
test_broadcast.py

Tests unitaires pour la fonctionnalité de diffusion (User Story 8).
Vérifie que les autres membres d'un salon reçoivent une notification quand quelqu'un rejoint.
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
import socket
from server.server import ChatServer, ClientContext
from common.protocol import *

class TestBroadcast(unittest.TestCase):

    def setUp(self):
        """
        Préparation:
        - Un serveur
        - Client A (Alice)
        - Client B (Bob)
        """
        self.server = ChatServer()
        
        # Setup Alice
        self.srv_sock_a, self.cli_sock_a = socket.socketpair()
        self.ctx_a = ClientContext(self.srv_sock_a)
        self.ctx_a.pseudo = "Alice"
        self.ctx_a.state = STATE_AUTHENTICATED
        self.server.clients["Alice"] = self.ctx_a
        
        # Setup Bob
        self.srv_sock_b, self.cli_sock_b = socket.socketpair()
        self.ctx_b = ClientContext(self.srv_sock_b)
        self.ctx_b.pseudo = "Bob"
        self.ctx_b.state = STATE_AUTHENTICATED
        self.server.clients["Bob"] = self.ctx_b

    def tearDown(self):
        self.srv_sock_a.close()
        self.cli_sock_a.close()
        self.srv_sock_b.close()
        self.cli_sock_b.close()

    def test_join_broadcasts_notification(self):
        """
        US8: Quand Bob rejoint le salon où est Alice, Alice reçoit une notification.
        """
        room_name = "Dev"
        
        # 1. Alice rejoint le salon
        self.server.handle_join(self.ctx_a, pack_string(room_name))
        
        # Vider le buffer d'Alice (elle reçoit JOIN_OK)
        header = self.cli_sock_a.recv(5)
        mt, _ = unpack_header(header)
        self.assertEqual(mt, JOIN_OK)
        
        # 2. Bob rejoint le même salon
        self.server.handle_join(self.ctx_b, pack_string(room_name))
        
        # Vider le buffer de Bob (il reçoit JOIN_OK)
        header_b = self.cli_sock_b.recv(5)
        mt_b, _ = unpack_header(header_b)
        self.assertEqual(mt_b, JOIN_OK)
        
        # 3. VERIFICATION : Alice doit avoir reçu un BROADCAST
        # Format MSG_BROADCAST : [LEN_PSEUDO][PSEUDO][LEN_MSG][MSG]
        # Sender devrait être "Serveur" (selon implémentation étape précédente)
        
        # Test non-bloquant sur le socket d'Alice
        self.cli_sock_a.settimeout(1.0)
        try:
            header_a = self.cli_sock_a.recv(5)
            mt_a, len_a = unpack_header(header_a)
            
            self.assertEqual(mt_a, MSG_BROADCAST, "Alice aurait dû recevoir un MSG_BROADCAST")
            
            payload_a = self.cli_sock_a.recv(len_a)
            
            # Décodage payload broadcast
            sender_pseudo = unpack_string(payload_a)
            # Puis le message se trouve après le premier string
            # Le premier string prend 2 bytes (len) + len bytes
            offset = 2 + len(sender_pseudo.encode('utf-8'))
            message = unpack_string(payload_a[offset:])
            
            self.assertEqual(sender_pseudo, "Serveur")
            self.assertEqual(message, "Bob s'est connecté")
            
        except socket.timeout:
            self.fail("Alice n'a pas reçu de notification (timeout)")

    def test_broadcast_excludes_sender(self):
        """
        US8: Bob ne doit PAS recevoir la notification de sa propre connexion.
        """
        room_name = "Dev"
        self.server.handle_join(self.ctx_a, pack_string(room_name))
        self.cli_sock_a.recv(1024) # Alice clear

        # Bob rejoint
        self.server.handle_join(self.ctx_b, pack_string(room_name))
        
        # Bob lit son JOIN_OK
        header = self.cli_sock_b.recv(5)
        mt, _ = unpack_header(header)
        self.assertEqual(mt, JOIN_OK)
        
        # Bob essaie de lire SUITE ... il ne devrait RIEN y avoir
        self.cli_sock_b.settimeout(0.5)
        try:
            extra = self.cli_sock_b.recv(5)
            # Si on reçoit quelque chose, c'est un échec (sauf si c'est un PING heartbeat? mais on ne teste pas ça ici)
            msg_type, _ = unpack_header(extra)
            self.fail(f"Bob a reçu un message inattendu: {msg_type}")
        except socket.timeout:
            # OK, pas de message reçu
            pass

if __name__ == "__main__":
    unittest.main()
