# 🌍 TradeSahel - Intelligence Commerciale pour le Mali

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://streamlit.io)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Groq](https://img.shields.io/badge/Groq-LLaMA_3.3-orange.svg)](https://groq.com)
[![SQLite](https://img.shields.io/badge/SQLite-3-blue.svg)](https://sqlite.org)

**TradeSahel** est une application web d'intelligence commerciale complète dédiée aux commerçants, PME et entrepreneurs du Mali. Elle permet d'importer des données de ventes, d'analyser les performances en temps réel, de suivre les stocks, de définir des objectifs commerciaux et d'obtenir des analyses avancées par IA.

---

## 📑 Table des matières

1. [Présentation](#-présentation)
2. [Fonctionnalités](#-fonctionnalités)
3. [Installation](#-installation)
4. [Démarrage rapide](#-démarrage-rapide)
5. [Format des données](#-format-des-données)
6. [Configuration IA](#-configuration-ia)
7. [Structure du projet](#-structure-du-projet)
8. [Base de données](#-base-de-données)
9. [Personnalisation](#-personnalisation)
10. [Dépannage](#-dépannage)
11. [Déploiement](#-déploiement)
12. [Licence](#-licence)

---

## 🎯 Présentation

TradeSahel est né d'un besoin réel : **aider les commerçants maliens à mieux gérer leurs ventes et prendre des décisions éclairées**.

### Problèmes résolus
- ❌ Difficulté à suivre les performances commerciales
- ❌ Manque de visibilité sur les stocks
- ❌ Absence d'analyses prédictives
- ❌ Perte de temps sur les rapports manuels

### Solutions apportées
- ✅ Tableau de bord en temps réel
- ✅ Gestion automatisée des stocks
- ✅ Prévisions IA adaptées au contexte malien
- ✅ Export PDF/Excel professionnel

---

## ✨ Fonctionnalités

### 📊 13 onglets disponibles

| # | Onglet | Fonctionnalités |
|---|--------|-----------------|
| 1 | 📊 Vue générale | KPIs, graphiques, top produits, évolution |
| 2 | 🏬 Multi-boutiques | Comparaison entre plusieurs fichiers/boutiques |
| 3 | ⚖️ Comparaison | Deux périodes ou plusieurs produits |
| 4 | 🎯 Objectifs | Définition et suivi des objectifs |
| 5 | 📦 Stocks | Gestion des niveaux de stock |
| 6 | 🔮 Prévisions IA | Projections des ventes (LLaMA 3.3) |
| 7 | 💬 Chat IA | Assistant conversationnel |
| 8 | 🧠 Rapport IA | Analyse commerciale complète |
| 9 | 🚨 Alertes | Détection automatique des anomalies |
| 10 | 📜 Historique | Rapports IA sauvegardés |
| 11 | 💬 Notes | Prise de notes personnelles |
| 12 | 🗄️ Données | Gestion des fichiers importés |
| 13 | 📥 Export | PDF, Excel, CSV |

### 📈 KPIs calculés

| Métrique | Formule |
|----------|---------|
| CA Nominal | Σ(quantité × prix_unitaire) |
| CA Réel | CA_nominal / 1.02 (TVA Mali 2%) |
| Panier Moyen | CA_nominal / nb_transactions |
| Marge Brute | Σ(CA - (quantité × prix_achat)) |
| Taux de Marge | (marge_brute / CA) × 100 |

---

## 💻 Installation

### Prérequis

| Configuration | Minimum |
|---------------|---------|
| Système | Windows 10/11, macOS 11+, Linux |
| RAM | 2 Go |
| Stockage | 500 Mo |
| Python | 3.8 ou supérieur |

### Étape 1 : Installer Python

**Windows :**
- Téléchargez sur [python.org](https://python.org/downloads)
- **Cochez "Add Python to PATH"**
- Vérifiez : `python --version`

