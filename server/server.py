import socket
from common.protocol import *


class ClientContext:
    """
    Représente l'état d'un client connecté.
    """

    def __init__(self, sock):
        self.sock = sock
        self.pseudo = None
        self.state = STATE_CONNECTED
        self.room = None

    def is_authenticated(self):
        return self.state in (STATE_AUTHENTICATED, STATE_IN_ROOM)

    def is_in_room(self):
        return self.state == STATE_IN_ROOM


class ChatServer:
    """
    Serveur de chat gérant les connexions des clients.
    """

    def __init__(self):
        self.clients = {}

    def handle_client(self, sock):
        """
        Traite un client tant que la connexion TCP est ouverte.
        """

        client = ClientContext(sock)

        try:
            while True:
                # Lecture de l'en-tête
                header = sock.recv(5)
                if not header:
                    break

                msg_type, length = unpack_header(header)
                payload = sock.recv(length)

                # --------------------
                # Phase LOGIN
                # --------------------
                if client.state == STATE_CONNECTED:
                    if msg_type != LOGIN:
                        sock.send(pack_message(
                            LOGIN_ERR,
                            pack_string("Login requis")
                        ))
                        break

                    pseudo = unpack_string(payload)

                    if not pseudo or len(pseudo) > MAX_PSEUDO_LEN:
                        sock.send(pack_message(
                            LOGIN_ERR,
                            pack_string("Pseudo invalide")
                        ))
                        break

                    if pseudo in self.clients:
                        sock.send(pack_message(
                            LOGIN_ERR,
                            pack_string("Pseudo déjà utilisé")
                        ))
                        break

                    client.pseudo = pseudo
                    client.state = STATE_AUTHENTICATED
                    self.clients[pseudo] = client

                    sock.send(pack_message(LOGIN_OK))
                    continue

                # --------------------
                # États suivants (non implémentés)
                # --------------------
                sock.send(pack_message(
                    GENERIC_ERR,
                    pack_string("Action non supportée")
                ))

        finally:
            # Nettoyage lors de la déconnexion
            if client.pseudo in self.clients:
                del self.clients[client.pseudo]

            sock.close()
