import socket
import threading
import datetime
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
        self.last_message_time = None  # datetime du dernier message envoyé
        self.pending_file = None

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
            
            # Récupérer les membres actuels avant d'ajouter le nouveau
            existing_members = list(self.rooms[room_name])
            
            # Ajouter le client au salon
            self.rooms[room_name].add(client.pseudo)
        
        client.room = room_name
        client.state = STATE_IN_ROOM  # Transition: AUTHENTIFIÉ → DANS_SALON
        
        # Confirmer
        client.sock.send(pack_message(JOIN_OK))
        
        # Envoyer la liste des membres existants au nouveau client via ROOM_UPDATE
        for member in existing_members:
            payload = pack_string(room_name) + pack_string(member) + pack_string("join")
            client.sock.send(pack_message(ROOM_UPDATE, payload))
        
        # Notifier TOUS les clients que le nouveau a rejoint (pour la liste globale)
        self._broadcast_room_update(room_name, client.pseudo, "join")
        
        # Notifier les autres dans le chat
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
        
        # Enregistrer le timestamp du message pour le dashboard admin
        client.last_message_time = datetime.datetime.now()
        
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
    
    def _broadcast_room_update(self, room_name: str, user: str, action: str):
        """
        Diffuse une mise à jour de room à TOUS les clients authentifiés.
        Permet à tous de voir qui est dans chaque room.
        
        Args:
            room_name: Le nom du salon
            user: L'utilisateur concerné
            action: "join" ou "leave"
        """
        # Format: [room_name][user][action]
        payload = pack_string(room_name) + pack_string(user) + pack_string(action)
        msg = pack_message(ROOM_UPDATE, payload)
        
        # Envoyer à tous les clients authentifiés
        with self.lock:
            for pseudo, client in self.clients.items():
                if client.is_authenticated():
                    try:
                        client.sock.send(msg)
                    except:
                        pass
    
    def _remove_client_from_room(self, client: ClientContext, reason: str = "s'est déconnecté"):
        """
        Retire un client de son salon actuel et notifie les autres.
        Méthode interne utilisée par handle_join, handle_leave et déconnexion.
        
        Args:
            client: Le client à retirer
            reason: La raison (par défaut "s'est déconnecté")
        """
        room_name = client.room
        
        with self.lock:
            if room_name and room_name in self.rooms:
                # Retirer le pseudo du salon
                self.rooms[room_name].discard(client.pseudo)
                
                # Supprimer le salon s'il est vide (optionnel, mais propre)
                if len(self.rooms[room_name]) == 0:
                    del self.rooms[room_name]
        
        # Notifier les autres membres du room dans le chat
        if room_name and client.pseudo:
            self._broadcast_to_room(room_name, "Serveur", f"{client.pseudo} {reason}")
            # Notifier TOUS les clients pour la liste globale
            self._broadcast_room_update(room_name, client.pseudo, "leave")
        
        # Mettre à jour l'état du client
        client.room = None
        client.state = STATE_AUTHENTICATED  # Transition: DANS_SALON → AUTHENTIFIÉ

    def get_clients_info(self) -> list:
        """
        Retourne les informations de tous les clients connectés.
        Utilisé par le dashboard admin.
        
        Returns:
            list: Liste de dictionnaires contenant les infos clients
        """
        clients_info = []
        with self.lock:
            for pseudo, client in self.clients.items():
                info = {
                    'pseudo': pseudo,
                    'room': client.room or '-',
                    'last_message': client.last_message_time.strftime('%H:%M:%S') if client.last_message_time else '-'
                }
                clients_info.append(info)
        return clients_info

    def kick_client(self, pseudo: str) -> bool:
        """
        Kick un client du serveur.
        
        Args:
            pseudo: Le pseudo du client à kicker
            
        Returns:
            bool: True si le client a été kické, False sinon
        """
        with self.lock:
            if pseudo not in self.clients:
                return False
            
            client = self.clients[pseudo]
            room = client.room
        
        # Broadcaster le message de kick et retirer du room
        if room:
            self._remove_client_from_room(client, "a été kické")
        
        # Fermer la socket du client (ce qui va déclencher la déconnexion)
        try:
            client.sock.close()
        except:
            pass
        
        # Retirer le client de la liste
        with self.lock:
            if pseudo in self.clients:
                del self.clients[pseudo]
        
        return True

    def handle_file_offer(self, client: ClientContext, payload: bytes):
        if not client.is_in_room():
            client.sock.send(pack_message(
                ERROR,
                bytes([0x03]) + pack_string("Pas dans un salon")
            ))
            return

        if client.state == STATE_WAITING_FILE_CONFIRMATION:
            client.sock.send(pack_message(
                ERROR,
                bytes([0x06]) + pack_string("Déjà une requête en cours")
            ))
            return

        # Décodage payload
        filename = unpack_string(payload)
        size_offset = 2 + len(filename.encode("utf-8"))
        size = unpack_int(payload[size_offset:])

        # Passage à l'état intermédiaire
        client.state = STATE_WAITING_FILE_CONFIRMATION
        client.pending_file = {
            "filename": filename,
            "size": size,
            "accepted": set(),
            "rejected": set()
        }

        # Diffuser la demande aux autres clients du salon
        request_payload = (
            pack_string(client.pseudo) +
            pack_string(filename) +
            pack_int(size)
        )

        request_msg = pack_message(FILE_REQUEST, request_payload)

        for pseudo in self.rooms.get(client.room, []):
            if pseudo != client.pseudo:
                self.clients[pseudo].sock.send(request_msg)


    def handle_file_response(self, client: ClientContext, accepted: bool):
        # Trouver le client émetteur
        for sender in self.clients.values():
            if sender.state == STATE_WAITING_FILE_CONFIRMATION:
                break
        else:
            return  # Aucun transfert en attente

        if accepted:
            sender.pending_file["accepted"].add(client.pseudo)
        else:
            sender.pending_file["rejected"].add(client.pseudo)

        # Décision simple : 1 refus = rejet
        if sender.pending_file["rejected"]:
            sender.sock.send(pack_message(
                FILE_CANCEL,
                pack_string("Refus d'un participant")
            ))
            sender.state = STATE_IN_ROOM
            sender.pending_file = None
            return

        # Tous ont accepté
        room_clients = self.rooms.get(sender.room, set())
        if sender.pending_file["accepted"] >= (room_clients - {sender.pseudo}):
            sender.sock.send(pack_message(FILE_START))
            sender.state = STATE_IN_ROOM
            sender.pending_file = None



    def handle_client(self, sock):
        """
        Traite un client tant que la connexion TCP est ouverte.
        """

        client = ClientContext(sock)

        try:
            while True:
                # Lecture de l'en-tête
                try:
                    header = sock.recv(5)
                except OSError:
                    # Socket fermée (par exemple après un kick)
                    break
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

                # ====================
                # ÉTAT INTERMÉDIAIRE : attente confirmation fichier
                # ====================
                if client.state == STATE_WAITING_FILE_CONFIRMATION:
                    if msg_type == FILE_ACCEPT:
                        self.handle_file_response(client, accepted=True)

                    elif msg_type == FILE_REJECT:
                        self.handle_file_response(client, accepted=False)

                    else:
                        sock.send(pack_message(
                            ERROR,
                            bytes([0x06]) + pack_string("Action bloquée : transfert en attente")
                        ))
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
