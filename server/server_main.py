"""
Point d'entrée du serveur de chat.

Ce fichier est responsable :
- de la création de la socket d'écoute
- de la réception des connexions clients
- du déclenchement de la logique serveur définie dans server.py
- du lancement du dashboard admin

Il ne contient pas de logique métier : celle-ci reste dans ChatServer.
"""

import socket
import threading
# Ensure running the script directly can import package modules
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from server.server import ChatServer
from server.admin_gui import run_admin_dashboard

# Adresse et port d'écoute du serveur
HOST = "0.0.0.0"  # toutes les interfaces
PORT = 5555       # port à utiliser pour les clients (5000 est utilisé par macOS)


def run_socket_server(server):
    """
    Lance le serveur socket dans un thread.
    """
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
            client_thread = threading.Thread(
                target=server.handle_client,
                args=(client_sock,),
                daemon=True
            )
            client_thread.start()

    finally:
        sock.close()
        print("Serveur arrêté.")


def main():
    """
    Initialise le serveur et le dashboard admin.
    Le serveur socket tourne dans un thread, le dashboard Flet dans le main thread.
    """

    server = ChatServer()

    # Lancer le serveur socket dans un thread séparé
    server_thread = threading.Thread(
        target=run_socket_server,
        args=(server,),
        daemon=True
    )
    server_thread.start()

    # Lancer le dashboard admin dans le main thread (requis par Flet)
    print("Dashboard admin lancé")
    run_admin_dashboard(server)


if __name__ == "__main__":
    main()
