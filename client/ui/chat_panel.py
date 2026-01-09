"""
chat_panel.py - Panneau de chat en bas de la fenêtre.

Affiche les messages et logs, avec un champ de saisie.
"""

import flet as ft
import datetime
from .theme import *


class ChatPanel:
    """Panneau de chat avec logs et saisie de messages."""
    
    def __init__(self, server_ip: str, on_send_message):
        """
        Args:
            server_ip: Adresse IP du serveur (pour l'onglet)
            on_send_message: Callback(message) appelé lors de l'envoi d'un message
        """
        self.server_ip = server_ip
        self.on_send_message = on_send_message
        self._create_components()
    
    def _create_components(self):
        """Crée les composants du panneau."""
        
        # Onglet serveur
        self.tab_server = ft.Container(
            content=ft.Row([
                ft.Icon(ft.icons.COMPUTER, color=TS_BLUE, size=14),
                ft.Text(self.server_ip, color=TS_TEXT_BLACK, size=11),
            ], spacing=5),
            bgcolor=TS_BG_WHITE,
            padding=ft.padding.only(left=10, right=10, top=5, bottom=5),
            border=ft.border.only(
                top=ft.BorderSide(1, TS_BORDER),
                left=ft.BorderSide(1, TS_BORDER),
                right=ft.BorderSide(1, TS_BORDER)
            ),
            border_radius=ft.border_radius.only(top_left=5, top_right=5),
        )
        
        # Onglet channel (masqué par défaut)
        self.tab_channel = ft.Container(
            content=ft.Row([
                ft.Icon(ft.icons.TAG, color=TS_BLUE, size=14),
                ft.Text("No channel", color=TS_TEXT_BLACK, size=11),
            ], spacing=5),
            bgcolor=TS_BG_LIGHT,
            padding=ft.padding.only(left=10, right=10, top=5, bottom=5),
            border_radius=ft.border_radius.only(top_left=5, top_right=5),
            visible=False,
        )
        
        tabs_row = ft.Row([self.tab_server, self.tab_channel], spacing=2)
        
        # Liste des messages
        self.chat_list = ft.ListView(
            expand=True,
            spacing=1,
            auto_scroll=True,
            padding=5,
        )
        
        # Champ de saisie
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
            on_submit=self._handle_send,
        )
        
        # Container principal
        self.container = ft.Container(
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
    
    def _handle_send(self, e):
        """Gère l'envoi d'un message."""
        msg = self.chat_input.value.strip()
        if msg:
            self.chat_input.value = ""
            self.on_send_message(msg)
    
    def _get_timestamp(self) -> str:
        """Retourne le timestamp actuel formaté."""
        return datetime.datetime.now().strftime("%H:%M:%S")
    
    def add_log(self, text: str, color: str = TS_TEXT_BLACK):
        """
        Ajoute un message de log (système).
        
        Args:
            text: Texte du message
            color: Couleur du texte
        """
        msg = ft.Row([
            ft.Text(f"<{self._get_timestamp()}>", color=TS_TEXT_GRAY, size=11),
            ft.Text(text, color=color, size=11),
        ], spacing=5)
        
        self.chat_list.controls.append(msg)
    
    def add_chat_message(self, pseudo: str, text: str, is_me: bool = False, is_system: bool = False):
        """
        Ajoute un message de chat.
        
        Args:
            pseudo: Pseudo de l'expéditeur
            text: Contenu du message
            is_me: True si c'est mon propre message
            is_system: True si c'est un message système (ex: "X s'est connecté")
        """
        timestamp = self._get_timestamp()
        
        if is_system:
            # Message système en gris
            msg = ft.Row([
                ft.Text(f"<{timestamp}>", color=TS_TEXT_GRAY, size=11),
                ft.Text(text, color=TS_TEXT_GRAY, size=11),
            ], spacing=5)
        else:
            # Message utilisateur
            msg = ft.Row([
                ft.Text(f"<{timestamp}>", color=TS_TEXT_GRAY, size=11),
                ft.Text(f"<{pseudo}>", color=TS_BLUE, size=11, weight=ft.FontWeight.BOLD),
                ft.Text(text, color=TS_TEXT_BLACK, size=11),
            ], spacing=5)
        
        self.chat_list.controls.append(msg)
    
    def update_channel_tab(self, channel_name: str = None):
        """
        Met à jour l'onglet du channel.
        
        Args:
            channel_name: Nom du channel (ou None pour masquer)
        """
        if channel_name:
            self.tab_channel.visible = True
            self.tab_channel.content.controls[1].value = channel_name
        else:
            self.tab_channel.visible = False
    
    def clear(self):
        """Efface tous les messages."""
        self.chat_list.controls.clear()
    
    def get_widget(self) -> ft.Container:
        """Retourne le widget à ajouter à la page."""
        return self.container
