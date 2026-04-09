"""
subscription_manager.py - Gestion des abonnements avec blocage total d'accès
Version stable et corrigée - Compatible avec app.py
"""

import streamlit as st
import sqlite3
import secrets
import qrcode
from io import BytesIO
from datetime import datetime, timedelta
import pandas as pd

# Plans d'abonnement
ABONNEMENT_PLANS = {
    "mensuel_basic": {
        "nom": "Basic Mensuel",
        "prix": 15000,
        "prix_texte": "15 000 FCFA",
        "duree_jours": 30,
        "type": "mensuel",
        "couleur": "#006400",
        "features": [
            "📊 Import de données (5 fichiers/mois)",
            "📈 Rapports PDF basiques",
            "💾 3 mois d'historique",
            "📧 Support email"
        ]
    },
    "mensuel_pro": {
        "nom": "Pro Mensuel",
        "prix": 35000,
        "prix_texte": "35 000 FCFA",
        "duree_jours": 30,
        "type": "mensuel",
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
    "mensuel_premium": {
        "nom": "Premium Mensuel",
        "prix": 75000,
        "prix_texte": "75 000 FCFA",
        "duree_jours": 30,
        "type": "mensuel",
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
    },
    "annuel_basic": {
        "nom": "Basic Annuel",
        "prix": 150000,
        "prix_texte": "150 000 FCFA",
        "duree_jours": 365,
        "type": "annuel",
        "couleur": "#006400",
        "economie": "Économisez 30 000 FCFA",
        "features": [
            "📊 Import de données (5 fichiers/mois)",
            "📈 Rapports PDF basiques",
            "💾 3 mois d'historique",
            "📧 Support email",
            "🎁 2 mois offerts"
        ]
    },
    "annuel_pro": {
        "nom": "Pro Annuel",
        "prix": 350000,
        "prix_texte": "350 000 FCFA",
        "duree_jours": 365,
        "type": "annuel",
        "couleur": "#2563EB",
        "economie": "Économisez 70 000 FCFA",
        "features": [
            "🤖 Intelligence Artificielle avancée",
            "📦 Gestion des stocks en temps réel",
            "📊 Exports Excel/Word illimités",
            "🔮 Prévisions de ventes",
            "📁 Fichiers illimités",
            "💬 Chat IA prioritaire",
            "📧 Support prioritaire 24/7",
            "🎁 2 mois offerts"
        ],
        "populaire": True
    },
    "annuel_premium": {
        "nom": "Premium Annuel",
        "prix": 750000,
        "prix_texte": "750 000 FCFA",
        "duree_jours": 365,
        "type": "annuel",
        "couleur": "#D4AF37",
        "economie": "Économisez 150 000 FCFA",
        "features": [
            "👑 Toutes les fonctionnalités Pro",
            "🏪 Gestion multi-boutiques (jusqu'à 5)",
            "📱 Application mobile dédiée",
            "🔐 Accès API",
            "🎯 Analyse concurrentielle",
            "📞 Support téléphonique dédié",
            "🚀 Formation incluse",
            "💾 Backup automatique quotidien",
            "🎁 2 mois offerts"
        ]
    }
}

# Modes de paiement
MODES_PAIEMENT = {
    "orange_money": {"nom": "Orange Money", "icon": "📱", "color": "#FF6600"},
    "wave": {"nom": "Wave", "icon": "🌊", "color": "#1a73e8"},
    "moov_money": {"nom": "Moov Money", "icon": "🔵", "color": "#0055A4"},
    "paypal": {"nom": "PayPal", "icon": "💳", "color": "#003087"}
}

def init_subscription_tables():
    """Initialise les tables d'abonnement"""
    conn = sqlite3.connect("tradesahel.db")
    cursor = conn.cursor()
    
    # Table des abonnements
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS abonnements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        plan TEXT NOT NULL,
        type_abonnement TEXT NOT NULL,
        date_debut TEXT NOT NULL,
        date_fin TEXT NOT NULL,
        montant REAL NOT NULL,
        mode_paiement TEXT,
        transaction_id TEXT,
        statut TEXT DEFAULT 'actif',
        date_dernier_paiement TEXT
    )
    """)
    
    # Table des transactions - Version CORRIGÉE avec toutes les colonnes
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
        code_confirmation TEXT,
        telephone TEXT,
        nom_complet TEXT,
        email TEXT
    )
    """)
    
    conn.commit()
    conn.close()

def souscrire_abonnement(username: str, plan_key: str, mode_paiement: str, transaction_id: str, telephone: str = "", nom_complet: str = "", email: str = "") -> bool:
    """Souscrit un abonnement pour un utilisateur"""
    plan = ABONNEMENT_PLANS[plan_key]
    aujourd_hui = datetime.now()
    date_fin = aujourd_hui + timedelta(days=plan["duree_jours"])
    
    conn = sqlite3.connect("tradesahel.db")
    cursor = conn.cursor()
    
    # Supprimer l'ancien abonnement
    cursor.execute("DELETE FROM abonnements WHERE username=?", (username,))
    
    # Créer le nouvel abonnement
    cursor.execute("""
        INSERT INTO abonnements (
            username, plan, type_abonnement, date_debut, date_fin, 
            montant, mode_paiement, transaction_id, statut, date_dernier_paiement
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'actif', ?)
    """, (
        username, plan["nom"], plan["type"], aujourd_hui.isoformat(), 
        date_fin.isoformat(), plan["prix"], mode_paiement, transaction_id, 
        aujourd_hui.isoformat()
    ))
    
    conn.commit()
    conn.close()
    return True

def get_abonnement_actif(username: str):
    """Récupère l'abonnement actif d'un utilisateur"""
    conn = sqlite3.connect("tradesahel.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM abonnements 
        WHERE username=? AND statut='actif'
        ORDER BY date_fin DESC LIMIT 1
    """, (username,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "id": row[0],
            "username": row[1],
            "plan": row[2],
            "type": row[3],
            "date_debut": row[4],
            "date_fin": row[5],
            "montant": row[6],
            "mode_paiement": row[7],
            "transaction_id": row[8],
            "statut": row[9],
            "date_dernier_paiement": row[10]
        }
    return None

def est_abonnement_valide(username: str) -> bool:
    """Vérifie si l'utilisateur a un abonnement valide"""
    abo = get_abonnement_actif(username)
    if not abo:
        return False
    
    try:
        date_fin = datetime.fromisoformat(abo["date_fin"])
        return datetime.now() <= date_fin
    except:
        return False

def jours_restants(username: str) -> int:
    """Retourne le nombre de jours restants sur l'abonnement"""
    abo = get_abonnement_actif(username)
    if not abo:
        return 0
    
    try:
        date_fin = datetime.fromisoformat(abo["date_fin"])
        jours = (date_fin - datetime.now()).days
        return max(0, jours)
    except:
        return 0

def creer_transaction(username: str, plan_key: str, mode_paiement: str, telephone: str = "", nom_complet: str = "", email: str = "") -> str:
    """Crée une transaction de paiement avec coordonnées client"""
    plan = ABONNEMENT_PLANS[plan_key]
    transaction_id = f"TS-{datetime.now().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3).upper()}"
    
    conn = sqlite3.connect("tradesahel.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO transactions (transaction_id, username, plan, montant, mode_paiement, date_creation, telephone, nom_complet, email)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (transaction_id, username, plan["nom"], plan["prix"], mode_paiement, datetime.now().isoformat(), telephone, nom_complet, email))
    
    conn.commit()
    conn.close()
    return transaction_id

def confirmer_transaction(transaction_id: str, code: str) -> bool:
    """Confirme une transaction et active l'abonnement"""
    conn = sqlite3.connect("tradesahel.db")
    cursor = conn.cursor()
    
    # Vérifier la transaction
    cursor.execute("SELECT * FROM transactions WHERE transaction_id=? AND statut='en_attente'", (transaction_id,))
    transaction = cursor.fetchone()
    
    if not transaction:
        conn.close()
        return False
    
    # Pour la démo, on accepte tout code à 6 chiffres
    if len(code) == 6 and code.isdigit():
        # Mettre à jour la transaction
        cursor.execute("""
            UPDATE transactions 
            SET statut='confirme', date_confirmation=?, code_confirmation=?
            WHERE transaction_id=?
        """, (datetime.now().isoformat(), code, transaction_id))
        
        # Activer l'abonnement
        plan_key = None
        for key, plan in ABONNEMENT_PLANS.items():
            if plan["nom"] == transaction[3]:
                plan_key = key
                break
        
        if plan_key:
            telephone = transaction[10] if len(transaction) > 10 else ""
            nom_complet = transaction[11] if len(transaction) > 11 else ""
            email = transaction[12] if len(transaction) > 12 else ""
            souscrire_abonnement(transaction[2], plan_key, transaction[5], transaction_id, telephone, nom_complet, email)
        
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
            "code_confirmation": row[9],
            "telephone": row[10] if len(row) > 10 else "",
            "nom_complet": row[11] if len(row) > 11 else "",
            "email": row[12] if len(row) > 12 else ""
        }
    return None

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

# ====================== PAGE D'ACCÈS BLOQUÉ ======================

def afficher_page_acces_bloque():
    """Affiche une page professionnelle d'accès bloqué"""
    
    st.markdown("""
    <style>
    .blocked-page {
        text-align: center;
        padding: 60px 20px;
        background: linear-gradient(135deg, #FEF2F2 0%, #FEE2E2 100%);
        border-radius: 30px;
        margin: 20px 0;
        border: 2px solid #DC2626;
    }
    .lock-icon {
        font-size: 80px;
        margin-bottom: 20px;
    }
    .title-blocked {
        font-size: 32px;
        font-weight: bold;
        color: #DC2626;
        margin-bottom: 20px;
    }
    .message-blocked {
        font-size: 16px;
        color: #666;
        margin-bottom: 30px;
    }
    .offer-card {
        background: white;
        border-radius: 15px;
        padding: 20px;
        margin: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        transition: transform 0.3s;
    }
    .offer-card:hover {
        transform: translateY(-5px);
    }
    .price {
        font-size: 28px;
        font-weight: bold;
        color: #006400;
    }
    .popular-badge {
        background: #F59E0B;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        display: inline-block;
        margin-top: 10px;
    }
    .save-badge {
        background: #22C55E;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        display: inline-block;
        margin-top: 10px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Vérifier si l'utilisateur a un abonnement expiré
    abo = get_abonnement_actif(st.session_state.username)
    
    if abo:
        jours_expire = (datetime.now() - datetime.fromisoformat(abo["date_fin"])).days
        st.markdown(f"""
        <div class="blocked-page">
            <div class="lock-icon">⏰</div>
            <div class="title-blocked">Abonnement Expiré !</div>
            <div class="message-blocked">
                Votre abonnement <strong>{abo['plan']}</strong> a expiré depuis {jours_expire} jour(s).<br>
                Veuillez renouveler votre abonnement pour continuer à utiliser TradeSahel.
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="blocked-page">
            <div class="lock-icon">🔒</div>
            <div class="title-blocked">Accès Non Autorisé</div>
            <div class="message-blocked">
                Vous n'avez pas d'abonnement actif.<br>
                Pour accéder à TradeSahel, veuillez souscrire à l'un de nos plans.
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.subheader("💰 Choisissez votre formule d'abonnement")
    
    # Onglets
    tab_mensuel, tab_annuel = st.tabs(["📆 Abonnement Mensuel", "📅 Abonnement Annuel (Économies)"])
    
    with tab_mensuel:
        col1, col2, col3 = st.columns(3)
        for idx, (key, plan) in enumerate(ABONNEMENT_PLANS.items()):
            if plan["type"] != "mensuel":
                continue
            col = [col1, col2, col3][idx % 3]
            with col:
                popular = '<div class="popular-badge">⭐ LE PLUS POPULAIRE</div>' if plan.get("populaire") else ''
                st.markdown(f"""
                <div class="offer-card">
                    <h3 style='color: {plan["couleur"]}; text-align: center;'>{plan["nom"]}</h3>
                    <div style='text-align: center;'>
                        <span class='price'>{plan["prix_texte"]}</span>
                        <span class='period'>/mois</span>
                    </div>
                    <hr>
                """, unsafe_allow_html=True)
                for feature in plan["features"][:4]:
                    st.markdown(f"✓ {feature}")
                if popular:
                    st.markdown(popular, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
                if st.button(f"Souscrire", key=f"sub_{key}", use_container_width=True):
                    st.session_state['subscription_plan'] = key
                    st.session_state['show_payment'] = True
                    st.rerun()
    
    with tab_annuel:
        col1, col2, col3 = st.columns(3)
        for idx, (key, plan) in enumerate(ABONNEMENT_PLANS.items()):
            if plan["type"] != "annuel":
                continue
            col = [col1, col2, col3][idx % 3]
            with col:
                popular = '<div class="popular-badge">⭐ LE PLUS POPULAIRE</div>' if plan.get("populaire") else ''
                st.markdown(f"""
                <div class="offer-card">
                    <h3 style='color: {plan["couleur"]}; text-align: center;'>{plan["nom"]}</h3>
                    <div style='text-align: center;'>
                        <span class='price'>{plan["prix_texte"]}</span>
                        <span class='period'>/an</span>
                    </div>
                    <div style='text-align: center;'>
                        <span class='save-badge'>{plan.get("economie", "")}</span>
                    </div>
                    <hr>
                """, unsafe_allow_html=True)
                for feature in plan["features"][:4]:
                    st.markdown(f"✓ {feature}")
                if popular:
                    st.markdown(popular, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
                if st.button(f"Souscrire", key=f"sub_{key}", use_container_width=True):
                    st.session_state['subscription_plan'] = key
                    st.session_state['show_payment'] = True
                    st.rerun()
    
    st.markdown("---")
    st.caption("🔒 Paiement sécurisé - Support: Orange Money, Wave, Moov Money, PayPal")
    st.caption("💡 Code test: 123456")

def afficher_page_paiement(username: str):
    """Affiche la page de paiement"""
    plan_key = st.session_state.get('subscription_plan')
    if not plan_key:
        st.session_state['show_payment'] = False
        st.rerun()
    
    plan = ABONNEMENT_PLANS[plan_key]
    
    st.markdown(f"""
    <div style='text-align: center; padding: 20px; background: #F0FDF4; border-radius: 20px; margin-bottom: 20px;'>
        <h2 style='color: {plan["couleur"]};'>💳 Paiement - {plan["nom"]}</h2>
        <h3>{plan["prix_texte"]} - {plan["duree_jours"]} jours</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Formulaire coordonnées
    with st.expander("📝 Vos informations", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            nom_complet = st.text_input("Nom complet *", placeholder="Jean Diarra")
            telephone = st.text_input("Téléphone *", placeholder="XX XX XX XX XX")
        with col2:
            email = st.text_input("Email", placeholder="jean@email.com")
    
    st.markdown("---")
    st.markdown("### Choisissez votre mode de paiement")
    
    cols = st.columns(4)
    for idx, (key, mode) in enumerate(MODES_PAIEMENT.items()):
        with cols[idx]:
            if st.button(f"{mode['icon']}\n{mode['nom']}", key=f"mode_{key}", use_container_width=True):
                st.session_state['selected_mode'] = key
    
    mode_paiement = st.session_state.get('selected_mode')
    
    if mode_paiement:
        mode = MODES_PAIEMENT[mode_paiement]
        st.success(f"✅ Mode sélectionné: {mode['icon']} {mode['nom']}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💰 Procéder au paiement", use_container_width=True):
                if not nom_complet:
                    st.error("❌ Veuillez entrer votre nom complet")
                elif not telephone:
                    st.error("❌ Veuillez entrer votre numéro de téléphone")
                else:
                    transaction_id = creer_transaction(username, plan_key, mode_paiement, telephone, nom_complet, email)
                    st.session_state['current_transaction'] = transaction_id
                    st.rerun()
        with col2:
            if st.button("← Changer", use_container_width=True):
                del st.session_state['selected_mode']
                st.rerun()
    
    if st.button("← Retour aux offres", use_container_width=True):
        st.session_state['show_payment'] = False
        for key in ['subscription_plan', 'selected_mode', 'current_transaction']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()
    
    # Transaction en cours
    if 'current_transaction' in st.session_state:
        st.markdown("---")
        st.subheader("📋 Instructions de paiement")
        
        transaction = get_transaction(st.session_state['current_transaction'])
        if transaction:
            mode_info = MODES_PAIEMENT[transaction['mode_paiement']]
            st.info(f"""
            **Récapitulatif:**
            - Client: {transaction.get('nom_complet', 'N/A')}
            - Téléphone: {transaction.get('telephone', 'N/A')}
            - Plan: {transaction['plan']}
            - Montant: {transaction['montant']:,.0f} FCFA
            - ID: `{transaction['transaction_id']}`
            """)
            
            st.markdown(f"""
            **Instructions {mode_info['icon']} {mode_info['nom']}:**
            1. Ouvrez {mode_info['nom']}
            2. Payez {transaction['montant']:,.0f} FCFA
            3. Entrez le code reçu ci-dessous
            """)
            
            # QR Code
            qr_data = f"{mode_info['nom'].upper()}:TRADESAHEL:{transaction['transaction_id']}"
            qr_buf = generer_qr_code(qr_data)
            st.image(qr_buf.getvalue(), width=200, caption="Scannez pour payer")
            
            st.markdown("---")
            st.subheader("✅ Confirmation du paiement")
            st.caption("💡 **Code de test**: Entrez 123456 pour simuler le paiement")
            
            code = st.text_input("Code de confirmation reçu", placeholder="123456", type="password")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔓 Vérifier et activer mon abonnement", use_container_width=True):
                    if confirmer_transaction(st.session_state['current_transaction'], code):
                        st.success("🎉 Paiement confirmé ! Votre abonnement est activé.")
                        st.balloons()
                        for key in ['current_transaction', 'subscription_plan', 'show_payment', 'selected_mode']:
                            if key in st.session_state:
                                del st.session_state[key]
                        st.rerun()
                    else:
                        st.error("❌ Code invalide. Veuillez réessayer.")
            
            with col2:
                if st.button("❌ Annuler", use_container_width=True):
                    for key in ['current_transaction', 'subscription_plan', 'show_payment', 'selected_mode']:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.rerun()

def verifier_et_bloquer_si_necessaire(username: str) -> bool:
    """Vérifie l'abonnement et bloque l'accès si nécessaire"""
    init_subscription_tables()
    
    # Admin a toujours accès
    if username == "admin":
        return True
    
    # Vérifier abonnement valide
    if not est_abonnement_valide(username):
        if 'show_payment' in st.session_state and st.session_state['show_payment']:
            afficher_page_paiement(username)
        else:
            afficher_page_acces_bloque()
        return False
    
    return True

def admin_dashboard():
    """Dashboard administrateur"""
    st.subheader("👑 Administration des Abonnements")
    
    conn = sqlite3.connect("tradesahel.db")
    cursor = conn.cursor()
    
    # Vérifier si les tables existent
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='abonnements'")
    if not cursor.fetchone():
        st.info("Aucun abonnement enregistré")
        conn.close()
        return
    
    # Stats
    cursor.execute("SELECT COUNT(*) FROM abonnements WHERE statut='actif'")
    actifs = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM abonnements")
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(montant) FROM abonnements WHERE statut='actif'")
    result = cursor.fetchone()
    ca = result[0] if result and result[0] else 0
    
    col1, col2, col3 = st.columns(3)
    col1.metric("📊 Abonnés actifs", actifs)
    col2.metric("👥 Total abonnés", total)
    col3.metric("💰 CA mensuel", f"{ca:,.0f} FCFA")
    
    st.markdown("---")
    
    # Liste des abonnements
    st.subheader("📋 Abonnements actifs")
    cursor.execute("""
        SELECT username, plan, type_abonnement, date_debut, date_fin, montant
        FROM abonnements WHERE statut='actif' ORDER BY date_fin ASC
    """)
    rows = cursor.fetchall()
    conn.close()
    
    if rows:
        df = pd.DataFrame(rows, columns=["Utilisateur", "Plan", "Type", "Début", "Fin", "Montant"])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Aucun abonnement actif")

# Initialisation des tables
init_subscription_tables()