"""
connection.py - Gestion de la connexion réseau.

Gère la connexion au serveur, l'envoi de messages,
et la boucle de réception.
"""

import socket
import threading
import sys
import os

# Import du protocole
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from common.protocol import *


class NetworkManager:
    """Gère la connexion réseau avec le serveur."""
    
    def __init__(self, on_message_callback, on_disconnect_callback):
        """
        Args:
            on_message_callback: Fonction(msg_type, payload) appelée pour chaque message reçu
            on_disconnect_callback: Fonction() appelée lors de la déconnexion
        """
        self.sock = None
        self.connected = False
        self.on_message = on_message_callback
        self.on_disconnect = on_disconnect_callback
    
    def connect(self, ip: str, port: int, pseudo: str) -> tuple[bool, str]:
        """
        Se connecte au serveur et effectue le login.
        
        Args:
            ip: Adresse IP du serveur
            port: Port du serveur
            pseudo: Pseudo à utiliser
            
        Returns:
            tuple: (success: bool, error_message: str ou None)
        """
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((ip, port))
            
            # Envoyer le LOGIN
            self.sock.send(pack_message(LOGIN, pack_string(pseudo)))
            
            # Attendre la réponse
            header = self.sock.recv(5)
            msg_type, length = unpack_header(header)
            
            if msg_type == LOGIN_OK:
                self.connected = True
                return True, None
            else:
                # Erreur de login
                payload = self.sock.recv(length)
                error_msg = unpack_string(payload)
                self.sock.close()
                return False, error_msg
                
        except ConnectionRefusedError:
            return False, "Server not available"
        except Exception as ex:
            return False, str(ex)
    
    def disconnect(self):
        """Ferme la connexion."""
        self.connected = False
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
            self.sock = None
    
    def start_receive_loop(self):
        """Démarre la boucle de réception dans un thread séparé."""
        thread = threading.Thread(target=self._receive_loop, daemon=True)
        thread.start()
    
    def _receive_loop(self):
        """Boucle de réception des messages du serveur."""
        while self.connected:
            try:
                header = self.sock.recv(5)
                if not header:
                    # Connexion fermée par le serveur
                    self.connected = False
                    self.on_disconnect()
                    break
                
                msg_type, length = unpack_header(header)
                payload = self.sock.recv(length) if length > 0 else b""
                
                # Transmettre le message au callback
                self.on_message(msg_type, payload)
                
            except Exception as ex:
                if self.connected:
                    self.connected = False
                    self.on_disconnect()
                break
        
        self.connected = False
    
    # ==================== Méthodes d'envoi ====================
    
    def send_join(self, room_name: str):
        """Envoie une demande de rejoindre un channel."""
        if self.connected:
            self.sock.send(pack_message(JOIN, pack_string(room_name)))
    
    def send_leave(self):
        """Envoie une demande de quitter le channel actuel."""
        if self.connected:
            self.sock.send(pack_message(LEAVE))
    
    def send_message(self, text: str):
        """Envoie un message dans le channel actuel."""
        if self.connected:
            self.sock.send(pack_message(MSG, pack_string(text)))
