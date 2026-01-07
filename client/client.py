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


def join_room(sock, room_name: str):
    """
    Envoie une demande pour rejoindre un salon.
    
    Args:
        sock: La socket connectée au serveur
        room_name: Le nom du salon à rejoindre
    
    Returns:
        tuple: (msg_type, payload) — la réponse du serveur
    """
    
    # Encodage et envoi du message JOIN
    payload = pack_string(room_name)
    sock.send(pack_message(JOIN, payload))
    
    # Lecture de la réponse du serveur
    header = sock.recv(5)
    msg_type, length = unpack_header(header)
    payload = sock.recv(length)
    
    return msg_type, payload


def leave_room(sock):
    """
    Envoie une demande pour quitter le salon actuel.
    
    Args:
        sock: La socket connectée au serveur
    """
    
    # LEAVE n'a pas de payload
    sock.send(pack_message(LEAVE))
    
    # LEAVE n'a pas de réponse selon le protocole
