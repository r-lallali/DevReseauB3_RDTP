"""
Dashboard Admin pour le serveur de chat.

Interface Flet affichant en temps réel les clients connectés.
Doit être lancé dans le même processus que le serveur.

Usage:
    Lancé automatiquement par server_main.py
"""

import flet as ft
import threading
import time

# Couleurs du dashboard
ADMIN_BG = "#1a1a2e"
ADMIN_BG_CARD = "#16213e"
ADMIN_BORDER = "#0f3460"
ADMIN_TEXT = "#e8e8e8"
ADMIN_TEXT_DIM = "#a0a0a0"
ADMIN_ACCENT = "#00d9ff"
ADMIN_GREEN = "#00ff88"
ADMIN_RED = "#ff4757"


class AdminDashboard:
    """Dashboard admin pour visualiser les clients connectés."""
    
    def __init__(self, page: ft.Page, chat_server):
        self.page = page
        self.chat_server = chat_server
        self.running = True
        self._pending_kick_pseudo = None
        
        # Configuration de la page
        self.page.title = "Admin Dashboard - Chat Server"
        self.page.window.width = 800
        self.page.window.height = 400
        self.page.bgcolor = ADMIN_BG
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.padding = 20
        
        self.setup_ui()
        self._setup_kick_dialog()
        
        # Démarrer le rafraîchissement automatique
        threading.Thread(target=self.refresh_loop, daemon=True).start()

    def setup_ui(self):
        """Configure l'interface du dashboard."""
        
        # Titre
        title = ft.Row([
            ft.Icon(ft.icons.ADMIN_PANEL_SETTINGS, color=ADMIN_ACCENT, size=28),
            ft.Text(
                "Admin Dashboard",
                size=24,
                weight=ft.FontWeight.BOLD,
                color=ADMIN_TEXT
            ),
        ], spacing=10)
        
        # Compteur de clients
        self.client_count = ft.Text(
            "0 clients connectés",
            size=14,
            color=ADMIN_TEXT_DIM
        )
        
        header = ft.Row([
            title,
            ft.Container(expand=True),
            ft.Container(
                content=self.client_count,
                bgcolor=ADMIN_BG_CARD,
                padding=ft.padding.only(left=15, right=15, top=8, bottom=8),
                border_radius=20,
                border=ft.border.all(1, ADMIN_BORDER),
            ),
        ])
        
        # Table des clients
        self.clients_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Pseudo", color=ADMIN_ACCENT, weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Room", color=ADMIN_ACCENT, weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Dernier Message", color=ADMIN_ACCENT, weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Action", color=ADMIN_ACCENT, weight=ft.FontWeight.BOLD)),
            ],
            rows=[],
            border=ft.border.all(1, ADMIN_BORDER),
            border_radius=10,
            heading_row_color=ADMIN_BG_CARD,
            data_row_color={"": ADMIN_BG, "hovered": ADMIN_BG_CARD},
            column_spacing=30,
        )
        
        # Container scrollable pour la table
        table_container = ft.Container(
            content=ft.Column([
                self.clients_table,
            ], scroll=ft.ScrollMode.AUTO, expand=True),
            bgcolor=ADMIN_BG,
            border=ft.border.all(1, ADMIN_BORDER),
            border_radius=10,
            padding=10,
            expand=True,
        )
        
        # Message si aucun client
        self.no_clients_msg = ft.Container(
            content=ft.Column([
                ft.Icon(ft.icons.PERSON_OFF, color=ADMIN_TEXT_DIM, size=48),
                ft.Text("Aucun client connecté", color=ADMIN_TEXT_DIM, size=16),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER, spacing=10),
            expand=True,
            visible=True,
        )
        
        # Assemblage
        self.page.add(
            ft.Column([
                header,
                ft.Container(height=20),
                ft.Stack([
                    table_container,
                    self.no_clients_msg,
                ], expand=True),
            ], expand=True)
        )

    def _setup_kick_dialog(self):
        """Configure le dialog de confirmation pour le kick."""
        self.kick_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirm kick"),
            content=ft.Text(""),
            actions=[
                ft.TextButton("Cancel", on_click=self._cancel_kick),
                ft.ElevatedButton("Kick", on_click=self._confirm_kick, bgcolor=ADMIN_RED, color="white"),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.dialog = self.kick_dialog

    def _show_kick_dialog(self, pseudo: str):
        """Ouvre le dialog de confirmation pour le pseudo demandé."""
        self._pending_kick_pseudo = pseudo
        self.kick_dialog.content.value = f"Kick {pseudo} from the server?"
        self.kick_dialog.open = True
        self.page.update()

    def _cancel_kick(self, e):
        """Annule la demande de kick."""
        self._pending_kick_pseudo = None
        self.kick_dialog.open = False
        self.page.update()

    def _confirm_kick(self, e):
        """Confirme et exécute le kick."""
        if self._pending_kick_pseudo:
            self.kick_user(self._pending_kick_pseudo)
        self._pending_kick_pseudo = None
        self.kick_dialog.open = False
        self.page.update()
    
    def kick_user(self, pseudo: str):
        """Kick un utilisateur directement (sans confirmation)."""
        self.chat_server.kick_client(pseudo)
        print(f"Client {pseudo} kické")
        self.update_clients()
    
    def refresh_loop(self):
        """Boucle de rafraîchissement des données."""
        while self.running:
            try:
                self.update_clients()
            except Exception as e:
                print(f"Dashboard refresh error: {e}")
            time.sleep(2)
    
    def update_clients(self):
        """Met à jour la liste des clients."""
        clients = self.chat_server.get_clients_info()
        
        # Mettre à jour le compteur
        count = len(clients)
        self.client_count.value = f"{count} client{'s' if count != 1 else ''} connecté{'s' if count != 1 else ''}"
        
        # Mettre à jour la visibilité
        self.no_clients_msg.visible = count == 0
        self.clients_table.visible = count > 0
        
        # Mettre à jour les lignes
        self.clients_table.rows.clear()
        
        for client in clients:
            pseudo = client['pseudo']
            kick_btn = ft.IconButton(
                icon=ft.icons.BLOCK,
                icon_color=ADMIN_RED,
                icon_size=18,
                tooltip=f"Kicker {pseudo}",
                on_click=lambda e, p=pseudo: self._show_kick_dialog(p),
            )
            
            row = ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(pseudo, color=ADMIN_GREEN, weight=ft.FontWeight.BOLD)),
                    ft.DataCell(ft.Text(client['room'], color=ADMIN_TEXT)),
                    ft.DataCell(ft.Text(client['last_message'], color=ADMIN_TEXT_DIM)),
                    ft.DataCell(kick_btn),
                ]
            )
            self.clients_table.rows.append(row)
        
        self.page.update()


def run_admin_dashboard(chat_server):
    """
    Fonction pour lancer le dashboard admin.
    Appelée depuis server_main.py dans un thread séparé.
    """
    def main(page: ft.Page):
        AdminDashboard(page, chat_server)
    
    ft.app(target=main)
