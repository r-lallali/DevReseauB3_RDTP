import socket
from common.protocol import *


def login(sock, pseudo: str):
    """
    Envoie une demande de connexion au serveur et retourne sa réponse.
    """

    # Encodage et envoi du message LOGIN
    payload = pack_string(pseudo)
    sock.send(pack_message(LOGIN, payload))

    # Lecture de la réponse du serveur
    header = sock.recv(5)
    msg_type, length = unpack_header(header)
    payload = sock.recv(length)

    return msg_type, payload
