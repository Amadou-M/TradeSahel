# 🇲🇱 TradeSahel — Intelligence Commerciale Mali

> Plateforme d'analyse commerciale intelligente dédiée aux commerçants et PME du Mali, avec IA intégrée, base de données persistante et exports professionnels.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-red?logo=streamlit)
![SQLite](https://img.shields.io/badge/SQLite-3-green?logo=sqlite)
![Groq](https://img.shields.io/badge/Groq-LLaMA_3.3-orange)
![License](https://img.shields.io/badge/Licence-MIT-yellow)

---

## 📋 Table des matières

1. [Présentation](#présentation)
2. [Fonctionnalités](#fonctionnalités)
3. [Architecture](#architecture)
4. [Installation](#installation)
5. [Lancement](#lancement)
6. [Format des données](#format-des-données)
7. [Structure des fichiers](#structure-des-fichiers)
8. [Base de données](#base-de-données)
9. [Comptes démo](#comptes-démo)
10. [Dépendances](#dépendances)
11. [FAQ](#faq)

---

## Présentation

**TradeSahel** est un dashboard commercial complet développé avec Streamlit, conçu spécifiquement pour le marché malien (devise FCFA). Il permet aux commerçants, boutiquiers et PME d'analyser leurs ventes, suivre leurs stocks, générer des rapports IA et exporter leurs données en PDF, Word ou Excel — sans aucune connaissance technique.

### Pourquoi TradeSahel ?

- 🛒 **Adapté au Mali** : FCFA, saisonnalité locale (Ramadan, récoltes, hivernage), contexte PME africain
- 🤖 **IA intégrée** : Rapports commerciaux, prévisions et chat IA via Groq (LLaMA 3.3 70B)
- 💾 **Données persistantes** : Base SQLite locale — vos données restent entre les sessions
- 🔒 **Sécurisé** : Authentification SHA-256, comptes multi-utilisateurs
- 📱 **Accessible** : Interface web simple, aucune installation complexe

---

## Fonctionnalités

### 📊 Tableau de bord
- KPIs en temps réel : CA nominal, CA réel (hors inflation 2%), panier moyen, quantité, transactions
- Calcul automatique de la marge bénéficiaire si `prix_achat` fourni
- Tableau détaillé par produit avec part du CA et taux de marge
- Graphiques interactifs : Top 10 produits, répartition par secteur, évolution temporelle
- Filtres : type de commerce, produit, période (jour/semaine/mois/année)

### 🏬 Multi-boutiques
- Comparaison simultanée de plusieurs points de vente
- Import multi-fichiers avec détection automatique des doublons (hash MD5)
- Vue consolidée ou par boutique

### ⚖️ Comparaison
- Comparaison de deux périodes avec évolution en %
- Comparaison multi-produits sur une même période
- Tableau de tendances (Hausse / Baisse / Stable)

### 🎯 Objectifs
- Définition d'objectifs par secteur ou par produit
- Jauges visuelles d'atteinte (0–150%)
- **Sauvegarde persistante** des objectifs en base SQLite

### 📦 Gestion des stocks
- Suivi du stock restant par produit (dernier enregistrement)
- Seuil d'alerte configurable
- Code couleur : 🟢 OK / 🟡 Faible / 🔴 Rupture
- Graphique en barres avec ligne de seuil

### 🔮 Prévisions IA
- Prévisions sur 1 mois, 1 trimestre ou 6 mois
- Prise en compte de la saisonnalité malienne (Ramadan, hivernage, fêtes nationales)
- Fourchette basse/haute par secteur
- Niveau de confiance justifié

### 💬 Chat IA
- Chat contextuel basé sur vos données réelles
- Historique des conversations persisté en base SQLite
- Effacement possible à tout moment

### 🧠 Rapport IA complet
- Rapport structuré en 6 sections : résumé exécutif, analyse, points forts, vigilance, recommandations, plan d'action
- Adapté au contexte économique malien
- Sauvegardé automatiquement dans l'historique

### 📜 Historique IA
- Consultation de tous les rapports générés
- Export individuel en **TXT**, **PDF** ou **Word** par rapport
- Suppression sélective

### 💬 Notes
- Ajout, modification et suppression de notes
- 3 niveaux de priorité : info / important / urgent
- Persistées en base SQLite

### 🗄️ Gestion des données
- Liste des fichiers importés avec nombre de lignes et date
- Suppression d'un fichier et de toutes ses données (CASCADE)
- Statistiques globales de la base
- Zone de réinitialisation complète

### 📥 Export
- **PDF** : Rapport complet avec KPIs, tableau produits et analyse IA (ReportLab, UTF-8)
- **Excel** : 4 feuilles (données brutes, par produit, par secteur, stocks)
- **CSV** : Données filtrées de la période sélectionnée
- **Word** : Rapport formaté avec tableaux (.docx)
- Template CSV téléchargeable pour formater ses données

---

## Architecture

```
TradeSahel/
├── app.py                    # Application principale Streamlit
├── tradesahel_db.py          # Couche base de données SQLite
├── tradesahel.db             # Base SQLite (créée automatiquement)
├── tradesahel_comptes.json   # Comptes utilisateurs (créé automatiquement)
├── requirements.txt          # Dépendances Python
└── README.md                 # Cette documentation
```

### Séparation des responsabilités

| Fichier | Rôle |
|---|---|
| `app.py` | Interface Streamlit, logique UI, appels IA |
| `tradesahel_db.py` | Toutes les opérations SQLite (CRUD) |
| `tradesahel.db` | Base de données persistante |
| `tradesahel_comptes.json` | Authentification (JSON + SHA-256) |

---

## Installation

### Prérequis
- Python 3.10 ou supérieur
- pip

### Étape 1 — Cloner ou télécharger le projet

```powershell
# Créer le dossier
mkdir "C:\Users\VotreNom\Desktop\TradeSahel"
cd "C:\Users\VotreNom\Desktop\TradeSahel"
```

Placez `app.py` et `tradesahel_db.py` dans ce dossier.

### Étape 2 — Installer les dépendances

```powershell
pip install streamlit pandas plotly groq reportlab python-docx xlsxwriter openpyxl
```

Ou avec le fichier requirements :

```powershell
pip install -r requirements.txt
```

### Contenu de `requirements.txt`

```
streamlit>=1.32.0
pandas>=2.0.0
plotly>=5.18.0
groq>=0.4.0
reportlab>=4.0.0
python-docx>=1.1.0
xlsxwriter>=3.1.0
openpyxl>=3.1.0
```

### Étape 3 — Obtenir une clé API Groq (gratuite)

1. Allez sur [console.groq.com](https://console.groq.com)
2. Créez un compte gratuit
3. Générez une clé API (`gsk_...`)
4. Collez-la dans le panneau gauche de l'application

---

## Lancement

```powershell
cd "C:\Users\VotreNom\Desktop\TradeSahel"
streamlit run app.py
```

L'application s'ouvre automatiquement dans votre navigateur à `http://localhost:8501`.

---

## Format des données

### Colonnes requises

| Colonne | Type | Exemple | Description |
|---|---|---|---|
| `date` | Date | `2025-01-15` | Date de la vente |
| `produit` | Texte | `Riz 25kg` | Nom du produit |
| `quantite` | Nombre | `10` | Quantité vendue |
| `prix_unitaire` | Nombre | `12500` | Prix de vente unitaire en FCFA |

### Colonnes optionnelles

| Colonne | Type | Exemple | Description |
|---|---|---|---|
| `type_commerce` | Texte | `Alimentation` | Secteur d'activité |
| `prix_achat` | Nombre | `8000` | Prix d'achat (calcul marge automatique) |
| `stock` | Nombre | `50` | Stock restant |
| `boutique_nom` | Texte | `Boutique Centre` | Nom de la boutique |

### Exemple de fichier CSV

```csv
date,produit,type_commerce,quantite,prix_unitaire,prix_achat,stock
2025-01-15,Riz 25kg,Alimentation,10,12500,8000,50
2025-01-16,Huile 5L,Alimentation,5,3500,2200,30
2025-01-17,Savon,Hygiene,20,1500,900,80
2025-01-18,Sucre 1kg,Alimentation,15,800,500,120
2025-01-19,Lait en poudre,Alimentation,8,4500,3000,40
```

> 💡 Un template CSV téléchargeable est disponible directement dans l'application (panneau gauche).

---

## Base de données

### Tables SQLite

| Table | Description |
|---|---|
| `fichiers_importes` | Métadonnées des fichiers importés (anti-doublon MD5) |
| `ventes` | Toutes les lignes de ventes (CASCADE sur suppression) |
| `historique_ia` | Rapports et prévisions générés par l'IA |
| `objectifs` | Objectifs commerciaux par utilisateur |
| `notes` | Notes et observations |
| `historique_chat` | Conversations avec le chat IA |

### Anti-doublon automatique

Chaque fichier importé est hashé en MD5. Si vous importez deux fois le même fichier, il est automatiquement ignoré — aucune donnée dupliquée.

### Suppression en cascade

Supprimer un fichier importé supprime automatiquement toutes ses lignes de ventes associées (contrainte `ON DELETE CASCADE`).

---

## Comptes démo

| Identifiant | Mot de passe | Boutique |
|---|---|---|
| `admin` | `admin123` | Boutique Principale |
| `mali1` | `mali2025` | Shop Bamako |

> Les mots de passe sont hashés en SHA-256 — jamais stockés en clair.

---

## Dépendances

| Bibliothèque | Usage |
|---|---|
| `streamlit` | Interface web |
| `pandas` | Manipulation des données |
| `plotly` | Graphiques interactifs |
| `groq` | API LLaMA 3.3 70B (IA) |
| `reportlab` | Export PDF (UTF-8 natif) |
| `python-docx` | Export Word (.docx) |
| `xlsxwriter` | Export Excel avec mise en forme |
| `sqlite3` | Base de données (inclus Python) |
| `hashlib` | Hashage SHA-256 des mots de passe |

---

## FAQ

**Q : Mes données disparaissent après redémarrage ?**
R : Vérifiez que `tradesahel.db` est bien dans le même dossier que `app.py`. C'est ce fichier qui contient toutes vos données.

**Q : Erreur "No module named tradesahel_db" ?**
R : Le fichier `tradesahel_db.py` doit être dans le même dossier que `app.py`. Vérifiez que le nom est bien en minuscules.

**Q : Le PDF contient des carrés noirs à la place des accents ?**
R : Cette version utilise ReportLab (pas FPDF), ce problème est résolu. Vérifiez que vous avez la dernière version de `app.py`.

**Q : Comment ajouter un nouvel utilisateur ?**
R : Sur la page de connexion, cliquez sur "Créer un compte". Le compte est sauvegardé immédiatement dans `tradesahel_comptes.json`.

**Q : Puis-je importer plusieurs boutiques en même temps ?**
R : Oui. Dans le panneau gauche, vous pouvez importer plusieurs fichiers CSV/Excel simultanément. L'onglet "Multi-boutiques" compare automatiquement les données par fichier.

**Q : La clé Groq est-elle obligatoire ?**
R : Non. Toutes les fonctionnalités d'analyse (graphiques, KPIs, filtres, export) fonctionnent sans clé. La clé est uniquement nécessaire pour les onglets IA (Prévisions, Chat, Rapport IA).

---

## Auteur

**Amadou MAIGA**
Master 1 Data Science & Intelligence Artificielle
Ecole-IT Bruxelles, Belgique

---

*🇲🇱 TradeSahel · Intelligence Commerciale · Mali · 2025*