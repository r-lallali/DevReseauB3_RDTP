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
from chat.client import login

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
        pseudo = "Donald"

        # Demande de connexion
        msg_type, payload = login(sock, pseudo)

        # Le traitement de la réponse est volontairement minimal
        if msg_type != 0x01:  # LOGIN_OK
            print("Échec de la connexion")

    finally:
        # Fermeture propre de la socket
        sock.close()


if __name__ == "__main__":
    main()
