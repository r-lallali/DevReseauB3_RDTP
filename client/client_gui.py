"""
Client de chat avec interface graphique style TeamSpeak 3.

Usage:
    source venv/bin/activate
    python3 client/client_gui.py
"""

import flet as ft
import socket
import threading
import sys
import os
import datetime
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from common.protocol import *

# Configuration
SERVER_IP = "127.0.0.1"
SERVER_PORT = 5555

# Couleurs style TeamSpeak 3 (thème blanc et bleu)
TS_BG_WHITE = "#ffffff"
TS_BG_GRAY = "#f0f0f0"
TS_BG_LIGHT = "#e8e8e8"
TS_BORDER = "#acacac"
TS_TEXT_BLACK = "#000000"
TS_TEXT_GRAY = "#666666"
TS_BLUE = "#0078d4"
TS_BLUE_LIGHT = "#4da6ff"
TS_RED = "#cc0000"


class ChatClient:
    def __init__(self, page: ft.Page):
        self.page = page
        self.sock = None
        self.pseudo = None
        self.server_ip = SERVER_IP
        self.server_port = SERVER_PORT
        self.current_room = None
        self.connected = False
        self.users_in_room = set()  # Utilisateurs dans la room courante
        self.room_members = {}  # Dictionnaire room -> set de membres (pour affichage global)
        self._pending_room = None
        self.custom_channel_name = None  # Le channel custom créé par l'utilisateur
        
        # Configuration de la page
        self.page.title = "TeamSpeak 3"
        self.page.window.width = 800
        self.page.window.height = 550
        self.page.bgcolor = TS_BG_GRAY
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.padding = 0
        
        # Afficher le dialog de connexion au démarrage
        self.show_connect_dialog()
        
    def show_connect_dialog(self):
        """Affiche le dialog de connexion style TeamSpeak."""
        
        self.dialog_pseudo = ft.TextField(
            label="Nickname",
            hint_text="Entrez votre pseudo...",
            bgcolor=TS_BG_WHITE,
            border_color=TS_BORDER,
            focused_border_color=TS_BLUE,
            color=TS_TEXT_BLACK,
            label_style=ft.TextStyle(color=TS_TEXT_GRAY),
            width=280,
            height=50,
        )
        
        self.dialog_server = ft.TextField(
            label="Server Address",
            value=f"{SERVER_IP}",
            bgcolor=TS_BG_WHITE,
            border_color=TS_BORDER,
            focused_border_color=TS_BLUE,
            color=TS_TEXT_BLACK,
            label_style=ft.TextStyle(color=TS_TEXT_GRAY),
            width=200,
            height=50,
        )
        
        self.dialog_port = ft.TextField(
            label="Port",
            value=f"{SERVER_PORT}",
            bgcolor=TS_BG_WHITE,
            border_color=TS_BORDER,
            focused_border_color=TS_BLUE,
            color=TS_TEXT_BLACK,
            label_style=ft.TextStyle(color=TS_TEXT_GRAY),
            width=70,
            height=50,
        )
        
        self.dialog_error = ft.Text("", color=TS_RED, size=12)
        
        self.connect_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.COMPUTER, color=TS_BLUE, size=24),
                ft.Text("Connect to Server", color=TS_TEXT_BLACK, weight=ft.FontWeight.BOLD, size=16),
            ], spacing=10),
            bgcolor=TS_BG_GRAY,
            content=ft.Container(
                content=ft.Column([
                    ft.Row([self.dialog_server, self.dialog_port], spacing=10),
                    self.dialog_pseudo,
                    self.dialog_error,
                ], spacing=15, horizontal_alignment=ft.CrossAxisAlignment.START),
                padding=10,
                width=320,
            ),
            actions=[
                ft.TextButton(
                    "Cancel",
                    on_click=lambda e: self.page.window.close(),
                    style=ft.ButtonStyle(color=TS_TEXT_GRAY)
                ),
                ft.ElevatedButton(
                    "Connect",
                    on_click=self.do_connect,
                    bgcolor=TS_BLUE,
                    color="white",
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.overlay.append(self.connect_dialog)
        self.connect_dialog.open = True
        self.page.update()
    
    def do_connect(self, e):
        """Effectue la connexion au serveur."""
        pseudo = self.dialog_pseudo.value.strip()
        ip = self.dialog_server.value.strip()
        
        if not pseudo:
            self.dialog_error.value = "Please enter a nickname"
            self.page.update()
            return
        
        try:
            port = int(self.dialog_port.value.strip())
        except:
            self.dialog_error.value = "Invalid port number"
            self.page.update()
            return
        
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((ip, port))
            
            self.sock.send(pack_message(LOGIN, pack_string(pseudo)))
            header = self.sock.recv(5)
            msg_type, length = unpack_header(header)
            
            if msg_type == LOGIN_OK:
                self.pseudo = pseudo
                self.connected = True
                self.server_ip = ip
                self.server_port = port
                
                # Fermer le dialog et afficher l'UI principale
                self.connect_dialog.open = False
                self.page.update()
                
                self.setup_main_ui()
                
                # Lancer le thread de réception
                threading.Thread(target=self.receive_loop, daemon=True).start()
                
                self.log_message(f'"{pseudo}" connected', TS_BLUE)
            else:
                payload = self.sock.recv(length)
                self.dialog_error.value = unpack_string(payload)
                self.sock.close()
                self.page.update()
                
        except ConnectionRefusedError:
            self.dialog_error.value = "Server not available"
            self.page.update()
        except Exception as ex:
            self.dialog_error.value = f"Error: {ex}"
            self.page.update()
        
    def setup_main_ui(self):
        """Configure l'interface principale style TeamSpeak 3."""
        
        # ============ TOOLBAR ============
        self.mic_btn = self._toolbar_icon(ft.Icons.MIC, color=TS_BLUE, tooltip="Mute Microphone", on_click=self.toggle_mic)
        self.sound_btn = self._toolbar_icon(ft.Icons.HEADSET, color=TS_BLUE, tooltip="Mute Sound", on_click=self.toggle_sound)
        self.mic_muted = False
        self.sound_muted = False
        
        toolbar = ft.Container(
            content=ft.Row([
                self.mic_btn,
                self.sound_btn,
                ft.VerticalDivider(width=1, color=TS_BORDER),
                self._toolbar_icon(ft.Icons.LOGOUT, color=TS_RED, tooltip="Leave Channel", on_click=self.leave_channel),
            ], spacing=2),
            bgcolor=TS_BG_LIGHT,
            padding=5,
            border=ft.border.only(bottom=ft.BorderSide(1, TS_BORDER)),
        )
        
        # ============ PANNEAU GAUCHE - Arborescence serveur ============
        
        # Serveur (IP)
        server_row = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.COMPUTER, color=TS_BLUE, size=16),
                ft.Text(f"{self.server_ip}:{self.server_port}", color=TS_TEXT_BLACK, size=12, weight=ft.FontWeight.BOLD),
            ], spacing=8),
            padding=ft.padding.only(left=5, top=8, bottom=8),
        )
        
        # Default Channel
        self.default_channel_row = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.LOCK_OPEN, color=TS_BLUE, size=14),
                ft.Text("Default Channel", color=TS_TEXT_BLACK, size=12),
            ], spacing=8),
            padding=ft.padding.only(left=25, top=5, bottom=5),
            bgcolor=None,
            border_radius=3,
            on_click=lambda e: self.join_channel("Default Channel"),
        )
        
        # Utilisateurs du Default Channel
        self.default_users_list = ft.Column(spacing=0)
        
        # Séparateur
        separator = ft.Container(
            content=ft.Divider(color=TS_BORDER, height=1),
            padding=ft.padding.only(left=20, right=10, top=10, bottom=5),
        )
        
        # Custom Channel - Header
        custom_header = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.FOLDER, color=TS_BLUE, size=14),
                ft.Text("Custom Channel", color=TS_TEXT_GRAY, size=11, italic=True),
            ], spacing=8),
            padding=ft.padding.only(left=25, top=5, bottom=5),
        )
        
        # Custom Channel - Mon channel (si créé)
        self.custom_channel_row = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.LOCK, color=TS_BLUE, size=14),
                ft.Text("", color=TS_TEXT_BLACK, size=12),
            ], spacing=8),
            padding=ft.padding.only(left=40, top=5, bottom=5),
            bgcolor=None,
            border_radius=3,
            visible=False,
            on_click=lambda e: self.join_channel(self.custom_channel_name) if self.custom_channel_name else None,
        )
        
        # Utilisateurs du Custom Channel
        self.custom_users_list = ft.Column(spacing=0)
        
        # Input pour créer/rejoindre un custom channel
        self.custom_input = ft.TextField(
            hint_text="Channel name...",
            hint_style=ft.TextStyle(color=TS_TEXT_GRAY, size=10),
            bgcolor=TS_BG_WHITE,
            border_color=TS_BORDER,
            focused_border_color=TS_BLUE,
            color=TS_TEXT_BLACK,
            height=32,
            text_size=11,
            content_padding=ft.padding.only(left=8, right=8),
            on_submit=self.join_custom_channel,
            expand=True,
        )
        
        self.join_custom_btn = ft.ElevatedButton(
            "Join",
            bgcolor=TS_BLUE,
            color="white",
            height=32,
            on_click=self.join_custom_channel,
        )
        
        custom_input_row = ft.Container(
            content=ft.Row([
                self.custom_input,
                self.join_custom_btn,
            ], spacing=5),
            padding=ft.padding.only(left=20, right=5, top=10),
        )
        
        # Assemblage panneau gauche
        self.server_tree = ft.Column([
            server_row,
            self.default_channel_row,
            self.default_users_list,
            separator,
            custom_header,
            self.custom_channel_row,
            self.custom_users_list,
            custom_input_row,
        ], spacing=0)
        
        left_panel = ft.Container(
            content=ft.Column([
                ft.Container(
                    content=self.server_tree,
                    bgcolor=TS_BG_WHITE,
                    expand=True,
                    padding=5,
                ),
            ], spacing=0),
            width=280,
            bgcolor=TS_BG_WHITE,
            border=ft.border.all(1, TS_BORDER),
        )
        
        # ============ PANNEAU DROIT - Infos ============
        
        # Infos utilisateur
        self.info_nickname = ft.Text(self.pseudo, color=TS_TEXT_BLACK, size=13, weight=ft.FontWeight.BOLD)
        self.info_channel = ft.Text("No channel", color=TS_TEXT_BLACK, size=12)
        self.info_users = ft.Text("0", color=TS_TEXT_BLACK, size=12)
        
        info_section = ft.Column([
            self._info_row("Nickname:", self.info_nickname),
            self._info_row("Channel:", self.info_channel),
            self._info_row("Users in channel:", self.info_users),
        ], spacing=8)
        
        right_panel = ft.Container(
            content=ft.Column([
                info_section,
            ], spacing=0),
            expand=True,
            bgcolor=TS_BG_WHITE,
            border=ft.border.all(1, TS_BORDER),
            padding=15,
        )
        
        # ============ PANNEAU BAS - Chat/Logs ============
        
        # Onglets
        self.tab_server = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.COMPUTER, color=TS_BLUE, size=14),
                ft.Text(f"{self.server_ip}", color=TS_TEXT_BLACK, size=11),
            ], spacing=5),
            bgcolor=TS_BG_WHITE,
            padding=ft.padding.only(left=10, right=10, top=5, bottom=5),
            border=ft.border.only(top=ft.BorderSide(1, TS_BORDER), left=ft.BorderSide(1, TS_BORDER), right=ft.BorderSide(1, TS_BORDER)),
            border_radius=ft.border_radius.only(top_left=5, top_right=5),
        )
        
        self.tab_channel = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.TAG, color=TS_BLUE, size=14),
                ft.Text("No channel", color=TS_TEXT_BLACK, size=11),
            ], spacing=5),
            bgcolor=TS_BG_LIGHT,
            padding=ft.padding.only(left=10, right=10, top=5, bottom=5),
            border_radius=ft.border_radius.only(top_left=5, top_right=5),
            visible=False,
        )
        
        tabs_row = ft.Row([self.tab_server, self.tab_channel], spacing=2)
        
        # Zone de logs/chat
        self.chat_list = ft.ListView(
            expand=True,
            spacing=1,
            auto_scroll=True,
            padding=5,
        )
        
        # Input message
        self.chat_input = ft.TextField(
            hint_text="Enter Chat Message...",
            hint_style=ft.TextStyle(color=TS_TEXT_GRAY),
            bgcolor=TS_BG_WHITE,
            border_color=TS_BORDER,
            focused_border_color=TS_BLUE,
            color=TS_TEXT_BLACK,
            expand=True,
            height=35,
            text_size=12,
            content_padding=ft.padding.only(left=10, right=10, top=5, bottom=5),
            on_submit=self.send_message,
        )
        
        bottom_panel = ft.Container(
            content=ft.Column([
                tabs_row,
                ft.Container(
                    content=self.chat_list,
                    bgcolor=TS_BG_WHITE,
                    expand=True,
                    border=ft.border.all(1, TS_BORDER),
                ),
                ft.Container(
                    content=self.chat_input,
                    padding=5,
                ),
            ], spacing=0),
            height=180,
            bgcolor=TS_BG_GRAY,
        )
        
        # ============ BARRE DE STATUT ============
        status_bar = ft.Container(
            content=ft.Row([
                ft.Container(expand=True),
                ft.Text(f"Connected as {self.pseudo}", color=TS_TEXT_GRAY, size=11),
            ], spacing=8),
            bgcolor=TS_BG_LIGHT,
            padding=ft.padding.only(left=10, right=10, top=3, bottom=3),
            border=ft.border.only(top=ft.BorderSide(1, TS_BORDER)),
        )
        
        # ============ ASSEMBLAGE FINAL ============
        top_area = ft.Row([
            left_panel,
            right_panel,
        ], spacing=5, expand=True)
        
        self.page.add(
            ft.Container(
                content=ft.Column([
                    toolbar,
                    ft.Container(
                        content=ft.Column([
                            top_area,
                            bottom_panel,
                        ], spacing=5),
                        padding=5,
                        expand=True,
                    ),
                    status_bar,
                ], spacing=0, expand=True),
                expand=True,
            )
        )
    
    def _info_row(self, label: str, value_widget):
        """Crée une ligne d'info."""
        return ft.Row([
            ft.Text(label, color=TS_TEXT_GRAY, size=12, width=110),
            value_widget,
        ], spacing=5)
    
    def _toolbar_icon(self, icon, color=None, tooltip=None, on_click=None):
        """Crée une icône de toolbar."""
        return ft.IconButton(
            icon=icon,
            icon_color=color or TS_TEXT_GRAY,
            icon_size=18,
            tooltip=tooltip,
            on_click=on_click,
            style=ft.ButtonStyle(
                padding=5,
                shape=ft.RoundedRectangleBorder(radius=2),
            ),
        )
    
    def toggle_mic(self, e):
        """Active/désactive le micro."""
        self.mic_muted = not self.mic_muted
        self.mic_btn.icon = ft.Icons.MIC_OFF if self.mic_muted else ft.Icons.MIC
        self.mic_btn.icon_color = TS_RED if self.mic_muted else TS_BLUE
        self.log_message("Microphone " + ("muted" if self.mic_muted else "unmuted"), TS_BLUE if self.mic_muted else TS_BLUE)
        self.page.update()
    
    def toggle_sound(self, e):
        """Active/désactive le son."""
        self.sound_muted = not self.sound_muted
        self.sound_btn.icon = ft.Icons.HEADSET_OFF if self.sound_muted else ft.Icons.HEADSET
        self.sound_btn.icon_color = TS_RED if self.sound_muted else TS_BLUE
        self.log_message("Sound " + ("muted" if self.sound_muted else "unmuted"), TS_BLUE if self.sound_muted else TS_BLUE)
        self.page.update()
    
    def leave_channel(self, e):
        """Quitte le channel actuel."""
        if not self.current_room:
            self.log_message("You are not in a channel", TS_RED)
            return
        
        self.sock.send(pack_message(LEAVE))
        old_room = self.current_room
        
        # Si c'était un custom channel, on le supprime de l'affichage
        if old_room != "Default Channel" and old_room == self.custom_channel_name:
            self.custom_channel_name = None
            self.custom_channel_row.visible = False
        
        self.current_room = None
        self.users_in_room.clear()
        self.tab_channel.visible = False
        self._refresh_ui()
        self.log_message(f'Left channel "{old_room}"', TS_BLUE)
    
    def _add_user_to_list(self, user: str, target_list: ft.Column):
        """Ajoute un utilisateur à une liste."""
        is_me = user == self.pseudo
        user_row = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.PERSON, color=TS_BLUE, size=12),
                ft.Text(
                    user,
                    color=TS_BLUE if is_me else TS_TEXT_BLACK,
                    size=11,
                    weight=ft.FontWeight.BOLD if is_me else None,
                ),
            ], spacing=5),
            padding=ft.padding.only(left=45, top=2, bottom=2),
        )
        target_list.controls.append(user_row)
    
    def _refresh_ui(self):
        """Rafraîchit l'affichage."""
        # Effacer les listes d'utilisateurs
        self.default_users_list.controls.clear()
        self.custom_users_list.controls.clear()
        
        # Mettre à jour les styles des channels
        is_default = self.current_room == "Default Channel"
        is_custom = self.current_room == self.custom_channel_name and self.custom_channel_name is not None
        
        # Default Channel
        self.default_channel_row.bgcolor = TS_BG_LIGHT if is_default else None
        self.default_channel_row.content.controls[0].color = TS_BLUE if is_default else TS_BLUE
        
        # Afficher les users dans Default Channel (depuis room_members)
        default_members = self.room_members.get("Default Channel", set())
        for user in sorted(default_members):
            self._add_user_to_list(user, self.default_users_list)
        
        # Custom Channel
        if self.custom_channel_name:
            self.custom_channel_row.visible = True
            self.custom_channel_row.content.controls[1].value = self.custom_channel_name
            self.custom_channel_row.bgcolor = TS_BG_LIGHT if is_custom else None
            self.custom_channel_row.content.controls[0].color = TS_BLUE if is_custom else TS_BLUE
            
            # Afficher les users dans Custom Channel (depuis room_members)
            custom_members = self.room_members.get(self.custom_channel_name, set())
            for user in sorted(custom_members):
                self._add_user_to_list(user, self.custom_users_list)
        else:
            self.custom_channel_row.visible = False
        
        # Infos - nombre d'utilisateurs dans le room actuel
        current_members = self.room_members.get(self.current_room, set()) if self.current_room else set()
        self.info_channel.value = self.current_room or "No channel"
        self.info_users.value = str(len(current_members))
        
        # Onglet channel
        if self.current_room:
            self.tab_channel.visible = True
            self.tab_channel.content.controls[1].value = self.current_room
        
        self.page.update()
    
    def join_channel(self, name: str):
        """Rejoint un canal."""
        if not self.connected or name == self.current_room:
            return
        
        # Si on quitte un custom channel pour aller ailleurs, on le supprime de l'affichage
        if self.current_room and self.current_room != "Default Channel" and self.current_room == self.custom_channel_name:
            self.custom_channel_name = None
            self.custom_channel_row.visible = False
            self.page.update()
        
        self._pending_room = name
        self.sock.send(pack_message(JOIN, pack_string(name)))
    
    def join_custom_channel(self, e):
        """Rejoint ou crée un custom channel."""
        name = self.custom_input.value.strip()
        if not name or not self.connected:
            return
        
        self.custom_channel_name = name
        self.custom_input.value = ""
        self.join_channel(name)
    
    def send_message(self, e):
        """Envoie un message."""
        msg = self.chat_input.value.strip()
        if not msg:
            return
        
        if self.current_room:
            self.sock.send(pack_message(MSG, pack_string(msg)))
        else:
            self.log_message("Join a channel first!", TS_RED)
        
        self.chat_input.value = ""
        self.page.update()
    
    def log_message(self, text: str, color=TS_TEXT_BLACK):
        """Ajoute un message de log."""
        now = datetime.datetime.now().strftime("%H:%M:%S")
        
        msg = ft.Row([
            ft.Text(f"<{now}>", color=TS_TEXT_GRAY, size=11),
            ft.Text(text, color=color, size=11),
        ], spacing=5)
        
        self.chat_list.controls.append(msg)
        self.page.update()
    
    def chat_message(self, pseudo: str, text: str):
        """Ajoute un message de chat."""
        now = datetime.datetime.now().strftime("%H:%M:%S")
        is_me = pseudo == self.pseudo
        is_system = pseudo == "Serveur"
        
        if is_system:
            # Message système : juste le timestamp et le texte
            msg = ft.Row([
                ft.Text(f"<{now}>", color=TS_TEXT_GRAY, size=11),
                ft.Text(text, color=TS_TEXT_GRAY, size=11),
            ], spacing=5)
        else:
            msg = ft.Row([
                ft.Text(f"<{now}>", color=TS_TEXT_GRAY, size=11),
                ft.Text(f"<{pseudo}>", color=TS_BLUE if is_me else TS_BLUE, size=11, weight=ft.FontWeight.BOLD),
                ft.Text(text, color=TS_TEXT_BLACK, size=11),
            ], spacing=5)
        
        self.chat_list.controls.append(msg)
        self.page.update()
    
    def receive_loop(self):
        """Boucle de réception des messages."""
        while self.connected:
            try:
                header = self.sock.recv(5)
                if not header:
                    # Connexion fermée par le serveur (kick)
                    self.connected = False
                    self.log_message("Vous avez été déconnecté du serveur", TS_RED)
                    self._show_disconnected()
                    break
                
                msg_type, length = unpack_header(header)
                payload = self.sock.recv(length) if length > 0 else b""
                
                if msg_type == MSG_BROADCAST:
                    pseudo = unpack_string(payload)
                    pseudo_len = 2 + len(pseudo.encode('utf-8'))
                    message = unpack_string(payload[pseudo_len:])
                    
                    # Gérer les messages système du Serveur
                    if pseudo == "Serveur":
                        # Parser les messages de connexion/déconnexion
                        if "s'est connecté" in message:
                            # Extraire le pseudo de "X s'est connecté"
                            user = message.replace(" s'est connecté", "")
                            if user and user != self.pseudo and user not in self.users_in_room:
                                self.users_in_room.add(user)
                                self._refresh_ui()
                        elif "a été kické" in message:
                            # Extraire le pseudo de "X a été kické"
                            user = message.replace(" a été kické", "")
                            if user in self.users_in_room:
                                self.users_in_room.discard(user)
                                self._refresh_ui()
                        elif "s'est déconnecté" in message:
                            # Extraire le pseudo de "X s'est déconnecté"
                            user = message.replace(" s'est déconnecté", "")
                            if user in self.users_in_room:
                                self.users_in_room.discard(user)
                                self._refresh_ui()
                    else:
                        # Message d'un autre utilisateur
                        if pseudo not in self.users_in_room and pseudo != self.pseudo:
                            self.users_in_room.add(pseudo)
                            self._refresh_ui()
                    
                    self.chat_message(pseudo, message)
                
                elif msg_type == JOIN_OK:
                    room = self._pending_room
                    if room:
                        self.current_room = room
                        self._pending_room = None
                    
                    self.users_in_room = {self.pseudo}
                    
                    self._refresh_ui()
                    self.log_message(f'Joined channel "{room}"', TS_BLUE)
                
                elif msg_type == ERROR:
                    code = payload[0]
                    error_msg = unpack_string(payload[1:])
                    self.log_message(f"Error: {error_msg}", TS_RED)
                
                elif msg_type == ROOM_UPDATE:
                    # Parse: [room_name][user][action]
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
                    
                    # Mettre à jour users_in_room si on est dans cette room
                    if room_name == self.current_room:
                        self.users_in_room = self.room_members[room_name].copy()
                    
                    self._refresh_ui()
                
            except Exception as ex:
                if self.connected:
                    self.connected = False
                    self.log_message(f"Déconnecté: {ex}", TS_RED)
                    self._show_disconnected()
                break
        
        self.connected = False
    
    def _show_disconnected(self):
        """Retourne à la page de connexion après un kick."""
        try:
            # Fermer la socket
            if self.sock:
                try:
                    self.sock.close()
                except:
                    pass
            
            # Réinitialiser l'état
            self.sock = None
            self.pseudo = None
            self.current_room = None
            self.users_in_room = set()
            
            # Vider la page et réafficher le dialog de connexion
            self.page.controls.clear()
            self.page.overlay.clear()
            self.show_connect_dialog()
            self.dialog_error.value = "Vous avez été kické du serveur"
            self.page.update()
        except:
            pass


def main(page: ft.Page):
    ChatClient(page)


if __name__ == "__main__":
    ft.app(target=main)
