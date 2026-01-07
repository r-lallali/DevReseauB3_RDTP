# Projet Chat Audio — Application client / serveur

Ce dépôt contient une application de chat en Python, structurée autour d’une architecture client / serveur.

Le projet est conçu pour évoluer progressivement : nouvelles fonctionnalités, enrichissement du protocole, gestion de plusieurs clients, etc. 
Ce document décrit les **principes généraux** du projet et reste valable indépendamment de l’état d’avancement.

---

## 🎯 Objectifs du projet

* Mettre en place une architecture client / serveur claire
* Centraliser les règles d’échange dans un protocole partagé
* Séparer strictement la logique applicative du lancement des programmes
* Faciliter les tests automatisés
* Fournir une base de départ lisible, maintenable et évolutive

---

## 📁 Organisation générale

Le projet est organisé en plusieurs répertoires, chacun ayant une responsabilité bien définie.

```
project/
├── server/     # logique et exécution côté serveur
├── client/     # logique et exécution côté client
├── common/     # code partagé (protocole, constantes, formats)
├── tests/      # tests automatisés
└── README.md
```

Cette organisation permet :

* d’éviter les dépendances croisées inutiles,
* de rendre les rôles de chaque composant explicites,
* d’accompagner naturellement l’évolution du projet.

---

## 🧩 Rôles des composants

### Serveur

Le serveur est responsable des règles métier et de la gestion des clients :

* validation des requêtes,
* gestion de l’état des connexions,
* application des règles définies par le protocole.

La logique serveur est distincte du code de lancement (création de socket, écoute, acceptation des connexions).

---

### Client

Le client est responsable :

* de la construction et de l’envoi des messages,
* de la réception et de l’interprétation des réponses du serveur,
* de l’orchestration des actions côté utilisateur.

Comme pour le serveur, la logique applicative est séparée du point d’entrée.

---

### Protocole partagé

Le protocole définit :

* les types de messages échangés,
* le format des données,
* les règles d’encodage et de décodage.

Il constitue le contrat entre le client et le serveur.

---

### Tests

Les tests automatisés permettent de vérifier le comportement du système indépendamment du réseau réel.

Ils servent à :

* valider les règles métier,
* sécuriser les évolutions,
* détecter rapidement les régressions.

---

## ▶️ Exécution et tests

Le projet fournit :

* des points d’entrée pour lancer le serveur et le client,
* une suite de tests unitaires exécutables depuis la ligne de commande.

Les détails pratiques (commandes, paramètres) sont volontairement simples et peuvent évoluer sans remettre en cause l’architecture.

---

## 🧠 Principes de conception

* séparation claire des responsabilités
* aucun effet de bord lors de l’import des modules
* dépendances explicites entre composants
* code lisible avant d’être optimisé

---

## 🔄 Évolution du projet

Le projet est destiné à évoluer.


L’architecture actuelle est pensée pour accueillir ces évolutions sans remise en cause majeure.

---


