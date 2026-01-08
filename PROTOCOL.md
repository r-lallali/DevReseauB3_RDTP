# Protocole de Chat TCP

## 1. Format des messages

Chaque message a cette structure :

```
+----------+-------------------+------------------+
|   TYPE   |  PAYLOAD_LENGTH   |     PAYLOAD      |
|  1 octet |     4 octets      |    N octets      |
+----------+-------------------+------------------+
```

- **TYPE** : identifie le type de message
- **PAYLOAD_LENGTH** : taille du payload (Big Endian)
- **PAYLOAD** : contenu variable (peut être vide)

**Chaînes de caractères** (UTF-8, préfixées par leur longueur) :
```
+------------------+------------------+
|  LONGUEUR (2 o)  |   TEXTE (UTF-8)  |
+------------------+------------------+
```

---

## 2. Types de messages

| Code | Nom | Direction | Description |
|------|-----|-----------|-------------|
| `0x01` | LOGIN | Client → Serveur | Connexion avec pseudo |
| `0x02` | LOGIN_OK | Serveur → Client | Connexion acceptée |
| `0x03` | LOGIN_ERR | Serveur → Client | Connexion refusée |
| `0x10` | JOIN | Client → Serveur | Rejoindre un salon |
| `0x11` | JOIN_OK | Serveur → Client | Entrée confirmée |
| `0x12` | LEAVE | Client → Serveur | Quitter le salon |
| `0x20` | MSG | Client → Serveur | Envoyer un message |
| `0x21` | MSG_BROADCAST | Serveur → Client | Message diffusé |
| `0x30` | ERROR | Serveur → Client | Erreur |
| `0xF0` | PING | Serveur → Client | Heartbeat |
| `0xF1` | PONG | Client → Serveur | Réponse heartbeat |
| `0x40` | FILE_OFFER | Client → Serveur | Propose un fichier audio |
| `0x41` | FILE_REQUEST | Serveur → Clients | Demande d’acceptation du fichier |
| `0x42` | FILE_ACCEPT | Client → Serveur | Accepte le fichier |
| `0x43` | FILE_REJECT | Client → Serveur | Refuse le fichier |
| `0x44` | FILE_START | Serveur → Client | Autorisation de commencer l’envoi |
| `0x45` | FILE_CANCEL | Serveur → Client | Refus du transfert |

---

## 3. Détail des payloads

### LOGIN (0x01)
```
[LONGUEUR: 2o][PSEUDO: UTF-8]
```

### LOGIN_OK (0x02)
Payload vide.

### LOGIN_ERR (0x03)
```
[LONGUEUR: 2o][RAISON: UTF-8]
```

### JOIN (0x10)
```
[LONGUEUR: 2o][NOM_SALON: UTF-8]
```

### JOIN_OK (0x11)
Payload vide.

### LEAVE (0x12)
Payload vide.

### MSG (0x20)
```
[LONGUEUR: 2o][MESSAGE: UTF-8]
```

### MSG_BROADCAST (0x21)
```
[LONG_PSEUDO: 2o][PSEUDO: UTF-8][LONG_MSG: 2o][MESSAGE: UTF-8]
```

### ERROR (0x30)
```
[CODE: 1o][LONGUEUR: 2o][MESSAGE: UTF-8]
```

### PING (0xF0) / PONG (0xF1)
Payload vide.

---

### FILE_OFFER (0x40)

[LONG_FILENAME: 2o][FILENAME: UTF-8][SIZE: 4o]

- **États requis** : `DANS_SALON`
- **Nouvel état** : `WAITING_FILE_CONFIRMATION`

### FILE_REQUEST (0x41)

[LONG_PSEUDO: 2o][PSEUDO: UTF-8][LONG_FILENAME: 2o][FILENAME: UTF-8][SIZE: 4o]

### FILE_ACCEPT (0x42)
Payload vide.
- **États requis** : `DANS_SALON`

### FILE_REJECT (0x43)
Payload vide.
- **États requis** : `DANS_SALON`

### FILE_START (0x44)
Payload vide.
- **Effet** : Retour à l’état `DANS_SALON`

### FILE_CANCEL (0x45)

[LONG_REASON: 2o][REASON: UTF-8]

- **Effet** : Retour à l’état `DANS_SALON`

---

## 4. Codes d'erreur

| Code | Signification |
|------|---------------|
| `0x01` | Pseudo déjà utilisé |
| `0x02` | Pseudo invalide |
| `0x03` | Pas dans un salon |
| `0x04` | Déjà dans un salon |
| `0x05` | Message trop long |
| `0x06` | Action non autorisée |
| `0x07` | Fichier trop volumineux |
| `0x08` | Transfert déjà en cours |

---

## 5. États du client

```

DÉCONNECTÉ ──TCP──► CONNECTÉ ──LOGIN_OK──► AUTHENTIFIÉ ──JOIN_OK──► DANS_SALON
                                               ▲                         │
                                               │                         │
                                               │                         │ Propose fichier audio
                                               │                         ▼
                                               │             WAITING_FILE_CONFIRMATION
                                               |
                                               |
                                               │                         │
                                               └────────────── LEAVE ────┘


| État | Messages autorisés |
|------|-------------------|
| CONNECTÉ | LOGIN |
| AUTHENTIFIÉ | JOIN, PONG |
| DANS_SALON | MSG, LEAVE, PONG |
| WAITING_FILE_CONFIRMATION | Messages liés à la confirmation de fichier, PONG |

### État : WAITING_FILE_CONFIRMATION

Un client est dans cet état lorsqu’il a proposé un fichier audio et attend
la confirmation des autres clients du salon.

Durant cet état :
- le client ne peut pas envoyer de messages (MSG)
- le client ne peut pas changer de salon
- seuls certains messages sont autorisés
```

### État : WAITING_FILE_CONFIRMATION

Un client est dans cet état lorsqu’il a proposé un fichier audio et attend  
la confirmation des autres clients du salon.

Durant cet état :
- le client ne peut pas envoyer de messages (MSG)
- le client ne peut pas changer de salon
- seuls certains messages sont autorisés

## 6. Heartbeat

- Le serveur envoie `PING` toutes les 30 secondes
- Le client répond `PONG`
- Après 3 PING sans réponse → déconnexion

---

## 7. Limites

| Élément | Maximum |
|---------|---------|
| Pseudo | 32 caractères |
| Nom de salon | 32 caractères |
| Message | 1024 caractères |
| Taille fichier  | 10 Mo  |

---

## 8. Règles importantes

1. **Big Endian** pour tous les entiers multi-octets
2. **UTF-8** pour toutes les chaînes
3. Le salon est créé automatiquement s'il n'existe pas
4. Un client ne peut être que dans **un seul salon** à la fois
5. Toujours répondre `PONG` à un `PING`
6. Pendant un transfert de fichier, le client émetteur ne peut pas envoyer de messages ni changer de salon
7. Le serveur diffuse `FILE_REQUEST` à tous les clients du salon sauf l’émetteur
