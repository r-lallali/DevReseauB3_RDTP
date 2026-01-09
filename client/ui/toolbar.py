"""
toolbar.py - Barre d'outils en haut de la fenêtre.

Contient les boutons : mute micro, mute son, quitter le channel.
"""

import flet as ft
from .theme import *


class Toolbar:
    """Barre d'outils avec les contrôles audio et de navigation."""
    
    def __init__(self, on_toggle_mic, on_toggle_sound, on_leave_channel):
        """
        Args:
            on_toggle_mic: Callback pour mute/unmute le micro
            on_toggle_sound: Callback pour mute/unmute le son
            on_leave_channel: Callback pour quitter le channel
        """
        self.on_toggle_mic = on_toggle_mic
        self.on_toggle_sound = on_toggle_sound
        self.on_leave_channel = on_leave_channel
        
        # État des boutons
        self.mic_muted = False
        self.sound_muted = False
        
        self._create_components()
    
    def _create_components(self):
        """Crée les composants de la toolbar."""
        
        # Bouton micro
        self.mic_btn = self._create_icon_button(
            ft.icons.MIC, 
            color=TS_BLUE,
            tooltip="Mute Microphone",
            on_click=self._handle_mic_click
        )
        
        # Bouton son
        self.sound_btn = self._create_icon_button(
            ft.icons.HEADSET,
            color=TS_BLUE,
            tooltip="Mute Sound",
            on_click=self._handle_sound_click
        )
        
        # Bouton quitter
        self.leave_btn = self._create_icon_button(
            ft.icons.LOGOUT,
            color=TS_RED,
            tooltip="Leave Channel",
            on_click=lambda e: self.on_leave_channel()
        )
        
        # Container principal
        self.container = ft.Container(
            content=ft.Row([
                self.mic_btn,
                self.sound_btn,
                ft.VerticalDivider(width=1, color=TS_BORDER),
                self.leave_btn,
            ], spacing=2),
            bgcolor=TS_BG_LIGHT,
            padding=5,
            border=ft.border.only(bottom=ft.BorderSide(1, TS_BORDER)),
        )
    
    def _create_icon_button(self, icon, color, tooltip, on_click):
        """Crée un bouton icône standardisé."""
        return ft.IconButton(
            icon=icon,
            icon_color=color,
            icon_size=18,
            tooltip=tooltip,
            on_click=on_click,
            style=ft.ButtonStyle(
                padding=5,
                shape=ft.RoundedRectangleBorder(radius=2),
            ),
        )
    
    def _handle_mic_click(self, e):
        """Gère le clic sur le bouton micro."""
        self.mic_muted = not self.mic_muted
        self.mic_btn.icon = ft.icons.MIC_OFF if self.mic_muted else ft.icons.MIC
        self.mic_btn.icon_color = TS_RED if self.mic_muted else TS_BLUE
        self.on_toggle_mic(self.mic_muted)
    
    def _handle_sound_click(self, e):
        """Gère le clic sur le bouton son."""
        self.sound_muted = not self.sound_muted
        self.sound_btn.icon = ft.icons.HEADSET_OFF if self.sound_muted else ft.icons.HEADSET
        self.sound_btn.icon_color = TS_RED if self.sound_muted else TS_BLUE
        self.on_toggle_sound(self.sound_muted)
    
    def get_widget(self) -> ft.Container:
        """Retourne le widget à ajouter à la page."""
        return self.container
