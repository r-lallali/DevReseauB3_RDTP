"""
main_client.py

Point d'entrée de l'application cliente.

Ce fichier est responsable :
- de la création de la socket
- de la connexion au serveur
- du déclenchement des actions côté client

Il ne contient pas de logique de protocole, qui est dans client.py.
"""

import socket
import threading
import sys
from client.client import login, listen_server
from common.protocol import LOGIN_OK

# Adresse du serveur
SERVER_IP = "127.0.0.1"
SERVER_PORT = 5000


def main():
    """
    Initialise la connexion au serveur et effectue la phase de login.
    """

    # Création de la socket TCP
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # Connexion au serveur
        sock.connect((SERVER_IP, SERVER_PORT))

        # Pseudo utilisé pour la connexion
        if len(sys.argv) > 1:
            pseudo = sys.argv[1]
        else:
            pseudo = "Donald"

        # Phase de login
        msg_type, payload = login(sock, pseudo)

        print(f"[DEBUG] msg_type reçu: {msg_type} (LOGIN_OK={LOGIN_OK})")
        if msg_type != LOGIN_OK and payload:
            from common.protocol import unpack_string
            try:
                raison = unpack_string(payload)
                print(f"[DEBUG] Raison de l'erreur: {raison}")
            except Exception as e:
                print(f"[DEBUG] Erreur lors du décodage: {e}")

        if msg_type != LOGIN_OK:
            print("Échec de la connexion")
            return

        print("Connexion réussie")

        # Lancer l'écoute du serveur dans un thread séparé
        listen_thread = threading.Thread(
            target=listen_server,
            args=(sock,),
            daemon=True
        )
        listen_thread.start()
        
        # Garder le programme actif
        print("En attente de messages... (Ctrl+C pour quitter)")
        listen_thread.join()
        
    except KeyboardInterrupt:
        print("\nDéconnexion...")

    finally:
        # Fermeture propre de la connexion
        sock.close()


if __name__ == "__main__":
    main()
