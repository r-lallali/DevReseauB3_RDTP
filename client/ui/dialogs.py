"""
dialogs.py - Boîte de dialogue de connexion.

Gère l'affichage et la logique du dialog de connexion
au serveur (pseudo, IP, port).
"""

import flet as ft
from .theme import *


class ConnectDialog:
    """Dialog de connexion au serveur style TeamSpeak."""
    
    def __init__(self, page: ft.Page, on_connect_callback):
        """
        Args:
            page: Page Flet
            on_connect_callback: Fonction appelée avec (pseudo, ip, port) lors de la connexion
        """
        self.page = page
        self.on_connect = on_connect_callback
        self._create_dialog()
    
    def _create_dialog(self):
        """Crée les composants du dialog."""
        
        # Champ pseudo
        self.pseudo_field = ft.TextField(
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
        
        # Champ adresse serveur
        self.server_field = ft.TextField(
            label="Server Address",
            value=DEFAULT_SERVER_IP,
            bgcolor=TS_BG_WHITE,
            border_color=TS_BORDER,
            focused_border_color=TS_BLUE,
            color=TS_TEXT_BLACK,
            label_style=ft.TextStyle(color=TS_TEXT_GRAY),
            width=200,
            height=50,
        )
        
        # Champ port
        self.port_field = ft.TextField(
            label="Port",
            value=str(DEFAULT_SERVER_PORT),
            bgcolor=TS_BG_WHITE,
            border_color=TS_BORDER,
            focused_border_color=TS_BLUE,
            color=TS_TEXT_BLACK,
            label_style=ft.TextStyle(color=TS_TEXT_GRAY),
            width=70,
            height=50,
        )
        
        # Message d'erreur
        self.error_text = ft.Text("", color=TS_RED, size=12)
        
        # Dialog principal
        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.icons.COMPUTER, color=TS_BLUE, size=24),
                ft.Text("Connect to Server", color=TS_TEXT_BLACK, 
                       weight=ft.FontWeight.BOLD, size=16),
            ], spacing=10),
            bgcolor=TS_BG_GRAY,
            content=ft.Container(
                content=ft.Column([
                    ft.Row([self.server_field, self.port_field], spacing=10),
                    self.pseudo_field,
                    self.error_text,
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
                    on_click=self._handle_connect,
                    bgcolor=TS_BLUE,
                    color="white",
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
    
    def _handle_connect(self, e):
        """Valide les champs et appelle le callback de connexion."""
        pseudo = self.pseudo_field.value.strip()
        ip = self.server_field.value.strip()
        
        # Validation du pseudo
        if not pseudo:
            self.show_error("Please enter a nickname")
            return
        
        # Validation du port
        try:
            port = int(self.port_field.value.strip())
        except ValueError:
            self.show_error("Invalid port number")
            return
        
        # Appeler le callback de connexion
        self.on_connect(pseudo, ip, port)
    
    def show(self):
        """Affiche le dialog."""
        self.page.overlay.append(self.dialog)
        self.dialog.open = True
        self.page.update()
    
    def close(self):
        """Ferme le dialog."""
        self.dialog.open = False
        self.page.update()
    
    def show_error(self, message: str):
        """Affiche un message d'erreur."""
        self.error_text.value = message
        self.page.update()
    
    def clear_error(self):
        """Efface le message d'erreur."""
        self.error_text.value = ""
        self.page.update()
