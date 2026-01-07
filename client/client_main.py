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
from client.client import login
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
        pseudo = "Donald"

        # Phase de login
        msg_type, _ = login(sock, pseudo)

        if msg_type != LOGIN_OK:
            print("Échec de la connexion")
            return

        print("Connexion réussie")

        # À ce stade, la connexion TCP reste ouverte.
        # Les actions suivantes (JOIN, MSG, etc.) seront ajoutées ici.

    finally:
        # Fermeture propre de la connexion
        sock.close()


if __name__ == "__main__":
    main()
