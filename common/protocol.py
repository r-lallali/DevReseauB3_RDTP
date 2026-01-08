"""
protocole.py

Fonctions utilitaires pour l'encodage et le décodage des données
échangées dans l'application, selon un protocole binaire simple.

Conventions :
- Les entiers ont une taille fixe
- Les chaînes de caractères sont précédées de leur longueur
- L'ordre des octets est big-endian (ordre utilisé en réseau)
"""

import struct

# Message types
LOGIN = 0x01
LOGIN_OK = 0x02
LOGIN_ERR = 0x03
JOIN = 0x10
JOIN_OK = 0x11
LEAVE = 0x12
MSG = 0x20
MSG_BROADCAST = 0x21
ERROR = 0x30
PING = 0xF0
PONG = 0xF1

# Constants
MAX_PSEUDO_LEN = 32
MAX_ROOM_LEN = 32
MAX_MSG_LEN = 1024  # Taille max d'un message (voir PROTOCOL.md section 7)

STATE_CONNECTED = "CONNECTÉ"        # Connexion TCP établie, en attente de LOGIN
STATE_AUTHENTICATED = "AUTHENTIFIÉ"  # LOGIN réussi, peut faire JOIN
STATE_IN_ROOM = "DANS_SALON"         # Dans un salon, peut envoyer MSG ou LEAVE


def pack_int(value: int) -> bytes:
    """
    Encode un entier sur 4 octets.
    """

    return struct.pack(">I", value)


def unpack_int(data: bytes) -> int:
    """
    Décode un entier à partir des 4 premiers octets du flux.
    """

    return struct.unpack(">I", data[:4])[0]


def pack_string(text: str) -> bytes:
    """
    Encode une chaîne de caractères.

    Format :
    - 2 octets : longueur de la chaîne (en octets)
    - N octets : texte encodé en UTF-8
    """

    encoded_text = text.encode("utf-8")
    length = len(encoded_text)

    return struct.pack(">H", length) + encoded_text


def unpack_string(data: bytes) -> str:
    """
    Décode une chaîne de caractères à partir d'une suite d'octets (bytes).
    """

    length = struct.unpack(">H", data[:2])[0]
    return data[2:2 + length].decode("utf-8")


def pack_message(msg_type: int, payload: bytes = b"") -> bytes:
    """
    Encode un message complet (type + longueur + payload).
    
    Format :
    - 1 octet : type de message
    - 4 octets : longueur du payload (Big Endian)
    - N octets : payload
    """
    
    header = struct.pack(">BI", msg_type, len(payload))
    return header + payload


def unpack_header(header: bytes) -> tuple[int, int]:
    """
    Décode l'en-tête d'un message (type + longueur).
    
    Returns:
        tuple: (msg_type, payload_length)
    """
    
    msg_type = header[0]
    length = struct.unpack(">I", header[1:5])[0]
    return msg_type, length
