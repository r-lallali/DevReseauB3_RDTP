"""
server_tree.py - Panneau gauche avec l'arborescence serveur.

Affiche la hiérarchie : Serveur > Channels > Utilisateurs
"""

import flet as ft
from .theme import *


class ServerTree:
    """Arborescence du serveur avec les channels et utilisateurs."""
    
    def __init__(self, server_ip: str, server_port: int, 
                 on_join_channel, on_join_custom_channel):
        """
        Args:
            server_ip: Adresse IP du serveur
            server_port: Port du serveur
            on_join_channel: Callback(channel_name) pour rejoindre un channel
            on_join_custom_channel: Callback(channel_name) pour créer/rejoindre un custom channel
        """
        self.server_ip = server_ip
        self.server_port = server_port
        self.on_join_channel = on_join_channel
        self.on_join_custom_channel = on_join_custom_channel
        
        # État
        self.current_room = None
        self.custom_channel_name = None
        
        self._create_components()
    
    def _create_components(self):
        """Crée les composants de l'arborescence."""
        
        # En-tête serveur
        self.server_row = ft.Container(
            content=ft.Row([
                ft.Icon(ft.icons.COMPUTER, color=TS_BLUE, size=16),
                ft.Text(
                    f"{self.server_ip}:{self.server_port}",
                    color=TS_TEXT_BLACK, size=12, weight=ft.FontWeight.BOLD
                ),
            ], spacing=8),
            padding=ft.padding.only(left=5, top=8, bottom=8),
        )
        
        # Default Channel (toujours visible)
        self.default_channel_row = ft.Container(
            content=ft.Row([
                ft.Icon(ft.icons.LOCK_OPEN, color=TS_BLUE, size=14),
                ft.Text("Default Channel", color=TS_TEXT_BLACK, size=12),
            ], spacing=8),
            padding=ft.padding.only(left=25, top=5, bottom=5),
            bgcolor=None,
            border_radius=3,
            on_click=lambda e: self.on_join_channel("Default Channel"),
        )
        
        # Liste des utilisateurs du Default Channel
        self.default_users_list = ft.Column(spacing=0)
        
        # Séparateur
        self.separator = ft.Container(
            content=ft.Divider(color=TS_BORDER, height=1),
            padding=ft.padding.only(left=20, right=10, top=10, bottom=5),
        )
        
        # En-tête Custom Channels
        self.custom_header = ft.Container(
            content=ft.Row([
                ft.Icon(ft.icons.FOLDER, color=TS_BLUE, size=14),
                ft.Text("Custom Channel", color=TS_TEXT_GRAY, size=11, italic=True),
            ], spacing=8),
            padding=ft.padding.only(left=25, top=5, bottom=5),
        )
        
        # Custom Channel actuel (visible seulement si créé)
        self.custom_channel_row = ft.Container(
            content=ft.Row([
                ft.Icon(ft.icons.LOCK, color=TS_BLUE, size=14),
                ft.Text("", color=TS_TEXT_BLACK, size=12),
            ], spacing=8),
            padding=ft.padding.only(left=40, top=5, bottom=5),
            bgcolor=None,
            border_radius=3,
            visible=False,
            on_click=lambda e: self._on_custom_click(),
        )
        
        # Liste des utilisateurs du Custom Channel
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
            on_submit=self._handle_join_custom,
            expand=True,
        )
        
        self.join_btn = ft.ElevatedButton(
            "Join",
            bgcolor=TS_BLUE,
            color="white",
            height=32,
            on_click=self._handle_join_custom,
        )
        
        custom_input_row = ft.Container(
            content=ft.Row([
                self.custom_input,
                self.join_btn,
            ], spacing=5),
            padding=ft.padding.only(left=20, right=5, top=10),
        )
        
        # Assemblage
        self.tree = ft.Column([
            self.server_row,
            self.default_channel_row,
            self.default_users_list,
            self.separator,
            self.custom_header,
            self.custom_channel_row,
            self.custom_users_list,
            custom_input_row,
        ], spacing=0)
        
        # Container principal
        self.container = ft.Container(
            content=ft.Column([
                ft.Container(
                    content=self.tree,
                    bgcolor=TS_BG_WHITE,
                    expand=True,
                    padding=5,
                ),
            ], spacing=0),
            width=280,
            bgcolor=TS_BG_WHITE,
            border=ft.border.all(1, TS_BORDER),
        )
    
    def _on_custom_click(self):
        """Gère le clic sur le custom channel."""
        if self.custom_channel_name:
            self.on_join_channel(self.custom_channel_name)
    
    def _handle_join_custom(self, e):
        """Gère la création/rejoint d'un custom channel."""
        name = self.custom_input.value.strip()
        if name:
            self.custom_input.value = ""
            self.on_join_custom_channel(name)
    
    def _add_user_to_list(self, user: str, target_list: ft.Column, is_me: bool = False):
        """Ajoute un utilisateur à une liste."""
        user_row = ft.Container(
            content=ft.Row([
                ft.Icon(ft.icons.PERSON, color=TS_BLUE, size=12),
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
    
    def update_display(self, current_room: str, custom_channel_name: str,
                       room_members: dict, my_pseudo: str):
        """
        Met à jour l'affichage de l'arborescence.
        
        Args:
            current_room: Nom du channel actuel (ou None)
            custom_channel_name: Nom du custom channel (ou None)
            room_members: Dict room_name -> set de membres
            my_pseudo: Mon pseudo (pour le mettre en surbrillance)
        """
        self.current_room = current_room
        self.custom_channel_name = custom_channel_name
        
        # Effacer les listes
        self.default_users_list.controls.clear()
        self.custom_users_list.controls.clear()
        
        # Style du Default Channel
        is_default = current_room == "Default Channel"
        self.default_channel_row.bgcolor = TS_BG_LIGHT if is_default else None
        
        # Utilisateurs du Default Channel
        default_members = room_members.get("Default Channel", set())
        for user in sorted(default_members):
            self._add_user_to_list(user, self.default_users_list, user == my_pseudo)
        
        # Custom Channel
        if custom_channel_name:
            self.custom_channel_row.visible = True
            self.custom_channel_row.content.controls[1].value = custom_channel_name
            
            is_custom = current_room == custom_channel_name
            self.custom_channel_row.bgcolor = TS_BG_LIGHT if is_custom else None
            
            # Utilisateurs du Custom Channel
            custom_members = room_members.get(custom_channel_name, set())
            for user in sorted(custom_members):
                self._add_user_to_list(user, self.custom_users_list, user == my_pseudo)
        else:
            self.custom_channel_row.visible = False
    
    def set_custom_channel(self, name: str):
        """Définit le nom du custom channel."""
        self.custom_channel_name = name
    
    def clear_custom_channel(self):
        """Efface le custom channel."""
        self.custom_channel_name = None
        self.custom_channel_row.visible = False
    
    def get_widget(self) -> ft.Container:
        """Retourne le widget à ajouter à la page."""
        return self.container
