"""
Point d'entrée du serveur de chat.

Ce fichier est responsable :
- de la création de la socket d'écoute
- de la réception des connexions clients
- du déclenchement de la logique serveur définie dans server.py

Il ne contient pas de logique métier : celle-ci reste dans ChatServer.
"""

import socket
import threading
# Ensure running the script directly can import package modules
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from server.server import ChatServer

# Adresse et port d'écoute du serveur
HOST = "0.0.0.0"  # toutes les interfaces
PORT = 5002       # port à utiliser pour les clients (5000 est utilisé par macOS)

def main():
    """
    Initialise le serveur et accepte les connexions entrantes.
    Chaque client est géré dans un thread séparé pour permettre
    plusieurs connexions simultanées.
    """

    server = ChatServer()

    # Création de la socket TCP
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Permet de réutiliser l'adresse immédiatement après fermeture
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

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

            # Créer un thread pour gérer ce client
            # Cela permet d'accepter d'autres clients pendant que celui-ci est traité
            client_thread = threading.Thread(
                target=server.handle_client,
                args=(client_sock,),
                daemon=True  # Le thread se termine si le programme principal se termine
            )
            client_thread.start()

    finally:
        # Fermeture propre de la socket
        sock.close()
        print("Serveur arrêté.")

if __name__ == "__main__":
    main()
