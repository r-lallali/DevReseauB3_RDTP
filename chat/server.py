import socket
from .protocol import *


class ClientContext:
    """
    Représente l'état d'un client connecté.
    """

    def __init__(self, sock):
        self.sock = sock
        self.pseudo = None
        self.authenticated = False


class ChatServer:
    """
    Serveur de chat gérant les connexions des clients.
    """

    def __init__(self):
        # Dictionnaire des clients connectés, identifiés par pseudo
        self.clients = {}

    def handle_client(self, sock):
        """
        Traite un client pour une seule requête.
        """

        client = ClientContext(sock)

        # Lecture de l'en-tête du message (type + longueur)
        header = sock.recv(5)
        msg_type, length = unpack_header(header)

        # Lecture des données associées au message
        payload = sock.recv(length)

        # Seul le message LOGIN est accepté
        if msg_type != LOGIN:
            sock.send(pack_message(LOGIN_ERR, pack_string("Login requis")))
            sock.close()
            return

        # Extraction du pseudo depuis les données reçues
        pseudo = unpack_string(payload)

        # Vérification du pseudo
        if not pseudo or len(pseudo) > MAX_PSEUDO_LEN:
            sock.send(pack_message(LOGIN_ERR, pack_string("Pseudo invalide")))
            sock.close()
            return

        # Vérification de l'unicité du pseudo
        if pseudo in self.clients:
            sock.send(pack_message(LOGIN_ERR, pack_string("Pseudo déjà utilisé")))
            sock.close()
            return

        # Enregistrement du client
        client.pseudo = pseudo
        client.authenticated = True
        self.clients[pseudo] = client

        # Confirmation de la connexion
        sock.send(pack_message(LOGIN_OK))
