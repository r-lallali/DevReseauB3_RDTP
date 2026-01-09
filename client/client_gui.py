"""
Ce fichier est le point central qui orchestre tous les composants UI
et la connexion réseau.

Usage:
    python3 client/client_gui.py
"""

import flet as ft
import sys
import os

# Configuration du path pour les imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import des composants UI
from client.ui.theme import *
from client.ui.dialogs import ConnectDialog
from client.ui.toolbar import Toolbar
from client.ui.server_tree import ServerTree
from client.ui.info_panel import InfoPanel
from client.ui.chat_panel import ChatPanel

# Import du gestionnaire réseau
from client.network.connection import NetworkManager

# Import du protocole
from common.protocol import *


class ChatClient:
    """
    Classe principale du client de chat.
    
    Orchestre les composants UI et la connexion réseau.
    """
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.pseudo = None
        self.server_ip = DEFAULT_SERVER_IP
        self.server_port = DEFAULT_SERVER_PORT
        
        # État du chat
        self.current_room = None
        self.custom_channel_name = None
        self.room_members = {}  # room_name -> set de membres
        self._pending_room = None
        
        # Configuration de la page
        self._setup_page()
        
        # Gestionnaire réseau
        self.network = NetworkManager(
            on_message_callback=self._handle_message,
            on_disconnect_callback=self._handle_disconnect
        )
        
        # Afficher le dialog de connexion
        self._show_connect_dialog()
    
    def _setup_page(self):
        """Configure les propriétés de la page Flet."""
        self.page.title = "RDTP Speak"
        self.page.window.width = 800
        self.page.window.height = 550
        self.page.bgcolor = TS_BG_GRAY
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.padding = 0
    
    # ==================== Connexion ====================
    
    def _show_connect_dialog(self):
        """Affiche le dialog de connexion."""
        self.connect_dialog = ConnectDialog(
            self.page,
            on_connect_callback=self._do_connect
        )
        self.connect_dialog.show()
    
    def _do_connect(self, pseudo: str, ip: str, port: int):
        """Effectue la connexion au serveur."""
        success, error = self.network.connect(ip, port, pseudo)
        
        if success:
            self.pseudo = pseudo
            self.server_ip = ip
            self.server_port = port
            
            # Fermer le dialog et afficher l'UI principale
            self.connect_dialog.close()
            self._setup_main_ui()
            
            # Démarrer la réception des messages
            self.network.start_receive_loop()
            
            self.chat_panel.add_log(f'"{pseudo}" connected', TS_BLUE)
        else:
            self.connect_dialog.show_error(error)
    
    # ==================== Interface principale ====================
    
    def _setup_main_ui(self):
        """Configure l'interface principale après la connexion."""
        
        # Créer les composants
        self.toolbar = Toolbar(
            on_toggle_mic=self._on_toggle_mic,
            on_toggle_sound=self._on_toggle_sound,
            on_leave_channel=self._on_leave_channel
        )
        
        self.server_tree = ServerTree(
            self.server_ip, 
            self.server_port,
            on_join_channel=self._on_join_channel,
            on_join_custom_channel=self._on_join_custom_channel
        )
        
        self.info_panel = InfoPanel(self.pseudo)
        
        self.chat_panel = ChatPanel(
            self.server_ip,
            on_send_message=self._on_send_message
        )
        
        # Barre de statut
        status_bar = ft.Container(
            content=ft.Row([
                ft.Container(expand=True),
                ft.Text(f"Connected as {self.pseudo}", color=TS_TEXT_GRAY, size=11),
            ], spacing=8),
            bgcolor=TS_BG_LIGHT,
            padding=ft.padding.only(left=10, right=10, top=3, bottom=3),
            border=ft.border.only(top=ft.BorderSide(1, TS_BORDER)),
        )
        
        # Zone principale (gauche + droite)
        top_area = ft.Row([
            self.server_tree.get_widget(),
            self.info_panel.get_widget(),
        ], spacing=5, expand=True)
        
        # Assemblage final
        self.page.add(
            ft.Container(
                content=ft.Column([
                    self.toolbar.get_widget(),
                    ft.Container(
                        content=ft.Column([
                            top_area,
                            self.chat_panel.get_widget(),
                        ], spacing=5),
                        padding=5,
                        expand=True,
                    ),
                    status_bar,
                ], spacing=0, expand=True),
                expand=True,
            )
        )
    
    def _refresh_ui(self):
        """Rafraîchit l'affichage de tous les composants."""
        # Mettre à jour l'arborescence
        self.server_tree.update_display(
            current_room=self.current_room,
            custom_channel_name=self.custom_channel_name,
            room_members=self.room_members,
            my_pseudo=self.pseudo
        )
        
        # Mettre à jour le panneau d'info
        current_members = self.room_members.get(self.current_room, set()) if self.current_room else set()
        self.info_panel.update_info(
            channel=self.current_room,
            user_count=len(current_members)
        )
        
        # Mettre à jour l'onglet channel
        self.chat_panel.update_channel_tab(self.current_room)
        
        self.page.update()
    
    # ==================== Callbacks Toolbar ====================
    
    def _on_toggle_mic(self, muted: bool):
        """Callback quand le micro est mute/unmute."""
        status = "muted" if muted else "unmuted"
        self.chat_panel.add_log(f"Microphone {status}", TS_BLUE)
        self.page.update()
    
    def _on_toggle_sound(self, muted: bool):
        """Callback quand le son est mute/unmute."""
        status = "muted" if muted else "unmuted"
        self.chat_panel.add_log(f"Sound {status}", TS_BLUE)
        self.page.update()
    
    def _on_leave_channel(self):
        """Callback pour quitter le channel actuel."""
        if not self.current_room:
            self.chat_panel.add_log("You are not in a channel", TS_RED)
            self.page.update()
            return
        
        self.network.send_leave()
        old_room = self.current_room
        
        # Si c'était un custom channel, le supprimer
        if old_room != "Default Channel" and old_room == self.custom_channel_name:
            self.custom_channel_name = None
        
        self.current_room = None
        self._refresh_ui()
        self.chat_panel.add_log(f'Left channel "{old_room}"', TS_BLUE)
    
    # ==================== Callbacks ServerTree ====================
    
    def _on_join_channel(self, channel_name: str):
        """Callback pour rejoindre un channel."""
        if channel_name == self.current_room:
            return
        
        # Si on quitte un custom channel
        if self.current_room and self.current_room != "Default Channel":
            if self.current_room == self.custom_channel_name:
                self.custom_channel_name = None
        
        self._pending_room = channel_name
        self.network.send_join(channel_name)
    
    def _on_join_custom_channel(self, channel_name: str):
        """Callback pour créer/rejoindre un custom channel."""
        self.custom_channel_name = channel_name
        self._on_join_channel(channel_name)
    
    # ==================== Callback ChatPanel ====================
    
    def _on_send_message(self, message: str):
        """Callback pour envoyer un message."""
        if self.current_room:
            self.network.send_message(message)
        else:
            self.chat_panel.add_log("Join a channel first!", TS_RED)
        self.page.update()
    
    # ==================== Réception des messages ====================
    
    def _handle_message(self, msg_type: int, payload: bytes):
        """
        Traite un message reçu du serveur.
        
        Args:
            msg_type: Type du message (voir protocol.py)
            payload: Données du message
        """
        if msg_type == MSG_BROADCAST:
            self._handle_msg_broadcast(payload)
        
        elif msg_type == JOIN_OK:
            self._handle_join_ok()
        
        elif msg_type == ERROR:
            self._handle_error(payload)
        
        elif msg_type == ROOM_UPDATE:
            self._handle_room_update(payload)
    
    def _handle_msg_broadcast(self, payload: bytes):
        """Traite un message broadcast."""
        pseudo = unpack_string(payload)
        offset = 2 + len(pseudo.encode('utf-8'))
        message = unpack_string(payload[offset:])
        
        is_system = pseudo == "Serveur"
        is_me = pseudo == self.pseudo
        
        # Mettre à jour la liste des membres si nécessaire
        if not is_system and pseudo not in self.room_members.get(self.current_room, set()):
            if self.current_room:
                if self.current_room not in self.room_members:
                    self.room_members[self.current_room] = set()
                self.room_members[self.current_room].add(pseudo)
                self._refresh_ui()
        
        self.chat_panel.add_chat_message(pseudo, message, is_me=is_me, is_system=is_system)
        self.page.update()
    
    def _handle_join_ok(self):
        """Traite une confirmation de join."""
        room = self._pending_room
        if room:
            self.current_room = room
            self._pending_room = None
        
        # Initialiser les membres de la room
        if room not in self.room_members:
            self.room_members[room] = set()
        self.room_members[room].add(self.pseudo)
        
        self._refresh_ui()
        self.chat_panel.add_log(f'Joined channel "{room}"', TS_BLUE)
        self.page.update()
    
    def _handle_error(self, payload: bytes):
        """Traite un message d'erreur."""
        code = payload[0]
        error_msg = unpack_string(payload[1:])
        self.chat_panel.add_log(f"Error: {error_msg}", TS_RED)
        self.page.update()
    
    def _handle_room_update(self, payload: bytes):
        """Traite une mise à jour de room."""
        room_name = unpack_string(payload)
        offset = 2 + len(room_name.encode('utf-8'))
        user = unpack_string(payload[offset:])
        offset += 2 + len(user.encode('utf-8'))
        action = unpack_string(payload[offset:])
        
        # Mettre à jour room_members
        if room_name not in self.room_members:
            self.room_members[room_name] = set()
        
        if action == "join":
            self.room_members[room_name].add(user)
        elif action == "leave":
            self.room_members[room_name].discard(user)
        
        self._refresh_ui()
    
    def _handle_disconnect(self):
        """Gère la déconnexion du serveur."""
        self.chat_panel.add_log("Disconnected from server", TS_RED)
        self.page.update()
        
        # Réinitialiser et retourner au dialog de connexion
        self._reset_and_show_connect()
    
    def _reset_and_show_connect(self):
        """Réinitialise l'état et affiche le dialog de connexion."""
        try:
            self.network.disconnect()
            self.pseudo = None
            self.current_room = None
            self.custom_channel_name = None
            self.room_members = {}
            
            self.page.controls.clear()
            self.page.overlay.clear()
            self._show_connect_dialog()
            self.connect_dialog.show_error("Disconnected from server")
            self.page.update()
        except:
            pass


def main(page: ft.Page):
    """Point d'entrée de l'application Flet."""
    ChatClient(page)


if __name__ == "__main__":
    ft.app(target=main)
