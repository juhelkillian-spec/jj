# WhatsApp Bot CROUS — Dashboard PRD

## Problème original
Créer une application dashboard pour gérer un bot WhatsApp CROUS. Pouvoir ajouter de nouvelles commandes et de nouveaux éléments depuis le dashboard avec sauvegarde en DB.

## Architecture
- **Frontend**: React (Dashboard.jsx) — thème sombre neon green
- **Backend**: FastAPI (server.py) — API REST complète
- **Database**: MongoDB — collections auto_replies, banned_words, commands, settings, activity_logs

## Implémenté (2026-04-08)
- Vue d'ensemble avec stats (auto-réponses, mots bannis, commandes, suppressions) + journal d'activité
- CRUD complet Auto-Réponses (trigger/réponse/type + toggle actif/inactif)
- CRUD complet Mots Bannis (catégories insultes/religieux)
- CRUD complet Commandes (emoji/nom/description/catégorie)
- Paramètres bot (préfixe, langue, modèle GPT, max_tokens, clé API OpenAI, toggles modération)
- Seed initial depuis le bot Node.js existant (8 auto-réponses, 48 mots bannis, 17 commandes)
- Navigation sidebar responsive (mobile + desktop)

## Stack Bot Node.js (côté client)
- whatsapp-web.js + OpenAI GPT-4o-mini
- Fichier index.js séparé — tourne indépendamment du dashboard

## Backlog P1
- Connexion en temps réel (WebSocket) entre le bot et le dashboard pour logs live
- Génération automatique du code index.js depuis les données du dashboard
- Authentification admin pour sécuriser le dashboard
- Export de la configuration bot en JSON

## Backlog P2
- QR Code WhatsApp dans le dashboard pour connecter le bot
- Statistiques avancées avec graphiques
- Historique des commandes exécutées
