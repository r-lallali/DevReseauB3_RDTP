import socket
from common.protocol import *


import socket
import selectors
import sys
from common.protocol import *


class ClientContext:
    """
    Représente l'état d'un client connecté.
    
    Chaque client a un état qui détermine ce qu'il peut faire :
    - CONNECTÉ : peut seulement envoyer LOGIN
    - AUTHENTIFIÉ : peut envoyer JOIN
    - DANS_SALON : peut envoyer MSG, LEAVE
    """

    def __init__(self, sock):
        self.sock = sock
        self.addr = sock.getpeername()
        self.pseudo = None
        self.state = STATE_CONNECTED  # État initial après connexion TCP
        self.room = None              # Nom du salon (None si pas dans un salon)
    
    def is_authenticated(self):
        """Retourne True si le client a passé l'étape LOGIN."""
        return self.state in (STATE_AUTHENTICATED, STATE_IN_ROOM)
    
    def is_in_room(self):
        """Retourne True si le client est dans un salon."""
        return self.state == STATE_IN_ROOM


class ChatServer:
    """
    Serveur de chat gérant les connexions des clients via select (non-bloquant).
    """

    def __init__(self, host="0.0.0.0", port=5002):
        self.host = host
        self.port = port
        self.selector = selectors.DefaultSelector()
        # Dictionnaire des clients connectés : pseudo -> ClientContext
        # Note: on garde aussi les clients non-identifiés dans le selecteur
        self.clients_by_pseudo = {}

    def start(self):
        """
        Démarre le serveur et la boucle d'événements.
        """
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Avoid "Address already in use" error
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind((self.host, self.port))
        server_sock.listen()
        server_sock.setblocking(False)
        
        # Enregistre la socket d'écoute
        self.selector.register(server_sock, selectors.EVENT_READ, data=None)
        
        print(f"Serveur en écoute sur {self.host}:{self.port}")
        sys.stdout.flush()

        try:
            while True:
                events = self.selector.select(timeout=None)
                for key, mask in events:
                    if key.data is None:
                        # C'est la socket d'écoute
                        self.accept_connection(key.fileobj)
                    else:
                        # C'est un client
                        self.service_connection(key, mask)
        except KeyboardInterrupt:
            print("Arrêt du serveur demandé.")
        finally:
            self.selector.close()

    def accept_connection(self, sock):
        """Accepte une nouvelle connexion entrante."""
        conn, addr = sock.accept()
        print(f"Connexion de {addr}")
        conn.setblocking(False)
        
        # Crée le contexte client
        client_ctx = ClientContext(conn)
        
        # Enregistre le client dans le sélecteur
        events = selectors.EVENT_READ
        self.selector.register(conn, events, data=client_ctx)

    def service_connection(self, key, mask):
        """Gère les événements sur une socket client."""
        client = key.data
        sock = key.fileobj

        if mask & selectors.EVENT_READ:
            # Pour l'instant, on suppose que les messages arrivent entiers 
            # ou que recv attendra (mais on est en non-bloquant).
            # Solution robuste simplifiée : on essaie de lire l'en-tête (5 bytes)
            # En VRAI non-bloquant, on devrait bufferiser.
            # Ici, pour valider US4, on fait un recv au mieux.
            
            try:
                # Lecture en-tête
                # TODO: Gérer partial reads proprement.
                # Pour US4, on suppose que le client envoie le paquet correctement.
                header = sock.recv(5)
                if not header:
                    self.close_connection(key)
                    return
                
                msg_type, length = unpack_header(header)
                
                # Lecture payload
                payload = b""
                if length > 0:
                    payload = sock.recv(length)
                    # Si on n'a pas tout lu, c'est un problème en mode non-bloquant
                    # mais ignorons pour l'instant sauf si critique
                
                self.process_message(client, msg_type, payload)
                
            except ConnectionResetError:
                self.close_connection(key)
            except Exception as e:
                print(f"Erreur avec le client {client.addr}: {e}")
                self.close_connection(key)

    def process_message(self, client, msg_type, payload):
        """Traite un message reçu d'un client."""
        sock = client.sock
        
        # Si le client n'est pas authentifié, seul LOGIN est autorisé
        if not client.is_authenticated():
            if msg_type == LOGIN:
                self.handle_login(client, payload)
            else:
                # Tout autre message provoque une erreur/déconnexion
                self.send_error(sock, "Authentification requise")
                # Ou on ignore ? Le protocole dit "DÉCONNECTÉ -> CONNECTÉ"
                return
        else:
            # Client authentifié
            if msg_type == LOGIN:
                 self.send_error(sock, "Déjà connecté")
            # Pour l'instant, on ne gère pas JOIN/MSG ici (US futures), mais on garde la co.
            # On pourrait dummy handler.
            else:
                 print(f"Message reçu de {client.pseudo}: Type {msg_type}")

    def handle_login(self, client, payload):
        sock = client.sock
        pseudo = unpack_string(payload)
        
        # Validation
        if not pseudo or len(pseudo) > MAX_PSEUDO_LEN:
            sock.send(pack_message(LOGIN_ERR, pack_string("Pseudo invalide")))
            # On pourrait fermer, mais on peut laisser retenter ?
            # Le code original fermait. Gardons ce comportement.
            self.close_connection(self.selector.get_key(sock))
            return
            
        if pseudo in self.clients_by_pseudo:
            sock.send(pack_message(LOGIN_ERR, pack_string("Pseudo déjà utilisé")))
            self.close_connection(self.selector.get_key(sock))
            return
            
        # Succès
        client.pseudo = pseudo
        client.state = STATE_AUTHENTICATED
        self.clients_by_pseudo[pseudo] = client
        
        sock.send(pack_message(LOGIN_OK))
        print(f"Client authentifié : {pseudo}")

    def send_error(self, sock, message):
         sock.send(pack_message(LOGIN_ERR, pack_string(message)))

    def close_connection(self, key):
        """Ferme la connexion et nettoie."""
        client = key.data
        print(f"Déconnexion de {client.addr} ({client.pseudo})")
        
        if client.pseudo and client.pseudo in self.clients_by_pseudo:
            del self.clients_by_pseudo[client.pseudo]
            
        self.selector.unregister(key.fileobj)
        key.fileobj.close()
