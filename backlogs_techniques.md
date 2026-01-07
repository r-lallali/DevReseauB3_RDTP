# 📌 Backlog technique — Stories réseau (US2 à US5)


## 🔧 US2 — Connexion client / serveur (TCP)

### Objectif technique
Mettre en place la **connexion TCP de base** entre un client et un serveur.

---

### Côté serveur
- Créer une socket TCP (`AF_INET`, `SOCK_STREAM`)
- `bind()` sur une IP et un port
- `listen()` pour accepter des connexions
- `accept()` les clients
- Pour chaque client :
  - créer une **socket dédiée**
  - initialiser son état à `CONNECTÉ`

---

### Côté client
- Créer une socket TCP
- Se connecter au serveur avec `connect()`
- Maintenir la connexion ouverte tant que la session est active

---

### Critères de validation
- Le client peut se connecter sans erreur
- Le serveur accepte plusieurs connexions successives
- La connexion TCP reste ouverte

---

## US3 — Authentification (LOGIN / pseudo)

### Objectif technique
Gérer un **état client côté serveur** et autoriser ou refuser les actions selon cet état.

---

### Côté serveur
- À la connexion TCP :
  - état initial = `CONNECTÉ`
- Réception du message `LOGIN`
- Vérifier :
  - format valide
  - pseudo non vide
  - pseudo non déjà utilisé
- Si succès :
  - stocker le pseudo **en mémoire**
  - changer l’état client → `AUTHENTIFIÉ`
  - envoyer `LOGIN_OK`
- Sinon :
  - envoyer `LOGIN_ERR` ou `ERROR`

---

### Côté client
- Envoyer `LOGIN` après la connexion TCP
- Attendre `LOGIN_OK`
- Ne rien envoyer d’autre tant que l’authentification n’est pas validée

---

### Critères de validation
- Un client non authentifié ne peut rien faire
- Deux clients ne peuvent pas avoir le même pseudo
- Un client refusé reste bloqué

---

## 🔧 US4 — Rejoindre un salon (JOIN / LEAVE)

### Objectif technique
Associer un client à un **groupe logique (salon)** géré côté serveur.

---

### Côté serveur
- Maintenir une structure en mémoire :
  - `nom_salon → liste des clients`
- À la réception de `JOIN` :
  - vérifier que le client est `AUTHENTIFIÉ`
  - créer le salon s’il n’existe pas
  - retirer le client de son ancien salon si nécessaire
  - ajouter le client au nouveau salon
  - changer l’état client → `DANS_SALON`
  - envoyer `JOIN_OK`
- À la réception de `LEAVE` :
  - retirer le client du salon
  - changer l’état client → `AUTHENTIFIÉ`

---

### Côté client
- Envoyer `JOIN` uniquement après `LOGIN_OK`
- Attendre `JOIN_OK`
- Ne pas envoyer de message tant que le client n’est pas dans un salon

---

### Critères de validation
- Un client ne peut être que dans **un seul salon**
- Impossible d’envoyer un message hors salon
- Les salons sont gérés uniquement côté serveur

---

## US5 — Envoi et diffusion de messages (MSG / MSG_BROADCAST)

### Objectif technique
Implémenter la **diffusion de messages** via le serveur (broadcast).

---

### Côté serveur
- Réception d’un `MSG` depuis un client `DANS_SALON`
- Vérifier :
  - état valide
  - message non vide
  - taille ≤ limite autorisée
- Diffuser un `MSG_BROADCAST` à :
  - tous les clients du même salon
- Le serveur est l’unique point de diffusion

---

### Côté client
- Envoyer `MSG`
- Recevoir `MSG_BROADCAST`
- Afficher le pseudo et le message reçu

---

### Critères de validation
- Tous les clients d’un salon reçoivent le message
- Les clients hors salon ne reçoivent rien
- Aucun client ne diffuse directement à un autre client

---

## Vision globale

| Story | Compétence réseau validée |
|------|----------------------------|
| US2 | Connexion TCP |
| US3 | États client |
| US4 | Logique serveur / salons |
| US5 | Diffusion (broadcast) |
