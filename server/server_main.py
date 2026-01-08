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
import sys

# Adresse et port d'écoute du serveur
HOST = "0.0.0.0"  # toutes les interfaces
PORT = 5002        # port à utiliser pour les clients

def main():
    """
    Initialise le serveur et accepte les connexions entrantes.
    """
    print("DEBUG: main() called")
    
    server = ChatServer(HOST, PORT)
    server.start()

if __name__ == "__main__":
    main()
