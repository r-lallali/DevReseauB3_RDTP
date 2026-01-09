"""
Client de chat interactif.

Usage:
    python3 -m client.client_main

Commandes disponibles:
    /join <salon>  - Rejoindre un salon
    /leave         - Quitter le salon
    /quit          - Quitter le client
    <message>      - Envoyer un message
"""

import socket
import threading
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from common.protocol import *

# Configuration
SERVER_IP = "127.0.0.1"
SERVER_PORT = 5555


def receive_messages(sock):
    """
    Thread qui écoute les messages du serveur en continu.
    """
    while True:
        try:
            header = sock.recv(5)
            if not header:
                print("\n[Déconnecté du serveur]")
                break
            
            msg_type, length = unpack_header(header)
            payload = sock.recv(length) if length > 0 else b""
            
            if msg_type == MSG_BROADCAST:
                # Décoder pseudo + message
                pseudo = unpack_string(payload)
                pseudo_len = 2 + len(pseudo.encode('utf-8'))
                message = unpack_string(payload[pseudo_len:])
                print(f"\n[{pseudo}] {message}")
                print("> ", end="", flush=True)
            
            elif msg_type == JOIN_OK:
                print("\n[Vous avez rejoint le salon]")
                print("> ", end="", flush=True)
            
            elif msg_type == ERROR:
                code = payload[0]
                error_msg = unpack_string(payload[1:])
                print(f"\n[Erreur {code}] {error_msg}")
                print("> ", end="", flush=True)
            
            elif msg_type == ROOM_UPDATE:
                # Notification quand un user rejoint/quitte le salon
                room_name = unpack_string(payload)
                offset = 2 + len(room_name.encode('utf-8'))
                user = unpack_string(payload[offset:])
                offset += 2 + len(user.encode('utf-8'))
                action = unpack_string(payload[offset:])
                
                if action == "join":
                    print(f"\n[→ {user} a rejoint le salon]")
                else:
                    print(f"\n[← {user} a quitté le salon]")
                print("> ", end="", flush=True)
            
        except Exception as e:
            print(f"\n[Erreur de réception: {e}]")
            break


def main():
    print("=== Client de Chat ===")
    print(f"Connexion à {SERVER_IP}:{SERVER_PORT}...")
    
    # Connexion
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((SERVER_IP, SERVER_PORT))
    except ConnectionRefusedError:
        print("Impossible de se connecter au serveur. Est-il lancé ?")
        return
    
    # Demander le pseudo
    pseudo = input("Votre pseudo: ").strip()
    if not pseudo:
        print("Pseudo invalide.")
        return
    
    # Login
    sock.send(pack_message(LOGIN, pack_string(pseudo)))
    header = sock.recv(5)
    msg_type, length = unpack_header(header)
    
    if msg_type == LOGIN_OK:
        print(f"Bienvenue {pseudo} !")
    else:
        payload = sock.recv(length)
        error = unpack_string(payload)
        print(f"Échec du login: {error}")
        return
    
    # Lancer le thread de réception
    receiver = threading.Thread(target=receive_messages, args=(sock,), daemon=True)
    receiver.start()
    
    print("\nCommandes: /join <salon> | /leave | /quit")
    print("Ou tapez directement un message.\n")
    
    # Boucle principale
    while True:
        try:
            msg = input("> ").strip()
            
            if not msg:
                continue
            
            if msg.startswith("/join "):
                room = msg[6:].strip()
                if room:
                    sock.send(pack_message(JOIN, pack_string(room)))
                else:
                    print("Usage: /join <nom_du_salon>")
            
            elif msg == "/leave":
                sock.send(pack_message(LEAVE))
                print("[Vous avez quitté le salon]")
            
            elif msg == "/quit":
                print("Au revoir !")
                break
            
            else:
                # Envoyer un message
                sock.send(pack_message(MSG, pack_string(msg)))
        
        except KeyboardInterrupt:
            print("\nAu revoir !")
            break
    
    sock.close()


if __name__ == "__main__":
    main()
