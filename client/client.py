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


def send_message(sock, message: str):
    """
    Envoie un message dans le salon actuel.
    
    Args:
        sock: La socket connectée au serveur
        message: Le texte du message à envoyer
    """
    
    payload = pack_string(message)
    sock.send(pack_message(MSG, payload))
    
    # Pas de réponse directe — le message sera broadcasté à tous


def receive_broadcast(sock):
    """
    Reçoit un message MSG_BROADCAST du serveur.
    
    Returns:
        tuple: (pseudo, message) — l'expéditeur et son message
    """
    
    # Lire l'en-tête
    header = sock.recv(5)
    msg_type, length = unpack_header(header)
    
    # Lire le payload
    payload = sock.recv(length)
    
    if msg_type != MSG_BROADCAST:
        # Ce n'est pas un broadcast, retourner le type pour traitement
        return None, None, msg_type, payload
    
    # Décoder le payload : [pseudo][message]
    pseudo = unpack_string(payload)
    # Calculer où commence le message (après le pseudo)
    pseudo_len = 2 + len(pseudo.encode('utf-8'))
    message = unpack_string(payload[pseudo_len:])
    
    return pseudo, message
