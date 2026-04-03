# 📊 TradeSahel – Plateforme d’Intelligence Commerciale (Mali)

## 🧾 README.md

### 🚀 Présentation

TradeSahel est une application web développée avec Streamlit permettant aux commerçants maliens d’analyser leurs ventes, suivre leurs performances et générer des prévisions grâce à l’intelligence artificielle.

---

### 🎯 Objectifs

* Centraliser les données de vente
* Analyser les performances commerciales
* Comparer plusieurs points de vente
* Suivre des objectifs financiers
* Générer des prévisions avec IA
* Exporter les données facilement

---

### ⚙️ Technologies utilisées

* Python
* Streamlit
* Pandas
* Plotly
* Groq API (LLM IA)
* Excel / CSV

---

### 📦 Installation

```bash
pip install streamlit pandas plotly groq openpyxl xlsxwriter
```

---

### ▶️ Lancement

```bash
streamlit run app.py
```

---

### 🔐 Comptes de démonstration

| Utilisateur | Mot de passe |
| ----------- | ------------ |
| admin       | admin123     |
| mali1       | mali2025     |

---

### 📊 Fonctionnalités principales

#### 🔑 Authentification

* Connexion utilisateur
* Création de compte
* Réinitialisation de mot de passe

#### 📂 Import de données

* CSV / Excel
* Multi points de vente

#### 📊 Analyse

* KPI (CA, panier moyen, transactions)
* Graphiques dynamiques
* Top produits
* Répartition par secteur

#### 🏪 Multi-points

* Comparaison entre boutiques

#### ⚖️ Comparaison temporelle

* Analyse entre périodes
* Évolution du chiffre d’affaires

#### 🎯 Objectifs

* Définition d’objectifs par secteur
* Suivi des performances

#### 🔮 IA (Groq)

* Prévisions de ventes
* Recommandations business

#### 🚨 Alertes automatiques

* Baisse ou hausse du CA
* Secteurs faibles
* Produits performants

#### 📥 Export

* Excel complet
* CSV filtré

---

### 🧠 IA utilisée

* Modèle : Llama 3.3 (Groq)
* Analyse des tendances commerciales
* Génération de recommandations adaptées au marché malien

---

### 📁 Structure du projet

```
TradeSahel/
│── app.py
│── README.md
│── requirements.txt
```

---

## 📘 Cahier de charges

### 1. 📌 Contexte

Les commerçants maliens manquent souvent d’outils digitaux simples pour analyser leurs ventes et prendre des décisions stratégiques.

---

### 2. 🎯 Objectifs du projet

* Digitaliser le suivi commercial
* Fournir des analyses simples et visuelles
* Aider à la prise de décision
* Introduire l’IA dans le commerce local

---

### 3. 👥 Utilisateurs cibles

* Commerçants
* Boutiques locales
* PME
* Distributeurs

---

### 4. 🧩 Fonctionnalités détaillées

#### 4.1 Authentification

* Login sécurisé
* Gestion des comptes en session

#### 4.2 Gestion des données

* Import CSV / Excel
* Nettoyage automatique
* Calcul du chiffre d’affaires

#### 4.3 Analyse des performances

* CA nominal et réel
* Panier moyen
* Quantité vendue
* Nombre de transactions

#### 4.4 Visualisation

* Graphiques interactifs
* Courbes d’évolution
* Diagrammes circulaires

#### 4.5 Comparaison

* Multi-points de vente
* Comparaison temporelle

#### 4.6 Objectifs

* Saisie d’objectifs
* Indicateurs de performance
* Jauges visuelles

#### 4.7 Intelligence artificielle

* Prévisions de ventes
* Analyse des tendances
* Recommandations stratégiques

#### 4.8 Alertes

* Détection automatique d’anomalies
* Notifications visuelles

#### 4.9 Export

* Génération de fichiers Excel
* Export CSV

---

### 5. ⚙️ Contraintes techniques

* Application web légère (Streamlit)
* Fonctionnement offline (hors IA)
* Interface simple et intuitive

---

### 6. 🔐 Sécurité

* Authentification basique (session)
* Données non persistées (actuellement)
* API Key utilisateur pour IA

---

### 7. 🚀 Évolutions futures

* Base de données (PostgreSQL)
* Authentification sécurisée (JWT)
* Dashboard mobile
* Notifications WhatsApp
* Multi-pays (Afrique de l’Ouest)

---

### 8. 📊 Indicateurs de succès

* Nombre d’utilisateurs
* Fréquence d’utilisation
* Amélioration des ventes

---

### 9. 📅 Planning estimatif

| Phase         | Durée        |
| ------------- | ------------ |
| Conception    | 1 semaine    |
| Développement | 2-3 semaines |
| Tests         | 1 semaine    |
| Déploiement   | 1 semaine    |

---

### 10. 💡 Valeur ajoutée

* Simplicité d’utilisation
* Adapté au contexte africain
* Intégration IA
* Multi-boutiques

---

## 🇲🇱 TradeSahel

**Intelligence Commerciale pour le Mali et l’Afrique**
