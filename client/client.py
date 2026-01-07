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

def listen_server(sock, callback=None):
    """
    Écoute en continu les messages envoyés par le serveur.
    
    Args:
        sock: La socket connectée au serveur
        callback: Fonction optionnelle appelée pour chaque message reçu
                  callback(msg_type, payload)
    """
    try:
        while True:
            # Lecture de l'en-tête
            header = sock.recv(5)
            if not header:
                print("Connexion fermée par le serveur")
                break
            
            msg_type, length = unpack_header(header)
            payload = sock.recv(length) if length > 0 else b""
            
            # Traiter le message selon son type
            if msg_type == USER_CONNECTED:
                pseudo = unpack_string(payload)
                print(f"[NOTIFICATION] {pseudo} vient de se connecter")
            elif msg_type == PING:
                # Répondre automatiquement aux PING
                sock.send(pack_message(PONG))
            elif msg_type == ERROR:
                error_msg = unpack_string(payload)
                print(f"[ERREUR] {error_msg}")
            else:
                print(f"[MESSAGE] Type {msg_type} reçu")
            
            # Appeler le callback si fourni
            if callback:
                callback(msg_type, payload)
                
    except Exception as e:
        print(f"Erreur lors de l'écoute: {e}")
    finally:
        sock.close()
