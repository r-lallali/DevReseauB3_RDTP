"""
Point d'entrée du serveur de chat.

Ce fichier est responsable :
- de la création de la socket d'écoute
- de la réception des connexions clients
- du déclenchement de la logique serveur définie dans server.py

Il ne contient pas de logique métier : celle-ci reste dans ChatServer.
"""

import socket
from .server import ChatServer

# Adresse et port d'écoute du serveur
HOST = "0.0.0.0"  # toutes les interfaces
PORT = 5000        # port à utiliser pour les clients

def main():
    """
    Initialise le serveur et accepte les connexions entrantes.
    """

    server = ChatServer()

    # Création de la socket TCP
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # Liaison de la socket à l'adresse et au port
        sock.bind((HOST, PORT))

        # Passage en mode écoute
        sock.listen()
        print(f"Serveur en écoute sur {HOST}:{PORT}")

        # Boucle principale pour accepter les connexions
        while True:
            # Accepte une connexion entrante
            client_sock, client_addr = sock.accept()
            print(f"Connexion de {client_addr}")

            # Transmet le socket au serveur pour traitement
            # Ici, le serveur est minimal et ne gère qu'un message
            server.handle_client(client_sock)

    finally:
        # Fermeture propre de la socket
        sock.close()
        print("Serveur arrêté.")

if __name__ == "__main__":
    main()
