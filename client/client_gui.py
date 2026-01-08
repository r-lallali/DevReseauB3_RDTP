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

# Couleurs style TeamSpeak 3 (thème clair comme l'original)
TS_BG_WHITE = "#ffffff"
TS_BG_GRAY = "#f0f0f0"
TS_BG_LIGHT = "#e8e8e8"
TS_BORDER = "#acacac"
TS_HEADER_BG = "#d4d4d4"
TS_TEXT_BLACK = "#000000"
TS_TEXT_GRAY = "#666666"
TS_BLUE = "#0066cc"
TS_GREEN = "#008000"
TS_RED = "#cc0000"
TS_ORANGE = "#ff6600"
TS_YELLOW = "#999900"


class ChatClient:
    def __init__(self, page: ft.Page):
        self.page = page
        self.sock = None
        self.pseudo = None
        self.server_name = "RDTP Server"
        self.current_room = None
        self.connected = False
        self.users_in_room = set()
        self.all_users = set()  # Tous les utilisateurs du serveur
        self.channels = {}  # nom_channel -> set(users)
        self._pending_room = None
        
        # Configuration de la page
        self.page.title = "TeamSpeak 3"
        self.page.window.width = 850
        self.page.window.height = 600
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
            height=45,
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
            height=45,
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
            height=45,
        )
        
        self.dialog_error = ft.Text("", color=TS_RED, size=12)
        
        self.connect_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.icons.CONNECT_WITHOUT_CONTACT, color=TS_BLUE, size=24),
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
                self.server_name = f"RDTP Server ({ip}:{port})"
                self.all_users.add(pseudo)
                
                # Fermer le dialog et afficher l'UI principale
                self.connect_dialog.open = False
                self.page.update()
                
                self.setup_main_ui()
                
                # Lancer le thread de réception
                threading.Thread(target=self.receive_loop, daemon=True).start()
                
                self.log_message(f'"{pseudo}" connected', TS_GREEN)
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
        toolbar = ft.Container(
            content=ft.Row([
                self._toolbar_icon(ft.icons.BOOKMARK),
                self._toolbar_icon(ft.icons.BOOKMARK_BORDER),
                ft.VerticalDivider(width=1, color=TS_BORDER),
                self._toolbar_icon(ft.icons.ARROW_BACK),
                self._toolbar_icon(ft.icons.ARROW_FORWARD),
                self._toolbar_icon(ft.icons.HOME),
                ft.VerticalDivider(width=1, color=TS_BORDER),
                self._toolbar_icon(ft.icons.MIC, color=TS_GREEN),
                self._toolbar_icon(ft.icons.HEADSET, color=TS_GREEN),
                ft.VerticalDivider(width=1, color=TS_BORDER),
                self._toolbar_icon(ft.icons.SETTINGS),
                ft.Container(expand=True),
                self._toolbar_icon(ft.icons.HELP_OUTLINE),
            ], spacing=2),
            bgcolor=TS_BG_LIGHT,
            padding=5,
            border=ft.border.only(bottom=ft.BorderSide(1, TS_BORDER)),
        )
        
        # ============ PANNEAU GAUCHE - Arborescence serveur & utilisateurs ============
        
        # Header "Server Rules"
        server_rules_header = ft.Container(
            content=ft.Text("Server Rules", color=TS_TEXT_GRAY, size=11),
            padding=ft.padding.only(left=10, top=5, bottom=5),
            bgcolor=TS_BG_LIGHT,
        )
        
        # Arborescence du serveur
        self.server_tree = ft.Column(spacing=0)
        self._build_server_tree()
        
        left_panel = ft.Container(
            content=ft.Column([
                server_rules_header,
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
        
        # ============ PANNEAU DROIT - Infos serveur ============
        
        # Logo TeamSpeak
        ts_logo = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("team", color=TS_TEXT_BLACK, size=20, weight=ft.FontWeight.BOLD),
                    ft.Text("speak", color=TS_BLUE, size=20, weight=ft.FontWeight.BOLD),
                ], spacing=0),
                ft.Text("COMMUNICATION SYSTEM", color=TS_TEXT_GRAY, size=8),
            ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.START),
            padding=10,
        )
        
        # Infos du serveur
        self.info_name = ft.Text(self.server_name, color=TS_TEXT_BLACK, size=12)
        self.info_address = ft.Text(f"{SERVER_IP}:{SERVER_PORT}", color=TS_TEXT_BLACK, size=12)
        self.info_clients = ft.Text("1 / 100", color=TS_TEXT_BLACK, size=12)
        self.info_channels = ft.Text("0", color=TS_TEXT_BLACK, size=12)
        self.info_uptime = ft.Text("0 hours, 0 minutes", color=TS_TEXT_BLACK, size=12)
        
        info_grid = ft.Column([
            self._info_row("Name:", self.info_name),
            self._info_row("Address:", self.info_address),
            self._info_row("Current Channels:", self.info_channels),
            self._info_row("Current Clients:", self.info_clients),
            self._info_row("Uptime:", self.info_uptime),
            ft.Container(height=10),
            ft.TextButton("Refresh", on_click=self.refresh_info),
        ], spacing=5)
        
        # Slogan
        slogan = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("When a ", color=TS_TEXT_GRAY, size=11),
                    ft.Text("word", color=TS_RED, size=14, weight=ft.FontWeight.BOLD),
                    ft.Text(" is worth a", color=TS_TEXT_GRAY, size=11),
                ], spacing=2),
                ft.Row([
                    ft.Text("thousand ", color=TS_TEXT_GRAY, size=11),
                    ft.Text("keystrokes...", color=TS_BLUE, size=14, weight=ft.FontWeight.BOLD, italic=True),
                ], spacing=2),
            ], spacing=0),
            padding=10,
        )
        
        right_panel = ft.Container(
            content=ft.Column([
                ft.Row([ts_logo, ft.Container(expand=True), slogan]),
                ft.Divider(color=TS_BORDER, height=1),
                ft.Container(content=info_grid, padding=15, expand=True),
            ], spacing=0),
            expand=True,
            bgcolor=TS_BG_WHITE,
            border=ft.border.all(1, TS_BORDER),
        )
        
        # ============ PANNEAU BAS - Chat/Logs ============
        
        # Onglets
        self.tab_server = ft.Container(
            content=ft.Row([
                ft.Icon(ft.icons.DNS, color=TS_GREEN, size=14),
                ft.Text(f"RDTP Server", color=TS_TEXT_BLACK, size=11),
            ], spacing=5),
            bgcolor=TS_BG_WHITE,
            padding=ft.padding.only(left=10, right=10, top=5, bottom=5),
            border=ft.border.only(top=ft.BorderSide(1, TS_BORDER), left=ft.BorderSide(1, TS_BORDER), right=ft.BorderSide(1, TS_BORDER)),
            border_radius=ft.border_radius.only(top_left=5, top_right=5),
        )
        
        self.tab_channel = ft.Container(
            content=ft.Row([
                ft.Icon(ft.icons.TAG, color=TS_YELLOW, size=14),
                ft.Text("No channel", color=TS_TEXT_BLACK, size=11),
                ft.IconButton(ft.icons.CLOSE, icon_size=12, icon_color=TS_TEXT_GRAY),
            ], spacing=5),
            bgcolor=TS_BG_LIGHT,
            padding=ft.padding.only(left=10, right=5, top=5, bottom=5),
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
            hint_text="",
            bgcolor=TS_BG_WHITE,
            border_color=TS_BORDER,
            focused_border_color=TS_BLUE,
            color=TS_TEXT_BLACK,
            expand=True,
            height=35,
            text_size=12,
            content_padding=ft.padding.only(left=10, right=10, top=5, bottom=5),
            on_submit=self.send_message,
            prefix=ft.Container(
                content=ft.Text("A", color=TS_TEXT_BLACK, size=14, weight=ft.FontWeight.BOLD),
                padding=ft.padding.only(right=10),
            ),
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
            height=200,
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
        # Zone haute : gauche + droite
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
    
    def _toolbar_icon(self, icon, color=None):
        """Crée une icône de toolbar."""
        return ft.IconButton(
            icon=icon,
            icon_color=color or TS_TEXT_GRAY,
            icon_size=18,
            style=ft.ButtonStyle(
                padding=5,
                shape=ft.RoundedRectangleBorder(radius=2),
            ),
        )
    
    def _info_row(self, label: str, value_widget):
        """Crée une ligne d'info."""
        return ft.Row([
            ft.Text(label, color=TS_TEXT_GRAY, size=12, weight=ft.FontWeight.BOLD, width=120),
            value_widget,
        ], spacing=10)
    
    def _build_server_tree(self):
        """Construit l'arborescence du serveur."""
        self.server_tree.controls.clear()
        
        # Icône serveur avec nom
        server_row = ft.Container(
            content=ft.Row([
                ft.Icon(ft.icons.DNS, color=TS_GREEN, size=16),
                ft.Text(self.server_name, color=TS_TEXT_BLACK, size=12, weight=ft.FontWeight.BOLD),
                ft.Icon(ft.icons.HOME, color=TS_BLUE, size=12),
                ft.Icon(ft.icons.LOCK_OPEN, color=TS_GREEN, size=12),
            ], spacing=5),
            padding=ft.padding.only(left=5, top=3, bottom=3),
            on_click=lambda e: None,
        )
        self.server_tree.controls.append(server_row)
        
        # Canaux par défaut
        default_channels = ["Lobby", "General", "Gaming", "Music", "AFK"]
        for ch in default_channels:
            self._add_channel_to_tree(ch)
        
        # Input nouveau channel
        new_channel_row = ft.Container(
            content=ft.Row([
                ft.Container(width=20),
                ft.TextField(
                    hint_text="+ New channel...",
                    hint_style=ft.TextStyle(color=TS_TEXT_GRAY, size=11),
                    bgcolor="transparent",
                    border_color="transparent",
                    focused_border_color=TS_BLUE,
                    color=TS_TEXT_BLACK,
                    height=25,
                    text_size=11,
                    content_padding=ft.padding.only(left=5),
                    on_submit=self.create_channel,
                    expand=True,
                ),
            ], spacing=0),
            padding=ft.padding.only(left=10),
        )
        self.server_tree.controls.append(new_channel_row)
        
        self.page.update()
    
    def _add_channel_to_tree(self, name: str):
        """Ajoute un canal à l'arborescence."""
        is_current = name == self.current_room
        
        # Container du channel
        channel_container = ft.Container(
            content=ft.Column([
                # Ligne du channel
                ft.Container(
                    content=ft.Row([
                        ft.Icon(
                            ft.icons.VOLUME_UP if is_current else ft.icons.FOLDER_OPEN,
                            color=TS_YELLOW if is_current else TS_TEXT_GRAY,
                            size=14
                        ),
                        ft.Text(
                            name,
                            color=TS_TEXT_BLACK,
                            size=12,
                            weight=ft.FontWeight.BOLD if is_current else None
                        ),
                        ft.Text(
                            "(Channel is moderated)" if name == "Lobby" else "",
                            color=TS_TEXT_GRAY,
                            size=10,
                            italic=True
                        ),
                    ], spacing=5),
                    padding=ft.padding.only(left=20, top=2, bottom=2),
                    bgcolor=TS_BG_LIGHT if is_current else None,
                    border_radius=3,
                    on_click=lambda e, n=name: self.join_channel(n),
                ),
            ], spacing=0),
            data=name,
        )
        
        # Si c'est le channel actuel, afficher les utilisateurs
        if is_current and self.current_room:
            users_col = channel_container.content
            for user in sorted(self.users_in_room):
                is_me = user == self.pseudo
                user_row = ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.icons.CIRCLE, color=TS_GREEN, size=8),
                        ft.Text(
                            user,
                            color=TS_GREEN if is_me else TS_TEXT_BLACK,
                            size=11,
                            weight=ft.FontWeight.BOLD if is_me else None,
                        ),
                    ], spacing=5),
                    padding=ft.padding.only(left=40, top=1, bottom=1),
                )
                users_col.controls.append(user_row)
        
        # Insérer avant le "new channel" input
        insert_pos = len(self.server_tree.controls) - 1
        self.server_tree.controls.insert(insert_pos, channel_container)
    
    def _refresh_tree(self):
        """Rafraîchit l'arborescence."""
        # Sauvegarder le new channel input
        new_channel_input = self.server_tree.controls[-1]
        
        # Reconstruire
        self.server_tree.controls.clear()
        
        # Server header
        server_row = ft.Container(
            content=ft.Row([
                ft.Icon(ft.icons.DNS, color=TS_GREEN, size=16),
                ft.Text(self.server_name, color=TS_TEXT_BLACK, size=12, weight=ft.FontWeight.BOLD),
                ft.Icon(ft.icons.HOME, color=TS_BLUE, size=12),
            ], spacing=5),
            padding=ft.padding.only(left=5, top=3, bottom=3),
        )
        self.server_tree.controls.append(server_row)
        
        # Channels
        default_channels = ["Lobby", "General", "Gaming", "Music", "AFK"]
        for ch in default_channels:
            self._add_channel_to_tree(ch)
        
        # Remettre le new channel input
        self.server_tree.controls.append(new_channel_input)
        
        self.page.update()
    
    def create_channel(self, e):
        """Crée un nouveau canal."""
        name = e.control.value.strip()
        if not name:
            return
        
        e.control.value = ""
        self._add_channel_to_tree(name)
        self.page.update()
        
        # Rejoindre automatiquement
        self.join_channel(name)
    
    def join_channel(self, name: str):
        """Rejoint un canal."""
        if not self.connected or name == self.current_room:
            return
        
        self._pending_room = name
        self.sock.send(pack_message(JOIN, pack_string(name)))
    
    def send_message(self, e):
        """Envoie un message."""
        msg = self.chat_input.value.strip()
        if not msg:
            return
        
        if self.current_room:
            self.sock.send(pack_message(MSG, pack_string(msg)))
        
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
        
        msg = ft.Row([
            ft.Text(f"<{now}>", color=TS_TEXT_GRAY, size=11),
            ft.Text(f"<{pseudo}>", color=TS_BLUE if is_me else TS_GREEN, size=11, weight=ft.FontWeight.BOLD),
            ft.Text(text, color=TS_TEXT_BLACK, size=11),
        ], spacing=5)
        
        self.chat_list.controls.append(msg)
        self.page.update()
    
    def refresh_info(self, e=None):
        """Rafraîchit les infos du serveur."""
        self.info_clients.value = f"{len(self.all_users)} / 100"
        self.info_channels.value = "5"
        self.page.update()
    
    def receive_loop(self):
        """Boucle de réception des messages."""
        while self.connected:
            try:
                header = self.sock.recv(5)
                if not header:
                    break
                
                msg_type, length = unpack_header(header)
                payload = self.sock.recv(length) if length > 0 else b""
                
                if msg_type == MSG_BROADCAST:
                    pseudo = unpack_string(payload)
                    pseudo_len = 2 + len(pseudo.encode('utf-8'))
                    message = unpack_string(payload[pseudo_len:])
                    
                    # Ajouter l'utilisateur à la liste si nouveau
                    if pseudo not in self.users_in_room:
                        self.users_in_room.add(pseudo)
                        self.all_users.add(pseudo)
                        self._refresh_tree()
                        self.refresh_info()
                    
                    self.chat_message(pseudo, message)
                
                elif msg_type == JOIN_OK:
                    room = self._pending_room
                    if room:
                        self.current_room = room
                        self._pending_room = None
                    
                    self.users_in_room = {self.pseudo}
                    
                    # Mettre à jour l'onglet du channel
                    self.tab_channel.content.controls[1].value = room
                    self.tab_channel.visible = True
                    
                    self._refresh_tree()
                    self.log_message(f'Joined channel "{room}"', TS_BLUE)
                    self.page.update()
                
                elif msg_type == ERROR:
                    code = payload[0]
                    error_msg = unpack_string(payload[1:])
                    self.log_message(f"Error: {error_msg}", TS_RED)
                
            except Exception as ex:
                if self.connected:
                    self.log_message(f"Disconnected: {ex}", TS_RED)
                break
        
        self.connected = False


def main(page: ft.Page):
    ChatClient(page)


if __name__ == "__main__":
    ft.app(target=main)
