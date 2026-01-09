"""
info_panel.py - Panneau d'informations à droite.

Affiche les informations de l'utilisateur : pseudo, channel actuel,
nombre d'utilisateurs dans le channel.
"""

import flet as ft
from .theme import *


class InfoPanel:
    """Panneau d'informations utilisateur."""
    
    def __init__(self, pseudo: str):
        """
        Args:
            pseudo: Pseudo de l'utilisateur connecté
        """
        self.pseudo = pseudo
        self._create_components()
    
    def _create_components(self):
        """Crée les composants du panneau."""
        
        # Labels d'info
        self.nickname_text = ft.Text(
            self.pseudo, 
            color=TS_TEXT_BLACK, 
            size=13, 
            weight=ft.FontWeight.BOLD
        )
        
        self.channel_text = ft.Text(
            "No channel", 
            color=TS_TEXT_BLACK, 
            size=12
        )
        
        self.users_text = ft.Text(
            "0", 
            color=TS_TEXT_BLACK, 
            size=12
        )
        
        # Section d'infos
        info_section = ft.Column([
            self._create_info_row("Nickname:", self.nickname_text),
            self._create_info_row("Channel:", self.channel_text),
            self._create_info_row("Users in channel:", self.users_text),
        ], spacing=8)
        
        # Container principal
        self.container = ft.Container(
            content=ft.Column([info_section], spacing=0),
            expand=True,
            bgcolor=TS_BG_WHITE,
            border=ft.border.all(1, TS_BORDER),
            padding=15,
        )
    
    def _create_info_row(self, label: str, value_widget: ft.Text) -> ft.Row:
        """Crée une ligne d'information."""
        return ft.Row([
            ft.Text(label, color=TS_TEXT_GRAY, size=12, width=110),
            value_widget,
        ], spacing=5)
    
    def update_info(self, channel: str = None, user_count: int = 0):
        """
        Met à jour les informations affichées.
        
        Args:
            channel: Nom du channel actuel (ou None)
            user_count: Nombre d'utilisateurs dans le channel
        """
        self.channel_text.value = channel or "No channel"
        self.users_text.value = str(user_count)
    
    def get_widget(self) -> ft.Container:
        """Retourne le widget à ajouter à la page."""
        return self.container
