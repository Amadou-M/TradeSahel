"""
advanced_features.py - Fonctionnalités avancées pour TradeSahel
Version complète avec toutes les fonctions nécessaires
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import sqlite3
import hashlib
import requests
from io import BytesIO
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

# ====================== DASHBOARD EXÉCUTIF AVANCÉ ======================

def dashboard_executif_avance(df, devise="FCFA"):
    """Dashboard exécutif avec graphiques avancés"""
    
    st.subheader("📈 Tableau de Bord Exécutif")
    
    # Métriques clés
    col1, col2, col3, col4 = st.columns(4)
    
    ca_total = df['chiffre_affaires'].sum()
    qte_total = df['quantite'].sum() if 'quantite' in df.columns else 0
    nb_transactions = len(df)
    panier_moyen = ca_total / nb_transactions if nb_transactions > 0 else 0
    
    col1.metric("📊 CA Total", f"{ca_total:,.0f} {devise}", delta=None)
    col2.metric("📦 Quantité vendue", f"{qte_total:,.0f}", delta=None)
    col3.metric("🔄 Transactions", f"{nb_transactions:,}", delta=None)
    col4.metric("⭐ Panier moyen", f"{panier_moyen:,.0f} {devise}", delta=None)
    
    st.markdown("---")
    
    # Graphiques avancés
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Évolution", "🥧 Répartition", "📊 Top Produits", "📉 Tendances"])
    
    with tab1:
        # Évolution du CA
        df_date = df.groupby('date')['chiffre_affaires'].sum().reset_index()
        fig_evol = px.line(df_date, x='date', y='chiffre_affaires', 
                           title="Évolution du Chiffre d'Affaires",
                           labels={'chiffre_affaires': f'CA ({devise})', 'date': 'Date'})
        fig_evol.update_traces(line_color='#006400', line_width=2)
        fig_evol.add_hline(y=df_date['chiffre_affaires'].mean(), 
                          line_dash="dash", line_color="red",
                          annotation_text="Moyenne")
        st.plotly_chart(fig_evol, use_container_width=True)
        
        # Moyenne mobile sur 7 jours
        df_date['moyenne_7j'] = df_date['chiffre_affaires'].rolling(window=7, min_periods=1).mean()
        fig_mm = px.line(df_date, x='date', y=['chiffre_affaires', 'moyenne_7j'],
                        title="CA vs Moyenne Mobile 7 jours",
                        labels={'value': f'CA ({devise})', 'date': 'Date'})
        fig_mm.update_traces(line_width=2)
        st.plotly_chart(fig_mm, use_container_width=True)
    
    with tab2:
        col1, col2 = st.columns(2)
        
        with col1:
            if 'type_commerce' in df.columns:
                secteur_ca = df.groupby('type_commerce')['chiffre_affaires'].sum()
                fig_secteur = px.pie(values=secteur_ca.values, names=secteur_ca.index,
                                     title="Répartition par Secteur", hole=0.4)
                fig_secteur.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_secteur, use_container_width=True)
        
        with col2:
            if 'produit' in df.columns:
                top10 = df.groupby('produit')['chiffre_affaires'].sum().nlargest(10)
                fig_top10 = px.bar(x=top10.values, y=top10.index, orientation='h',
                                   title="Top 10 Produits",
                                   labels={'x': f'CA ({devise})', 'y': 'Produit'})
                fig_top10.update_traces(marker_color='#006400')
                st.plotly_chart(fig_top10, use_container_width=True)
    
    with tab3:
        if 'produit' in df.columns:
            # Matrice BCG
            produit_stats = df.groupby('produit').agg({
                'chiffre_affaires': 'sum',
                'quantite': 'sum'
            }).reset_index()
            
            # Calcul de la croissance (si assez de données)
            if len(df['date'].unique()) >= 2:
                dates = sorted(df['date'].unique())
                date_recente = dates[-1]
                date_ancienne = dates[0]
                
                ca_recent = df[df['date'] == date_recente].groupby('produit')['chiffre_affaires'].sum()
                ca_ancien = df[df['date'] == date_ancienne].groupby('produit')['chiffre_affaires'].sum()
                
                croissance = {}
                for produit in produit_stats['produit']:
                    ancien = ca_ancien.get(produit, 0)
                    recent = ca_recent.get(produit, 0)
                    if ancien > 0:
                        croissance[produit] = ((recent - ancien) / ancien) * 100
                    else:
                        croissance[produit] = 100 if recent > 0 else 0
                
                produit_stats['croissance'] = produit_stats['produit'].map(croissance)
            else:
                produit_stats['croissance'] = 0
            
            # Part de marché relative
            total_ca = produit_stats['chiffre_affaires'].sum()
            produit_stats['part_marche'] = (produit_stats['chiffre_affaires'] / total_ca) * 100
            
            # Classification BCG
            def bcg_classification(row):
                if row['croissance'] > 10 and row['part_marche'] > 10:
                    return "⭐ Vedette", "#22C55E"
                elif row['croissance'] <= 10 and row['part_marche'] > 10:
                    return "🐄 Vache à lait", "#F59E0B"
                elif row['croissance'] <= 10 and row['part_marche'] <= 10:
                    return "🐕 Poids mort", "#EF4444"
                else:
                    return "❓ Dilemme", "#F97316"
            
            produit_stats[['BCG', 'Couleur']] = produit_stats.apply(bcg_classification, axis=1, result_type='expand')
            
            fig_bcg = px.scatter(produit_stats, x='part_marche', y='croissance', 
                                 text='produit', color='BCG',
                                 color_discrete_map={
                                     "⭐ Vedette": "#22C55E",
                                     "🐄 Vache à lait": "#F59E0B",
                                     "🐕 Poids mort": "#EF4444",
                                     "❓ Dilemme": "#F97316"
                                 },
                                 title="Matrice BCG - Analyse Stratégique",
                                 labels={'part_marche': 'Part de marché (%)', 'croissance': 'Croissance (%)'})
            fig_bcg.add_hline(y=10, line_dash="dash", line_color="gray")
            fig_bcg.add_vline(x=10, line_dash="dash", line_color="gray")
            fig_bcg.update_traces(textposition='top center', marker=dict(size=15))
            st.plotly_chart(fig_bcg, use_container_width=True)
            
            # Tableau BCG
            st.dataframe(produit_stats[['produit', 'chiffre_affaires', 'croissance', 'part_marche', 'BCG']]
                        .style.format({'chiffre_affaires': '{:,.0f}', 'croissance': '{:.1f}%', 'part_marche': '{:.1f}%'})
                        .background_gradient(subset=['croissance'], cmap='RdYlGn'),
                        use_container_width=True, hide_index=True)
    
    with tab4:
        # Analyse des tendances
        col1, col2 = st.columns(2)
        
        with col1:
            # Tendance par jour de semaine
            jours = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
            df['jour_semaine'] = df['date'].dt.dayofweek
            df['jour_nom'] = df['jour_semaine'].map(lambda x: jours[x])
            tendance_jour = df.groupby('jour_nom')['chiffre_affaires'].sum().reindex(jours)
            
            fig_jour = px.bar(x=tendance_jour.index, y=tendance_jour.values,
                             title="Ventes par Jour de Semaine",
                             labels={'x': 'Jour', 'y': f'CA ({devise})'})
            fig_jour.update_traces(marker_color='#006400')
            st.plotly_chart(fig_jour, use_container_width=True)
        
        with col2:
            # Tendance par heure (si disponible)
            if 'heure' in df.columns:
                tendance_heure = df.groupby('heure')['chiffre_affaires'].sum()
                fig_heure = px.line(x=tendance_heure.index, y=tendance_heure.values,
                                   title="Ventes par Heure",
                                   labels={'x': 'Heure', 'y': f'CA ({devise})'})
                fig_heure.update_traces(line_color='#006400', line_width=2)
                st.plotly_chart(fig_heure, use_container_width=True)
            else:
                st.info("💡 Astuce: Ajoutez une colonne 'heure' pour voir les tendances horaires")


# ====================== RAPPORT PDF AVANCÉ ======================

def generer_rapport_pdf_avance(df, username, filename="rapport_complet.pdf"):
    """Génère un rapport PDF complet avec graphiques"""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, Image
    
    buf = BytesIO()
    
    # Créer les graphiques
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    # 1. CA par produit (top 10)
    if 'produit' in df.columns:
        top_produits = df.groupby('produit')['chiffre_affaires'].sum().nlargest(10)
        axes[0, 0].barh(range(len(top_produits)), top_produits.values, color='#006400')
        axes[0, 0].set_yticks(range(len(top_produits)))
        axes[0, 0].set_yticklabels(top_produits.index, fontsize=8)
        axes[0, 0].set_title('Top 10 Produits')
        axes[0, 0].set_xlabel('CA (FCFA)')
    
    # 2. Évolution du CA
    df_date = df.groupby('date')['chiffre_affaires'].sum().reset_index()
    axes[0, 1].plot(df_date['date'], df_date['chiffre_affaires'], color='#006400', linewidth=2)
    axes[0, 1].set_title('Évolution du CA')
    axes[0, 1].set_xlabel('Date')
    axes[0, 1].set_ylabel('CA (FCFA)')
    axes[0, 1].tick_params(axis='x', rotation=45)
    
    # 3. Répartition par secteur
    if 'type_commerce' in df.columns:
        secteur_ca = df.groupby('type_commerce')['chiffre_affaires'].sum()
        axes[1, 0].pie(secteur_ca.values, labels=secteur_ca.index, autopct='%1.1f%%', colors=['#006400', '#22C55E', '#4ADE80', '#86EFAC'])
        axes[1, 0].set_title('Répartition par Secteur')
    
    # 4. Ventes par jour de semaine
    jours = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
    df['jour_semaine'] = df['date'].dt.dayofweek
    df['jour_nom'] = df['jour_semaine'].map(lambda x: jours[x])
    tendance_jour = df.groupby('jour_nom')['chiffre_affaires'].sum().reindex(jours)
    axes[1, 1].bar(range(len(tendance_jour)), tendance_jour.values, color='#006400')
    axes[1, 1].set_xticks(range(len(tendance_jour)))
    axes[1, 1].set_xticklabels(tendance_jour.index, rotation=45)
    axes[1, 1].set_title('Ventes par Jour de Semaine')
    axes[1, 1].set_ylabel('CA (FCFA)')
    
    plt.tight_layout()
    
    # Sauvegarder le graphique en mémoire
    img_buf = BytesIO()
    plt.savefig(img_buf, format='png', dpi=150, bbox_inches='tight')
    img_buf.seek(0)
    plt.close()
    
    # Créer le PDF
    doc = SimpleDocTemplate(buf, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Titre
    title_style = ParagraphStyle('CustomTitle', parent=styles['Title'], fontSize=24, textColor=colors.HexColor('#006400'))
    story.append(Paragraph("TradeSahel - Rapport Commercial", title_style))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}", styles['Normal']))
    story.append(Spacer(1, 12))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#006400')))
    story.append(Spacer(1, 12))
    
    # KPIs
    kpi_data = [
        ["Indicateur", "Valeur"],
        ["CA Total", f"{df['chiffre_affaires'].sum():,.0f} FCFA"],
        ["Transactions", f"{len(df)}"],
        ["Panier moyen", f"{df['chiffre_affaires'].mean():,.0f} FCFA"]
    ]
    kpi_table = Table(kpi_data, colWidths=[8*cm, 8*cm])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#006400')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey)
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 12))
    
    # Graphique
    img = Image(img_buf, width=400, height=300)
    story.append(img)
    
    doc.build(story)
    buf.seek(0)
    return buf


# ====================== SYSTÈME DE NOTIFICATIONS ======================

def init_notification_tables():
    """Initialise les tables de notifications"""
    conn = sqlite3.connect("tradesahel.db")
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        titre TEXT NOT NULL,
        message TEXT NOT NULL,
        type TEXT DEFAULT 'info',
        est_lu INTEGER DEFAULT 0,
        date_creation TEXT NOT NULL,
        date_lecture TEXT
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS alertes_config (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        alert_stock BOOLEAN DEFAULT 1,
        alert_baisse_ca BOOLEAN DEFAULT 1,
        alert_expiration_abo BOOLEAN DEFAULT 1,
        email_notifications BOOLEAN DEFAULT 0,
        email_destinataire TEXT,
        seuil_stock INTEGER DEFAULT 10,
        seuil_baisse_ca INTEGER DEFAULT 20
    )
    """)
    
    conn.commit()
    conn.close()

def ajouter_notification(username: str, titre: str, message: str, type_notif: str = "info"):
    """Ajoute une notification pour un utilisateur"""
    conn = sqlite3.connect("tradesahel.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO notifications (username, titre, message, type, date_creation)
        VALUES (?, ?, ?, ?, ?)
    """, (username, titre, message, type_notif, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_notifications(username: str, non_lus_seulement: bool = False):
    """Récupère les notifications d'un utilisateur"""
    conn = sqlite3.connect("tradesahel.db")
    cursor = conn.cursor()
    
    if non_lus_seulement:
        cursor.execute("""
            SELECT id, titre, message, type, date_creation, est_lu
            FROM notifications 
            WHERE username=? AND est_lu=0
            ORDER BY date_creation DESC
        """, (username,))
    else:
        cursor.execute("""
            SELECT id, titre, message, type, date_creation, est_lu
            FROM notifications 
            WHERE username=?
            ORDER BY date_creation DESC
            LIMIT 50
        """, (username,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [{
        "id": r[0],
        "titre": r[1],
        "message": r[2],
        "type": r[3],
        "date": r[4],
        "est_lu": r[5]
    } for r in rows]

def marquer_notification_lue(notification_id: int):
    """Marque une notification comme lue"""
    conn = sqlite3.connect("tradesahel.db")
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE notifications 
        SET est_lu=1, date_lecture=?
        WHERE id=?
    """, (datetime.now().isoformat(), notification_id))
    conn.commit()
    conn.close()

def get_alertes_config(username: str):
    """Récupère la configuration des alertes"""
    conn = sqlite3.connect("tradesahel.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM alertes_config WHERE username=?", (username,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "alert_stock": row[2],
            "alert_baisse_ca": row[3],
            "alert_expiration_abo": row[4],
            "email_notifications": row[5],
            "email_destinataire": row[6],
            "seuil_stock": row[7],
            "seuil_baisse_ca": row[8]
        }
    return {
        "alert_stock": True,
        "alert_baisse_ca": True,
        "alert_expiration_abo": True,
        "email_notifications": False,
        "email_destinataire": "",
        "seuil_stock": 10,
        "seuil_baisse_ca": 20
    }

def sauvegarder_alertes_config(username: str, config: dict):
    """Sauvegarde la configuration des alertes"""
    conn = sqlite3.connect("tradesahel.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO alertes_config 
        (username, alert_stock, alert_baisse_ca, alert_expiration_abo, 
         email_notifications, email_destinataire, seuil_stock, seuil_baisse_ca)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (username, config['alert_stock'], config['alert_baisse_ca'], 
          config['alert_expiration_abo'], config['email_notifications'],
          config['email_destinataire'], config['seuil_stock'], config['seuil_baisse_ca']))
    conn.commit()
    conn.close()

def verifier_alertes_automatiques(username: str, df: pd.DataFrame):
    """Vérifie les alertes et crée des notifications"""
    config = get_alertes_config(username)
    
    # Alerte stock faible
    if config['alert_stock'] and 'stock' in df.columns:
        stocks_faibles = df[df['stock'] <= config['seuil_stock']]['produit'].unique()
        for produit in stocks_faibles:
            ajouter_notification(username, "⚠️ Stock faible", 
                                f"Le produit '{produit}' a un stock faible ({df[df['produit']==produit]['stock'].iloc[0]} unités restantes)",
                                "warning")
    
    # Alerte baisse CA
    if config['alert_baisse_ca'] and len(df['date'].unique()) >= 2:
        dates = sorted(df['date'].unique())
        ca_recent = df[df['date'] == dates[-1]]['chiffre_affaires'].sum()
        ca_ancien = df[df['date'] == dates[-2]]['chiffre_affaires'].sum()
        
        if ca_ancien > 0:
            baisse = ((ca_ancien - ca_recent) / ca_ancien) * 100
            if baisse >= config['seuil_baisse_ca']:
                ajouter_notification(username, "📉 Baisse du CA", 
                                    f"Baisse du chiffre d'affaires de {baisse:.1f}% par rapport à la période précédente",
                                    "danger")

def afficher_centre_notifications(username: str):
    """Affiche le centre de notifications"""
    st.subheader("🔔 Centre de Notifications")
    
    # Configuration des alertes
    with st.expander("⚙️ Configuration des alertes", expanded=False):
        config = get_alertes_config(username)
        
        col1, col2 = st.columns(2)
        with col1:
            alert_stock = st.checkbox("Alertes stock faible", value=config['alert_stock'])
            seuil_stock = st.slider("Seuil stock faible", 1, 50, config['seuil_stock'])
        
        with col2:
            alert_baisse = st.checkbox("Alertes baisse CA", value=config['alert_baisse_ca'])
            seuil_baisse = st.slider("Seuil baisse CA (%)", 5, 50, config['seuil_baisse_ca'])
        
        if st.button("💾 Sauvegarder configuration", use_container_width=True):
            nouvelle_config = {
                'alert_stock': alert_stock,
                'alert_baisse_ca': alert_baisse,
                'alert_expiration_abo': config['alert_expiration_abo'],
                'email_notifications': config['email_notifications'],
                'email_destinataire': config['email_destinataire'],
                'seuil_stock': seuil_stock,
                'seuil_baisse_ca': seuil_baisse
            }
            sauvegarder_alertes_config(username, nouvelle_config)
            st.success("Configuration sauvegardée !")
    
    st.markdown("---")
    
    # Liste des notifications
    notifications = get_notifications(username)
    
    if not notifications:
        st.info("Aucune notification")
    else:
        for notif in notifications:
            if notif['type'] == 'warning':
                icon = "⚠️"
                bg_color = "#FEF3C7"
            elif notif['type'] == 'danger':
                icon = "🔴"
                bg_color = "#FEE2E2"
            elif notif['type'] == 'success':
                icon = "✅"
                bg_color = "#DCFCE7"
            else:
                icon = "ℹ️"
                bg_color = "#DBEAFE"
            
            col1, col2 = st.columns([10, 1])
            with col1:
                st.markdown(f"""
                <div style='background: {bg_color}; border-radius: 10px; padding: 12px; margin-bottom: 10px;'>
                    <div style='display: flex; justify-content: space-between;'>
                        <div><strong>{icon} {notif['titre']}</strong></div>
                        <div style='font-size: 11px; color: #666;'>{notif['date'][:16]}</div>
                    </div>
                    <div style='margin-top: 5px;'>{notif['message']}</div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                if st.button("✓", key=f"mark_{notif['id']}"):
                    marquer_notification_lue(notif['id'])
                    st.rerun()


# ====================== MODE SOMBRE ======================

def appliquer_theme(theme="clair"):
    """Applique le thème choisi"""
    if theme == "sombre":
        st.markdown("""
        <style>
        .stApp {
            background-color: #1a1a2e;
        }
        .main > div {
            background-color: #1a1a2e;
        }
        .stMarkdown, .stText, .stMetric, .stDataFrame {
            color: #ffffff !important;
        }
        .stMetric > div {
            background-color: #16213e;
            border-radius: 10px;
            padding: 10px;
        }
        .stTabs [data-baseweb="tab-list"] {
            background-color: #16213e;
        }
        div[data-testid="stExpander"] {
            background-color: #16213e;
            border-radius: 10px;
        }
        </style>
        """, unsafe_allow_html=True)
    elif theme == "professionnel":
        st.markdown("""
        <style>
        .stApp {
            background-color: #f0fdf4;
        }
        .stMetric > div {
            background: linear-gradient(135deg, #ffffff, #f0fdf4);
            border: 1px solid #bbf7d0;
        }
        </style>
        """, unsafe_allow_html=True)


# ====================== ANALYSE SAISONNIÈRE ======================

def analyse_saisonnalite(df):
    """Analyse les tendances saisonnières"""
    st.subheader("📅 Analyse Saisonnière")
    
    df['mois'] = df['date'].dt.month
    df['annee'] = df['date'].dt.year
    df['trimestre'] = df['date'].dt.quarter
    
    tab1, tab2, tab3 = st.tabs(["📆 Par Mois", "📊 Par Trimestre", "📈 Comparaison Annuelle"])
    
    with tab1:
        # Ventes par mois
        ventes_mois = df.groupby('mois')['chiffre_affaires'].sum().reset_index()
        mois_noms = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin', 'Juil', 'Aoû', 'Sep', 'Oct', 'Nov', 'Déc']
        ventes_mois['mois_nom'] = ventes_mois['mois'].map(lambda x: mois_noms[x-1])
        
        fig_mois = px.bar(ventes_mois, x='mois_nom', y='chiffre_affaires',
                         title="Ventes par Mois",
                         labels={'chiffre_affaires': 'CA (FCFA)', 'mois_nom': 'Mois'})
        fig_mois.update_traces(marker_color='#006400')
        st.plotly_chart(fig_mois, use_container_width=True)
        
        # Détection du meilleur et pire mois
        meilleur_mois = ventes_mois.loc[ventes_mois['chiffre_affaires'].idxmax()]
        pire_mois = ventes_mois.loc[ventes_mois['chiffre_affaires'].idxmin()]
        
        col1, col2 = st.columns(2)
        col1.metric("📈 Meilleur mois", f"{meilleur_mois['mois_nom']}", f"{meilleur_mois['chiffre_affaires']:,.0f} FCFA")
        col2.metric("📉 Pire mois", f"{pire_mois['mois_nom']}", f"{pire_mois['chiffre_affaires']:,.0f} FCFA")
    
    with tab2:
        # Ventes par trimestre
        ventes_trimestre = df.groupby('trimestre')['chiffre_affaires'].sum().reset_index()
        fig_trimestre = px.bar(ventes_trimestre, x='trimestre', y='chiffre_affaires',
                              title="Ventes par Trimestre",
                              labels={'chiffre_affaires': 'CA (FCFA)', 'trimestre': 'Trimestre'})
        fig_trimestre.update_traces(marker_color='#006400')
        st.plotly_chart(fig_trimestre, use_container_width=True)
    
    with tab3:
        # Comparaison année par année
        if len(df['annee'].unique()) > 1:
            ventes_annee = df.groupby(['annee', 'mois'])['chiffre_affaires'].sum().reset_index()
            ventes_annee['mois_nom'] = ventes_annee['mois'].map(lambda x: mois_noms[x-1])
            
            fig_compare = px.line(ventes_annee, x='mois_nom', y='chiffre_affaires', color='annee',
                                 title="Comparaison Annuelle",
                                 labels={'chiffre_affaires': 'CA (FCFA)', 'mois_nom': 'Mois'})
            st.plotly_chart(fig_compare, use_container_width=True)
        else:
            st.info("📊 Ajoutez des données sur plusieurs années pour voir la comparaison")


# ====================== PARRAINAGE ======================

def init_parrainage_tables():
    """Initialise les tables de parrainage"""
    conn = sqlite3.connect("tradesahel.db")
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS parrainage (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code_parrain TEXT UNIQUE NOT NULL,
        parrain TEXT NOT NULL,
        filleul TEXT,
        date_creation TEXT NOT NULL,
        date_utilisation TEXT,
        est_utilise INTEGER DEFAULT 0
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS commissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        montant REAL NOT NULL,
        source TEXT NOT NULL,
        date TEXT NOT NULL,
        est_paye INTEGER DEFAULT 0
    )
    """)
    
    conn.commit()
    conn.close()

def generer_code_parrainage(username: str) -> str:
    """Génère un code de parrainage unique"""
    code = hashlib.md5(f"{username}{datetime.now().timestamp()}".encode()).hexdigest()[:8].upper()
    
    conn = sqlite3.connect("tradesahel.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO parrainage (code_parrain, parrain, date_creation)
        VALUES (?, ?, ?)
    """, (code, username, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    
    return code

def get_code_parrainage(username: str) -> str:
    """Récupère le code de parrainage d'un utilisateur"""
    conn = sqlite3.connect("tradesahel.db")
    cursor = conn.cursor()
    cursor.execute("SELECT code_parrain FROM parrainage WHERE parrain=? AND est_utilise=0", (username,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return row[0]
    return generer_code_parrainage(username)

def utiliser_code_parrainage(code: str, filleul: str) -> bool:
    """Utilise un code de parrainage"""
    conn = sqlite3.connect("tradesahel.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM parrainage WHERE code_parrain=? AND est_utilise=0", (code,))
    row = cursor.fetchone()
    
    if row:
        cursor.execute("""
            UPDATE parrainage 
            SET filleul=?, date_utilisation=?, est_utilise=1
            WHERE code_parrain=?
        """, (filleul, datetime.now().isoformat(), code))
        
        # Ajouter une commission au parrain
        cursor.execute("""
            INSERT INTO commissions (username, montant, source, date)
            VALUES (?, ?, ?, ?)
        """, (row[1], 5000, f"Parrainage de {filleul}", datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        return True
    
    conn.close()
    return False

def get_commissions(username: str) -> dict:
    """Récupère les commissions d'un utilisateur"""
    conn = sqlite3.connect("tradesahel.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT SUM(montant) FROM commissions WHERE username=? AND est_paye=0", (username,))
    total = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT id, montant, source, date FROM commissions WHERE username=? ORDER BY date DESC", (username,))
    rows = cursor.fetchall()
    conn.close()
    
    commissions = [{
        "id": r[0],
        "montant": r[1],
        "source": r[2],
        "date": r[3]
    } for r in rows]
    
    return {"total": total, "liste": commissions}

def afficher_interface_parrainage(username: str):
    """Affiche l'interface de parrainage"""
    st.subheader("🤝 Programme de Parrainage")
    
    # Générer le code
    code = get_code_parrainage(username)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Votre code de parrainage")
        st.code(code, language="text")
        st.caption("Partagez ce code avec vos amis")
        
        # Lien de parrainage
        url_parrainage = f"https://tradesahel.com/parrainage?code={code}"
        st.text_input("Lien de parrainage", value=url_parrainage, disabled=True)
    
    with col2:
        st.markdown("### Vos commissions")
        commissions = get_commissions(username)
        st.metric("💰 Commissions disponibles", f"{commissions['total']:,.0f} FCFA")
        
        if commissions['total'] > 0:
            if st.button("💸 Demander le paiement", use_container_width=True):
                st.success("Demande de paiement envoyée !")
    
    # Historique des parrainages
    st.markdown("---")
    st.markdown("### 📜 Historique")
    
    conn = sqlite3.connect("tradesahel.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT code_parrain, filleul, date_utilisation 
        FROM parrainage 
        WHERE parrain=? AND est_utilise=1
        ORDER BY date_utilisation DESC
    """, (username,))
    rows = cursor.fetchall()
    conn.close()
    
    if rows:
        for r in rows:
            st.markdown(f"✓ Parrainage de **{r[1]}** le {r[2][:10]}")
    else:
        st.info("Aucun parrainage pour le moment")
    
    st.markdown("---")
    st.markdown("""
    **Comment ça marche ?**
    1. Partagez votre code de parrainage
    2. Vos amis l'utilisent en s'inscrivant
    3. Vous recevez **5 000 FCFA** par filleul
    4. Accumulez et demandez votre paiement
    """)


# ====================== IMPORT API ======================

def interface_import_api():
    """Interface pour importer depuis une API"""
    st.subheader("🌐 Import depuis API externe")
    
    api_url = st.text_input("URL de l'API", placeholder="https://api.exemple.com/ventes")
    api_key = st.text_input("Clé API (optionnel)", type="password")
    
    if st.button("🔄 Tester la connexion", use_container_width=True):
        if api_url:
            with st.spinner("Connexion en cours..."):
                try:
                    headers = {}
                    if api_key:
                        headers["Authorization"] = f"Bearer {api_key}"
                    response = requests.get(api_url, headers=headers, timeout=10)
                    if response.status_code == 200:
                        st.success("✅ Connexion réussie !")
                        data = response.json()
                        if isinstance(data, list):
                            df_api = pd.DataFrame(data)
                            st.dataframe(df_api.head(10), use_container_width=True)
                            if st.button("📥 Importer ces données"):
                                return df_api
                        else:
                            st.warning("Format de données non reconnu")
                    else:
                        st.error(f"Erreur HTTP: {response.status_code}")
                except Exception as e:
                    st.error(f"Erreur: {e}")
        else:
            st.warning("Veuillez entrer une URL")
    
    return None


# ====================== EXPORT PDF SIMPLE ======================

def generer_pdf_simple(df, titre="Rapport"):
    """Génère un PDF simple à partir des données"""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Titre
    story.append(Paragraph(titre, styles['Title']))
    story.append(Spacer(1, 12))
    
    # KPIs
    kpi_data = [
        ["Indicateur", "Valeur"],
        ["CA Total", f"{df['chiffre_affaires'].sum():,.0f} FCFA"],
        ["Transactions", f"{len(df)}"],
        ["Panier moyen", f"{df['chiffre_affaires'].mean():,.0f} FCFA"]
    ]
    
    table = Table(kpi_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('GRID', (0,0), (-1,-1), 1, colors.black)
    ]))
    story.append(table)
    
    doc.build(story)
    buf.seek(0)
    return buf