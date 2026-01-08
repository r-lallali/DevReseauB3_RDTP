import socket
import threading
from common.protocol import *


class ClientContext:
    """
    Représente l'état d'un client connecté.
    """

    def __init__(self, sock):
        self.sock = sock
        self.pseudo = None
        self.state = STATE_CONNECTED
        self.room = None

    def is_authenticated(self):
        return self.state in (STATE_AUTHENTICATED, STATE_IN_ROOM)

    def is_in_room(self):
        return self.state == STATE_IN_ROOM


class ChatServer:
    """
    Serveur de chat gérant les connexions des clients.
    Thread-safe : utilise un Lock pour protéger les structures partagées.
    """

    def __init__(self):
        self.clients = {}
        
        # Dictionnaire des salons : nom_salon → set de pseudos
        # Exemple : {"général": {"Alice", "Bob"}, "dev": {"Charlie"}}
        self.rooms = {}
        
        # Lock pour protéger l'accès concurrent aux clients et aux salons
        # Nécessaire car plusieurs threads (un par client) accèdent à ces structures
        self.lock = threading.Lock()
    
    def handle_join(self, client: ClientContext, payload: bytes):
        """
        Traite une demande JOIN d'un client.
        
        Args:
            client: Le contexte du client qui fait la demande
            payload: Les données du message (contient le nom du salon)
        """
        
        # Vérifier que le client est authentifié
        if not client.is_authenticated():
            client.sock.send(pack_message(ERROR, bytes([0x06]) + pack_string("Non authentifié")))
            return
        
        # Extraire le nom du salon
        room_name = unpack_string(payload)
        
        # Vérifier que le nom du salon est valide
        if not room_name or len(room_name) > 32:
            client.sock.send(pack_message(ERROR, bytes([0x06]) + pack_string("Nom de salon invalide")))
            return
        
        # Si le client est déjà dans un salon, le retirer d'abord
        if client.room is not None:
            self._remove_client_from_room(client)
        
        # Section critique : modification des structures partagées
        with self.lock:
            # Créer le salon s'il n'existe pas
            if room_name not in self.rooms:
                self.rooms[room_name] = set()
            
            # Ajouter le client au salon
            self.rooms[room_name].add(client.pseudo)
        
        client.room = room_name
        client.state = STATE_IN_ROOM  # Transition: AUTHENTIFIÉ → DANS_SALON
        
        # Confirmer
        client.sock.send(pack_message(JOIN_OK))
        
        # NOTIFICATION (US8)
        # Tous les clients connectés (sauf le nouveau) reçoivent un message d'info "PSEUDO s'est connecté"
        # _broadcast_to_room envoie à tout le monde dans la liste, on doit filtrer pour éviter d'envoyer à soi-même ?
        # La méthode _broadcast_to_room implémentée itère sur `self.rooms[room_name]`.
        # Si on l'appelle maintenant, le client courant EST dans la liste (ajouté lignes 73-74).
        # Donc il va recevoir le message.
        # Le DoD dit "sauf le nouveau".
        # Je vais modifier _broadcast_to_room pour accepter un paramètre d'exclusion ou gérer l'exclusion ici.
        # Pour faire simple et moins intrusif, je vais filtrer dans _broadcast_to_room si possible,
        # ou je l'appelle et le client filtrera ? Non le serveur ne doit pas l'envoyer.
        
        # Option: Modifier _broadcast_to_room pour exclude
        self._broadcast_to_room(room_name, "Serveur", f"{client.pseudo} s'est connecté", exclude_pseudo=client.pseudo)
    
    def handle_leave(self, client: ClientContext):
        """
        Traite une demande LEAVE d'un client.
        
        Args:
            client: Le contexte du client qui veut quitter
        """
        
        # Vérifier que le client est dans un salon
        if not client.is_in_room():
            client.sock.send(pack_message(ERROR, bytes([0x03]) + pack_string("Pas dans un salon")))
            return
        
        # Retirer le client du salon
        self._remove_client_from_room(client)
        
        # Pas de message de confirmation selon le protocole (LEAVE n'a pas de LEAVE_OK)
        # Le client sait qu'il a quitté car il a envoyé LEAVE
    
    def handle_msg(self, client: ClientContext, payload: bytes):
        """
        Traite un message MSG d'un client et le diffuse au salon.
        
        Args:
            client: Le contexte du client qui envoie le message
            payload: Les données du message (contient le texte)
        """
        
        # Vérifier que le client est dans un salon
        if not client.is_in_room():
            client.sock.send(pack_message(ERROR, bytes([0x03]) + pack_string("Pas dans un salon")))
            return
        
        # Extraire le message
        message = unpack_string(payload)
        
        # Vérifier que le message n'est pas vide
        if not message:
            client.sock.send(pack_message(ERROR, bytes([0x05]) + pack_string("Message vide")))
            return
        
        # Vérifier la taille du message
        if len(message) > MAX_MSG_LEN:
            client.sock.send(pack_message(ERROR, bytes([0x05]) + pack_string("Message trop long")))
            return
        
        # Diffuser le message à tous les clients du salon
        self._broadcast_to_room(client.room, client.pseudo, message)
    
    def _broadcast_to_room(self, room_name: str, sender_pseudo: str, message: str, exclude_pseudo: str = None):
        """
        Diffuse un message à tous les clients d'un salon.
        
        Args:
            room_name: Le nom du salon
            sender_pseudo: Le pseudo de l'expéditeur
            message: Le message à diffuser
            exclude_pseudo: Pseudo à exclure de la diffusion (optionnel)
        """
        
        # Vérifier que le salon existe
        if room_name not in self.rooms:
            return
        
        # Construire le payload MSG_BROADCAST : [pseudo][message]
        broadcast_payload = pack_string(sender_pseudo) + pack_string(message)
        broadcast_msg = pack_message(MSG_BROADCAST, broadcast_payload)
        
        # Envoyer à chaque client du salon
        for pseudo in self.rooms[room_name]:
            if pseudo == exclude_pseudo:
                continue
                
            if pseudo in self.clients:
                try:
                    self.clients[pseudo].sock.send(broadcast_msg)
                except:
                    # Si l'envoi échoue, on ignore (le client sera nettoyé plus tard)
                    pass
    
    def _remove_client_from_room(self, client: ClientContext):
        """
        Retire un client de son salon actuel.
        Méthode interne utilisée par handle_join et handle_leave.
        """
        
        with self.lock:
            if client.room and client.room in self.rooms:
                # Retirer le pseudo du salon
                self.rooms[client.room].discard(client.pseudo)
                
                # Supprimer le salon s'il est vide (optionnel, mais propre)
                if len(self.rooms[client.room]) == 0:
                    del self.rooms[client.room]
        
        # Mettre à jour l'état du client
        client.room = None
        client.state = STATE_AUTHENTICATED  # Transition: DANS_SALON → AUTHENTIFIÉ

    def handle_client(self, sock):
        """
        Traite un client tant que la connexion TCP est ouverte.
        """

        client = ClientContext(sock)

        try:
            while True:
                # Lecture de l'en-tête
                header = sock.recv(5)
                if not header:
                    break

                msg_type, length = unpack_header(header)
                payload = sock.recv(length)

                # --------------------
                # Phase LOGIN
                # --------------------
                if client.state == STATE_CONNECTED:
                    if msg_type != LOGIN:
                        sock.send(pack_message(
                            LOGIN_ERR,
                            pack_string("Login requis")
                        ))
                        break

                    pseudo = unpack_string(payload)

                    if not pseudo or len(pseudo) > MAX_PSEUDO_LEN:
                        sock.send(pack_message(
                            LOGIN_ERR,
                            pack_string("Pseudo invalide")
                        ))
                        break

                    # Section critique : vérification et ajout du client
                    with self.lock:
                        if pseudo in self.clients:
                            sock.send(pack_message(
                                LOGIN_ERR,
                                pack_string("Pseudo déjà utilisé")
                            ))
                            break

                        # Succès
                        client.pseudo = pseudo
                        client.state = STATE_AUTHENTICATED
                        self.clients[pseudo] = client # Changed from self.clients_by_pseudo to self.clients to match original structure
                    
                    sock.send(pack_message(LOGIN_OK))
                    print(f"Client authentifié : {pseudo}")
                    continue

                # --------------------
                # États AUTHENTIFIÉ et DANS_SALON
                # --------------------
                if msg_type == JOIN:
                    self.handle_join(client, payload)
                
                elif msg_type == LEAVE:
                    self.handle_leave(client)
                
                elif msg_type == MSG:
                    self.handle_msg(client, payload)
                # Pour l'instant, on ne gère pas MSG ici, mais on garde la co.
                else:
                    print(f"Message reçu de {client.pseudo}: Type {msg_type}")                  
                    sock.send(pack_message(
                        ERROR,
                        bytes([0x06]) + pack_string("Action non autorisée")
                    ))

        finally:
            # Nettoyage lors de la déconnexion
            # Retirer le client du salon s'il y était
            if client.is_in_room():
                self._remove_client_from_room(client)
            
            # Retirer le client de la liste
            with self.lock:
                if client.pseudo and client.pseudo in self.clients:
                    del self.clients[client.pseudo]

            sock.close()
