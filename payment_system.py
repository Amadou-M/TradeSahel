"""
payment_system.py - Système de paiement et abonnements pour TradeSahel
Version corrigée avec création automatique des tables
"""

import streamlit as st
import sqlite3
import hashlib
import json
import os
import qrcode
from io import BytesIO
from datetime import datetime, timedelta
import secrets
import pandas as pd

# Configuration des plans d'abonnement
ABONNEMENT_PLANS = {
    "basic": {
        "nom": "Basic",
        "prix": 15000,
        "prix_texte": "15 000 FCFA",
        "duree_jours": 30,
        "couleur": "#006400",
        "features": [
            "📊 Import de données (5 fichiers/mois)",
            "📈 Rapports PDF basiques",
            "💾 3 mois d'historique",
            "📧 Support email"
        ]
    },
    "pro": {
        "nom": "Pro",
        "prix": 35000,
        "prix_texte": "35 000 FCFA",
        "duree_jours": 30,
        "couleur": "#2563EB",
        "features": [
            "🤖 Intelligence Artificielle avancée",
            "📦 Gestion des stocks en temps réel",
            "📊 Exports Excel/Word illimités",
            "🔮 Prévisions de ventes",
            "📁 Fichiers illimités",
            "💬 Chat IA prioritaire",
            "📧 Support prioritaire 24/7"
        ],
        "populaire": True
    },
    "premium": {
        "nom": "Premium",
        "prix": 75000,
        "prix_texte": "75 000 FCFA",
        "duree_jours": 30,
        "couleur": "#D4AF37",
        "features": [
            "👑 Toutes les fonctionnalités Pro",
            "🏪 Gestion multi-boutiques (jusqu'à 5)",
            "📱 Application mobile dédiée",
            "🔐 Accès API",
            "🎯 Analyse concurrentielle",
            "📞 Support téléphonique dédié",
            "🚀 Formation incluse",
            "💾 Backup automatique quotidien"
        ]
    }
}

# Modes de paiement
MODES_PAIEMENT = {
    "orange_money": {
        "nom": "Orange Money",
        "icon": "📱",
        "instructions": """
        1. Composez #144#
        2. Choisissez "Payer"
        3. Entrez le code marchand: **TRADESAHEL**
        4. Entrez le montant
        5. Confirmez avec votre code secret
        6. Entrez le code reçu ci-dessous
        """
    },
    "wave": {
        "nom": "Wave",
        "icon": "🌊",
        "instructions": """
        1. Ouvrez l'application Wave
        2. Scannez le QR code
        3. Vérifiez le montant
        4. Confirmez le paiement
        5. Entrez le code reçu ci-dessous
        """
    },
    "moov_money": {
        "nom": "Moov Money",
        "icon": "🔵",
        "instructions": """
        1. Composez #150#
        2. Choisissez "Payer facture"
        3. Entrez le code: **TRADESAHEL**
        4. Entrez le montant
        5. Confirmez
        6. Entrez le code reçu ci-dessous
        """
    },
    "paypal": {
        "nom": "PayPal",
        "icon": "💳",
        "instructions": """
        1. Cliquez sur "Payer avec PayPal"
        2. Connectez-vous à votre compte
        3. Confirmez le paiement
        """
    }
}

def init_payment_tables():
    """Initialise les tables de paiement si elles n'existent pas"""
    conn = sqlite3.connect("tradesahel.db")
    cursor = conn.cursor()
    
    # Table des transactions
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        transaction_id TEXT UNIQUE NOT NULL,
        username TEXT NOT NULL,
        plan TEXT NOT NULL,
        montant REAL NOT NULL,
        mode_paiement TEXT NOT NULL,
        statut TEXT DEFAULT 'en_attente',
        date_creation TEXT NOT NULL,
        date_confirmation TEXT,
        code_confirmation TEXT
    )
    """)
    
    conn.commit()
    conn.close()

def generer_id_transaction(username: str) -> str:
    """Génère un ID de transaction unique"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random = secrets.token_hex(3).upper()
    return f"TS-{timestamp}-{random}"

def generer_qr_code(data: str) -> BytesIO:
    """Génère un QR code pour le paiement"""
    qr = qrcode.QRCode(version=1, box_size=8, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="#006400", back_color="white")
    buf = BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf

def creer_transaction(username: str, plan: str, mode_paiement: str) -> str:
    """Crée une nouvelle transaction dans la base de données"""
    init_payment_tables()  # S'assurer que la table existe
    
    conn = sqlite3.connect("tradesahel.db")
    cursor = conn.cursor()
    
    transaction_id = generer_id_transaction(username)
    montant = ABONNEMENT_PLANS[plan]["prix"]
    
    cursor.execute("""
        INSERT INTO transactions (transaction_id, username, plan, montant, mode_paiement, date_creation)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (transaction_id, username, plan, montant, mode_paiement, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    
    return transaction_id

def verifier_paiement(transaction_id: str, code_confirmation: str) -> bool:
    """Vérifie et confirme un paiement"""
    conn = sqlite3.connect("tradesahel.db")
    cursor = conn.cursor()
    
    # Vérifier la transaction
    cursor.execute("SELECT * FROM transactions WHERE transaction_id=? AND statut='en_attente'", (transaction_id,))
    transaction = cursor.fetchone()
    
    if not transaction:
        conn.close()
        return False
    
    # Simuler la vérification du code (en production, appeler l'API réelle)
    # Pour la démo, on accepte n'importe quel code de 6 chiffres
    if len(code_confirmation) == 6 and code_confirmation.isdigit():
        # Mettre à jour la transaction
        cursor.execute("""
            UPDATE transactions 
            SET statut='confirme', date_confirmation=?, code_confirmation=?
            WHERE transaction_id=?
        """, (datetime.now().isoformat(), code_confirmation, transaction_id))
        
        # Activer l'abonnement
        from tradesahel_db import souscrire_abonnement
        souscrire_abonnement(transaction[2], transaction[3], transaction[5], transaction_id)
        
        conn.commit()
        conn.close()
        return True
    
    conn.close()
    return False

def get_transaction(transaction_id: str):
    """Récupère une transaction"""
    conn = sqlite3.connect("tradesahel.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM transactions WHERE transaction_id=?", (transaction_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "id": row[0],
            "transaction_id": row[1],
            "username": row[2],
            "plan": row[3],
            "montant": row[4],
            "mode_paiement": row[5],
            "statut": row[6],
            "date_creation": row[7],
            "date_confirmation": row[8],
            "code_confirmation": row[9]
        }
    return None

def get_historique_transactions(username: str) -> list:
    """Récupère l'historique des transactions d'un utilisateur"""
    init_payment_tables()  # S'assurer que la table existe
    
    conn = sqlite3.connect("tradesahel.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT transaction_id, plan, montant, mode_paiement, statut, date_creation
        FROM transactions 
        WHERE username=? 
        ORDER BY date_creation DESC
        LIMIT 20
    """, (username,))
    rows = cursor.fetchall()
    conn.close()
    
    return [{
        "transaction_id": r[0],
        "plan": r[1].capitalize() if r[1] else "",
        "montant": r[2],
        "mode_paiement": r[3],
        "statut": "✅ Confirmé" if r[4] == "confirme" else "⏳ En attente",
        "date": r[5][:10] if r[5] else ""
    } for r in rows]

# ====================== INTERFACE STREAMLIT ======================

def afficher_carte_abonnement(plan_key: str, plan: dict, est_actif: bool = False):
    """Affiche une carte d'abonnement"""
    
    if plan.get("populaire"):
        st.markdown(f"""
        <div style='
            background: linear-gradient(135deg, {plan["couleur"]}20, white);
            border: 2px solid {plan["couleur"]};
            border-radius: 20px;
            padding: 20px;
            margin: 10px 0;
            position: relative;
        '>
            <div style='
                position: absolute;
                top: -12px;
                right: 20px;
                background: {plan["couleur"]};
                color: white;
                padding: 4px 16px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: bold;
            '>⭐ PLUS POPULAIRE</div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style='
            background: white;
            border: 2px solid #e0e0e0;
            border-radius: 20px;
            padding: 20px;
            margin: 10px 0;
        '>
        """, unsafe_allow_html=True)
    
    st.markdown(f"""
        <h2 style='color: {plan["couleur"]}; text-align: center;'>{plan["nom"]}</h2>
        <div style='text-align: center; margin: 15px 0;'>
            <span style='font-size: 36px; font-weight: bold;'>{plan["prix_texte"]}</span>
            <span style='color: #666;'>/mois</span>
        </div>
        <hr>
    """, unsafe_allow_html=True)
    
    for feature in plan["features"]:
        st.markdown(f"<div style='margin: 8px 0;'>✓ {feature}</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    if est_actif:
        st.success("✅ ACTIF")
        return False
    else:
        return st.button(f"Souscrire {plan['nom']}", key=f"btn_{plan_key}", use_container_width=True)

def afficher_interface_paiement(username: str, plan_key: str):
    """Affiche l'interface de paiement"""
    plan = ABONNEMENT_PLANS[plan_key]
    
    st.subheader(f"💳 Paiement - Abonnement {plan['nom']}")
    st.markdown(f"**Montant à payer :** {plan['prix_texte']} FCFA")
    
    # Sélection du mode de paiement
    mode_paiement = st.selectbox(
        "Choisissez votre mode de paiement",
        list(MODES_PAIEMENT.keys()),
        format_func=lambda x: f"{MODES_PAIEMENT[x]['icon']} {MODES_PAIEMENT[x]['nom']}"
    )
    
    if st.button("🔄 Générer le paiement", use_container_width=True):
        transaction_id = creer_transaction(username, plan_key, mode_paiement)
        st.session_state['current_transaction'] = transaction_id
        st.session_state['current_plan'] = plan_key
        st.rerun()
    
    # Afficher les instructions si une transaction est en cours
    if 'current_transaction' in st.session_state:
        transaction_id = st.session_state['current_transaction']
        transaction = get_transaction(transaction_id)
        
        if transaction and transaction['statut'] == 'en_attente':
            st.markdown("---")
            st.subheader("📋 Instructions de paiement")
            
            mode_info = MODES_PAIEMENT[transaction['mode_paiement']]
            st.markdown(mode_info['instructions'])
            
            # QR Code pour Wave/Orange Money
            if transaction['mode_paiement'] in ['wave', 'orange_money']:
                qr_data = f"TRADESAHEL:{transaction['transaction_id']}:{transaction['montant']}"
                qr_buf = generer_qr_code(qr_data)
                st.image(qr_buf.getvalue(), width=200, caption="Scannez pour payer")
            
            # Formulaire de confirmation
            st.markdown("---")
            st.subheader("✅ Confirmation du paiement")
            st.info("💡 **Code de test**: Entrez n'importe quel nombre à 6 chiffres (ex: 123456)")
            code = st.text_input("Code de confirmation reçu", placeholder="123456", type="password")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Vérifier le paiement", use_container_width=True):
                    if verifier_paiement(transaction_id, code):
                        st.success("🎉 Paiement confirmé ! Abonnement activé.")
                        st.balloons()
                        # Nettoyer la session
                        if 'current_transaction' in st.session_state:
                            del st.session_state['current_transaction']
                        if 'current_plan' in st.session_state:
                            del st.session_state['current_plan']
                        st.rerun()
                    else:
                        st.error("Code invalide. Vérifiez et réessayez.")
            
            with col2:
                if st.button("Annuler", use_container_width=True):
                    if 'current_transaction' in st.session_state:
                        del st.session_state['current_transaction']
                    if 'current_plan' in st.session_state:
                        del st.session_state['current_plan']
                    st.rerun()

def afficher_historique_abonnements(username: str):
    """Affiche l'historique des abonnements"""
    st.subheader("📜 Historique des transactions")
    
    transactions = get_historique_transactions(username)
    
    if transactions:
        df = pd.DataFrame(transactions)
        df.columns = ["ID Transaction", "Plan", "Montant (FCFA)", "Mode", "Statut", "Date"]
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Aucune transaction trouvée")

def afficher_interface_abonnement_complete(username: str):
    """Interface complète des abonnements"""
    from tradesahel_db import get_abonnement, est_abonnement_actif
    
    # Initialiser les tables de paiement
    init_payment_tables()
    
    st.title("💳 TradeSahel - Abonnements")
    
    # Vérifier l'abonnement actuel
    abo = get_abonnement(username)
    abo_actif = abo and est_abonnement_actif(username)
    
    if abo_actif:
        # Afficher l'abonnement actif
        st.success(f"✅ **Abonnement {abo['plan']} actif**")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📅 Date de fin", abo['date_fin'][:10])
        with col2:
            jours_restants = (datetime.fromisoformat(abo['date_fin']) - datetime.now()).days
            st.metric("⏰ Jours restants", max(0, jours_restants))
        with col3:
            st.metric("💳 Montant", f"{abo['montant_mensuel']:,.0f} FCFA")
        
        st.markdown("---")
        
        # Afficher les fonctionnalités du plan actuel
        plan_info = ABONNEMENT_PLANS.get(abo['plan'].lower(), ABONNEMENT_PLANS['basic'])
        st.subheader(f"📋 Vos fonctionnalités {plan_info['nom']}")
        
        cols = st.columns(2)
        for i, feature in enumerate(plan_info['features']):
            with cols[i % 2]:
                st.markdown(f"✓ {feature}")
        
        st.markdown("---")
        
        # Option de renouvellement
        if st.button("🔄 Renouveler l'abonnement", use_container_width=True):
            st.session_state['renouvellement'] = True
            st.rerun()
        
        # Afficher historique
        afficher_historique_abonnements(username)
        
        # Vérifier si on est en mode renouvellement
        if 'renouvellement' in st.session_state:
            st.markdown("---")
            st.subheader("🔄 Renouvellement d'abonnement")
            if st.button("← Retour"):
                del st.session_state['renouvellement']
                st.rerun()
            afficher_interface_paiement(username, abo['plan'].lower())
        
    else:
        # Pas d'abonnement actif
        st.warning("⚠️ **Vous n'avez pas d'abonnement actif**")
        st.markdown("Choisissez un plan ci-dessous pour commencer à utiliser TradeSahel.")
        st.markdown("---")
        
        # Vérifier si on est en mode paiement
        if 'current_plan' in st.session_state:
            afficher_interface_paiement(username, st.session_state['current_plan'])
            if st.button("← Retour aux plans"):
                del st.session_state['current_plan']
                if 'current_transaction' in st.session_state:
                    del st.session_state['current_transaction']
                st.rerun()
        else:
            # Afficher les 3 cartes d'abonnement
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if afficher_carte_abonnement("basic", ABONNEMENT_PLANS["basic"], False):
                    st.session_state['current_plan'] = "basic"
                    st.rerun()
            
            with col2:
                if afficher_carte_abonnement("pro", ABONNEMENT_PLANS["pro"], False):
                    st.session_state['current_plan'] = "pro"
                    st.rerun()
            
            with col3:
                if afficher_carte_abonnement("premium", ABONNEMENT_PLANS["premium"], False):
                    st.session_state['current_plan'] = "premium"
                    st.rerun()
            
            # Afficher historique même sans abonnement
            st.markdown("---")
            afficher_historique_abonnements(username)
    
    st.markdown("---")
    st.caption("🔒 Paiements sécurisés - Aucune information bancaire n'est stockée")
    st.caption("💡 Pour la démo, entrez n'importe quel code à 6 chiffres pour simuler un paiement")