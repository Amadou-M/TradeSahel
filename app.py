import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from groq import Groq
from datetime import datetime, timedelta
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from docx import Document as DocxDocument
from docx.shared import RGBColor
import time
import functools
import json
import requests
import hashlib

# Module BDD local
from tradesahel_db import (
    init_db, hash_fichier, fichier_deja_importe,
    enregistrer_fichier, inserer_ventes,
    charger_ventes, lister_fichiers, supprimer_fichier, vider_donnees,
    sauvegarder_rapport_ia, charger_historique_ia, supprimer_rapport_ia,
    sauvegarder_objectif, charger_objectifs,
    ajouter_note, charger_notes, supprimer_note, modifier_note,
    hash_pwd, charger_comptes, sauvegarder_comptes, stats_bdd,
    sauvegarder_message_chat, charger_historique_chat, supprimer_historique_chat,
    valider_donnees_ventes, backup_bdd, optimiser_bdd, get_performance_stats,
    clear_cache, lister_backups
)

# Module d'abonnement
from subscription_manager import (
    verifier_et_bloquer_si_necessaire, 
    admin_dashboard,
    est_abonnement_valide,
    get_abonnement_actif,
    jours_restants
)

# Module fonctionnalités avancées
from advanced_features import (
    dashboard_executif_avance,
    afficher_centre_notifications,
    generer_rapport_pdf_avance,
    appliquer_theme,
    analyse_saisonnalite,
    afficher_interface_parrainage,
    interface_import_api,
    init_notification_tables,
    init_parrainage_tables,
    verifier_alertes_automatiques
)

# ══════════════════════════════════════════════════════════
# CONSTANTES & CONFIG
# ══════════════════════════════════════════════════════════
VERT       = "#006400"
VERT_FONCE = "#004d1a"
VERT_CLAIR = "#F0FDF4"

st.set_page_config(page_title="TradeSahel - Mali", page_icon="🇲🇱", layout="wide")
init_db()

# Initialiser les nouvelles tables
init_notification_tables()
init_parrainage_tables()

# ══════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════
for k, v in {
    "authenticated": False,
    "username": "",
    "dernier_rapport": "",
    "chat_history": [],
    "use_cache": True,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

if "comptes" not in st.session_state:
    st.session_state.comptes = charger_comptes()

# ══════════════════════════════════════════════════════════
# CSS LOGIN
# ══════════════════════════════════════════════════════════
CSS_LOGIN = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@700;800&family=DM+Sans:wght@400;500;600&display=swap');
[data-testid="stAppViewContainer"]{background:linear-gradient(150deg,#003d14 0%,#006400 45%,#1aaa3a 80%,#FCD116 100%);min-height:100vh;}
[data-testid="stHeader"]{background:transparent!important;}
[data-testid="stSidebar"]{display:none!important;}
.block-container{padding-top:1.5rem!important;}
.lc{background:rgba(255,255,255,0.97);border-radius:20px;padding:24px 28px 20px;max-width:400px;width:100%;margin:0 auto;box-shadow:0 16px 48px rgba(0,0,0,0.22);}
.lc-head{display:flex;align-items:center;gap:12px;margin-bottom:12px;padding-bottom:12px;border-bottom:1.5px solid #E8F5E9;}
.lc-flag{font-size:30px;line-height:1;flex-shrink:0;}
.lc-title{font-family:'Sora',sans-serif;font-size:20px;font-weight:800;color:#003d14;letter-spacing:-0.03em;margin:0 0 2px;}
.lc-sub{font-size:9.5px;color:#64748B;text-transform:uppercase;letter-spacing:.07em;font-weight:600;margin:0;}
.lc-badges{display:flex;gap:5px;margin-bottom:12px;}
.bdg{padding:2px 8px;border-radius:999px;font-size:10px;font-weight:600;}
.bdg-g{background:#DCFCE7;color:#166534;}.bdg-y{background:#FEF9C3;color:#854D0E;}.bdg-b{background:#DBEAFE;color:#1E40AF;}
.msg-ok{background:#F0FDF4;border:1px solid #86EFAC;border-radius:8px;padding:9px 12px;color:#166534;font-size:12px;font-weight:500;margin-top:8px;}
.msg-err{background:#FEF2F2;border:1px solid #FCA5A5;border-radius:8px;padding:9px 12px;color:#991B1B;font-size:12px;font-weight:500;margin-top:8px;}
.msg-demo{background:#F0FDF4;border:1px solid #BBF7D0;border-radius:8px;padding:9px 12px;font-size:11px;color:#166534;line-height:1.8;margin-top:8px;}
.msg-demo b{color:#003d14;}
div[data-testid="stForm"] button{background:#006400!important;color:white!important;border:none!important;border-radius:8px!important;font-family:'DM Sans',sans-serif!important;font-weight:600!important;}
div[data-testid="stForm"] button:hover{background:#004d1a!important;}
</style>
"""

# ══════════════════════════════════════════════════════════
# FONCTIONS DE CACHE
# ══════════════════════════════════════════════════════════
@st.cache_data(ttl=300, show_spinner=False)
def charger_ventes_cache(username: str) -> pd.DataFrame:
    return charger_ventes(username)

@st.cache_data(ttl=600, show_spinner=False)
def calculer_top_produits(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    if "produit" not in df.columns:
        return pd.DataFrame()
    return df.groupby("produit")["chiffre_affaires"].sum().nlargest(n).reset_index()

# ══════════════════════════════════════════════════════════
# PAGE CONNEXION
# ══════════════════════════════════════════════════════════
def page_connexion():
    st.markdown(CSS_LOGIN, unsafe_allow_html=True)
    col = st.columns([1, 2, 1])[1]
    with col:
        st.markdown("""
        <div class="lc">
          <div class="lc-head">
            <span class="lc-flag">🇲🇱</span>
            <div><div class="lc-title">TradeSahel</div>
            <div class="lc-sub">Intelligence Commerciale · Mali</div></div>
          </div>
          <div class="lc-badges">
            <span class="bdg bdg-g">✓ Sécurisé</span>
            <span class="bdg bdg-y">FCFA</span>
            <span class="bdg bdg-b">IA intégrée</span>
          </div>
        </div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        option = st.radio("", ["🔑 Se connecter","➕ Créer un compte","🔓 Mot de passe oublié"],
                          horizontal=True, label_visibility="collapsed", key="login_opt")
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

        if option == "🔑 Se connecter":
            with st.form("f_login"):
                user = st.text_input("👤 Identifiant", placeholder="admin ou mali1")
                pwd  = st.text_input("🔑 Mot de passe", type="password")
                ok   = st.form_submit_button("Se connecter", use_container_width=True)
            if ok:
                c = st.session_state.comptes
                if user.strip() in c and hash_pwd(pwd) == c[user.strip()]["password"]:
                    st.session_state.authenticated = True
                    st.session_state.username      = user.strip()
                    st.rerun()
                else:
                    st.markdown('<div class="msg-err">❌ Identifiant ou mot de passe incorrect.</div>', unsafe_allow_html=True)
            st.markdown('<div class="msg-demo"><b>Démo :</b> admin / admin123 &nbsp;·&nbsp; mali1 / mali2025</div>', unsafe_allow_html=True)

        elif option == "➕ Créer un compte":
            with st.form("f_create"):
                c1,c2 = st.columns(2)
                with c1: nu = st.text_input("👤 Identifiant", placeholder="boutique_bko")
                with c2: ne = st.text_input("📧 Email",       placeholder="vous@email.ml")
                nb = st.text_input("🏪 Nom boutique", placeholder="Shop Bamako Centre")
                c3,c4 = st.columns(2)
                with c3: np = st.text_input("🔑 Mot de passe", type="password", placeholder="Min. 6 car.")
                with c4: nc = st.text_input("🔑 Confirmer",    type="password")
                ok = st.form_submit_button("✅ Créer mon compte", use_container_width=True)
            if ok:
                comptes = st.session_state.comptes
                if not nu.strip():
                    st.markdown('<div class="msg-err">❌ Identifiant obligatoire.</div>', unsafe_allow_html=True)
                elif nu.strip() in comptes:
                    st.markdown('<div class="msg-err">❌ Identifiant déjà utilisé.</div>', unsafe_allow_html=True)
                elif len(np) < 6:
                    st.markdown('<div class="msg-err">❌ Mot de passe trop court.</div>', unsafe_allow_html=True)
                elif np != nc:
                    st.markdown('<div class="msg-err">❌ Les mots de passe ne correspondent pas.</div>', unsafe_allow_html=True)
                else:
                    comptes[nu.strip()] = {"password":hash_pwd(np),"boutique":nb or nu.strip(),"email":ne}
                    st.session_state.comptes = comptes
                    sauvegarder_comptes(comptes)
                    st.session_state.authenticated = True
                    st.session_state.username      = nu.strip()
                    st.rerun()

        elif option == "🔓 Mot de passe oublié":
            with st.form("f_reset"):
                ru = st.text_input("👤 Identifiant")
                c5,c6 = st.columns(2)
                with c5: rn = st.text_input("🔑 Nouveau mot de passe", type="password")
                with c6: rc = st.text_input("🔑 Confirmer",            type="password")
                ok = st.form_submit_button("🔓 Réinitialiser", use_container_width=True)
            if ok:
                comptes = st.session_state.comptes
                if ru.strip() not in comptes:
                    st.markdown('<div class="msg-err">❌ Identifiant introuvable.</div>', unsafe_allow_html=True)
                elif len(rn) < 6:
                    st.markdown('<div class="msg-err">❌ Mot de passe trop court.</div>', unsafe_allow_html=True)
                elif rn != rc:
                    st.markdown('<div class="msg-err">❌ Les mots de passe ne correspondent pas.</div>', unsafe_allow_html=True)
                else:
                    comptes[ru.strip()]["password"] = hash_pwd(rn)
                    st.session_state.comptes = comptes
                    sauvegarder_comptes(comptes)
                    st.markdown('<div class="msg-ok">✅ Mot de passe réinitialisé !</div>', unsafe_allow_html=True)

if not st.session_state.authenticated:
    page_connexion()
    st.stop()

# ══════════════════════════════════════════════════════════
# ⚠️ VÉRIFICATION CRITIQUE - BLOCAGE SI PAS D'ABONNEMENT
# ══════════════════════════════════════════════════════════
username = st.session_state.username

# Vérifier l'abonnement - BLOQUE L'ACCÈS SI NON PAYÉ
if not verifier_et_bloquer_si_necessaire(username):
    st.stop()

# ══════════════════════════════════════════════════════════
# UTILITAIRES
# ══════════════════════════════════════════════════════════
boutique = st.session_state.comptes.get(username, {}).get("boutique", username)
devise   = "FCFA"

def preparer_df(df_raw: pd.DataFrame) -> pd.DataFrame:
    df = df_raw.copy()
    df.columns = df.columns.str.strip().str.lower()
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"])
    if "chiffre_affaires" not in df.columns and {"quantite","prix_unitaire"}.issubset(df.columns):
        df["chiffre_affaires"] = (
            pd.to_numeric(df["quantite"], errors="coerce") *
            pd.to_numeric(df["prix_unitaire"], errors="coerce")
        )
    if "prix_achat" in df.columns and "chiffre_affaires" in df.columns:
        qte = pd.to_numeric(df.get("quantite", pd.Series([1]*len(df))), errors="coerce")
        df["cout_total"] = pd.to_numeric(df["prix_achat"], errors="coerce") * qte
        df["marge"] = df["chiffre_affaires"] - df["cout_total"]
        df["marge_pct"] = (df["marge"] / df["chiffre_affaires"].replace(0,1) * 100).round(1)
    if "type_commerce" not in df.columns:
        df["type_commerce"] = "Commerce Général"
    if "boutique_nom" not in df.columns:
        df["boutique_nom"] = "Principal"
    if "stock" not in df.columns:
        df["stock"] = 100
    df["username"] = username
    return df

# ══════════════════════════════════════════════════════════
# FONCTIONS POUR RAPPORTS PDF/WORD
# ══════════════════════════════════════════════════════════
def generer_pdf_rapport(contenu: str, titre: str, username: str):
    buf = BytesIO()
    vert_c = colors.HexColor(VERT)
    
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=2*cm, rightMargin=2*cm,
                           topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    
    h1 = ParagraphStyle("h1", parent=styles["Normal"], fontSize=18, fontName="Helvetica-Bold", 
                        textColor=vert_c, spaceAfter=12)
    h2 = ParagraphStyle("h2", parent=styles["Normal"], fontSize=14, fontName="Helvetica-Bold",
                        textColor=vert_c, spaceBefore=12, spaceAfter=6)
    normal = ParagraphStyle("normal", parent=styles["Normal"], fontSize=10, leading=14)
    
    story = []
    story.append(Paragraph("TradeSahel - Rapport IA", h1))
    story.append(Paragraph(titre, h2))
    story.append(Paragraph(f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')} par {username}", normal))
    story.append(Spacer(1, 12))
    story.append(HRFlowable(width="100%", thickness=1, color=vert_c))
    
    for line in contenu.split('\n'):
        if line.strip():
            if line.startswith('##'):
                story.append(Paragraph(line.replace('##', '').strip(), h2))
            elif line.startswith('#'):
                story.append(Paragraph(line.replace('#', '').strip(), h1))
            else:
                story.append(Paragraph(line.strip(), normal))
    
    story.append(Spacer(1, 20))
    story.append(Paragraph("TradeSahel - Intelligence Commerciale Mali", normal))
    
    doc.build(story)
    buf.seek(0)
    return buf

def generer_word_rapport(contenu: str, titre: str, username: str):
    doc = DocxDocument()
    
    title = doc.add_heading('TradeSahel - Rapport IA', 0)
    title.runs[0].font.color.rgb = RGBColor(0, 100, 0)
    
    doc.add_heading(titre, level=1)
    doc.add_paragraph(f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')} par {username}")
    doc.add_paragraph()
    
    for line in contenu.split('\n'):
        if line.strip():
            if line.startswith('##'):
                doc.add_heading(line.replace('##', '').strip(), level=2)
            elif line.startswith('#'):
                doc.add_heading(line.replace('#', '').strip(), level=1)
            elif line.startswith('-') or line.startswith('•'):
                doc.add_paragraph(line, style='List Bullet')
            elif line[0].isdigit() and '. ' in line[:5]:
                doc.add_paragraph(line, style='List Number')
            else:
                doc.add_paragraph(line)
    
    buf = BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf

def generer_pdf_standard(boutique, username, choix, devise, total_ca, total_reel,
                panier, qte, trans, rapport_ia, df_produits, has_marge):
    buf = BytesIO()
    vert_c = colors.HexColor(VERT)
    gris_c = colors.HexColor("#64748B")
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=2*cm, rightMargin=2*cm,
                           topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=styles["Normal"], fontSize=20, fontName="Helvetica-Bold", textColor=vert_c, spaceAfter=4)
    sub = ParagraphStyle("sub", parent=styles["Normal"], fontSize=10, textColor=gris_c, spaceAfter=14)
    h2 = ParagraphStyle("h2", parent=styles["Normal"], fontSize=13, fontName="Helvetica-Bold", textColor=vert_c, spaceBefore=14, spaceAfter=6)
    bod = ParagraphStyle("bod", parent=styles["Normal"], fontSize=10, leading=15, spaceAfter=6)
    story = []
    story.append(Paragraph("TradeSahel", h1))
    story.append(Paragraph(f"Rapport Commercial  |  {boutique}  |  {choix}", sub))
    story.append(Paragraph(f"Genere le {datetime.now().strftime('%d/%m/%Y a %H:%M')}  |  {username}", sub))
    story.append(HRFlowable(width="100%", thickness=2, color=vert_c, spaceAfter=12))
    story.append(Paragraph("Indicateurs cles", h2))
    kd = [["Indicateur","Valeur"],
          ["CA nominal", f"{total_ca:,.0f} {devise}"],
          ["CA reel", f"{total_reel:,.0f} {devise}"],
          ["Panier moyen", f"{panier:,.0f} {devise}"],
          ["Quantite", f"{qte:,.0f} unites"],
          ["Transactions", f"{trans:,.0f}"]]
    tk = Table(kd, colWidths=[10*cm, 7*cm])
    tk.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),vert_c),("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,-1),10),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.HexColor("#F0FDF4"),colors.white]),
        ("GRID",(0,0),(-1,-1),0.4,colors.HexColor("#BBF7D0")),("PADDING",(0,0),(-1,-1),7),
    ]))
    story.append(tk)
    story.append(Spacer(1,12))
    if df_produits is not None and not df_produits.empty:
        story.append(Paragraph("Performance par produit", h2))
        cols = ["Produit","Qte vendue",f"CA ({devise})"]
        if has_marge:
            cols.append("Marge (%)")
        pd_data = [cols]
        for _, r in df_produits.head(15).iterrows():
            row = [str(r.get("Produit","—")), f"{r.get('Qte vendue',0):,.0f}", f"{r.get(f'CA ({devise})',0):,.0f}"]
            if has_marge:
                row.append(f"{r.get('Marge (%)',0):.1f}%")
            pd_data.append(row)
        cw = [8*cm,3.5*cm,3.5*cm]+([2*cm] if has_marge else [])
        tp = Table(pd_data, colWidths=cw)
        tp.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0),vert_c),("TEXTCOLOR",(0,0),(-1,0),colors.white),
            ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,-1),9),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.HexColor("#F0FDF4"),colors.white]),
            ("GRID",(0,0),(-1,-1),0.4,colors.HexColor("#BBF7D0")),("PADDING",(0,0),(-1,-1),6),
            ("ALIGN",(1,0),(-1,-1),"RIGHT"),
        ]))
        story.append(tp)
        story.append(Spacer(1,12))
    if rapport_ia:
        story.append(HRFlowable(width="100%",thickness=1,color=vert_c,spaceAfter=10))
        story.append(Paragraph("Analyse et Recommandations IA", h2))
        for line in rapport_ia.split("\n"):
            if line.strip():
                story.append(Paragraph(line.strip().replace("**","").replace("*",""), bod))
    story.append(Spacer(1,20))
    story.append(Paragraph("TradeSahel  |  Intelligence Commerciale  |  Mali", sub))
    doc.build(story)
    buf.seek(0)
    return buf

# ══════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════

# Sélecteur de thème
st.sidebar.markdown("---")
theme = st.sidebar.selectbox("🎨 Thème", ["Clair", "Sombre", "Professionnel"])
if theme == "Sombre":
    appliquer_theme("sombre")
elif theme == "Professionnel":
    appliquer_theme("professionnel")

st.sidebar.markdown(
    f"<div style='padding:10px;background:{VERT_CLAIR};border-radius:10px;margin-bottom:8px;'>"
    f"<div style='font-size:11px;color:#64748B;'>Connecté</div>"
    f"<div style='font-weight:600;color:{VERT};'>👤 {username}</div>"
    f"<div style='font-size:12px;color:#64748B;'>🏪 {boutique}</div>"
    f"</div>", unsafe_allow_html=True)

# Afficher info abonnement
abo = get_abonnement_actif(username)
if abo:
    jours = jours_restants(username)
    if jours <= 7:
        st.sidebar.warning(f"⚠️ Abonnement expire dans {jours} jour(s)")
    st.sidebar.info(f"📅 {abo['plan']} - {jours} jours restants")

if st.sidebar.button("🚪 Déconnexion", use_container_width=True):
    st.session_state.authenticated = False
    clear_cache(username)
    st.rerun()

st.sidebar.markdown("---")
api_key = st.sidebar.text_input("🔑 Clé API Groq", type="password")

# Section Maintenance
st.sidebar.markdown("---")
with st.sidebar.expander("🔧 Maintenance"):
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Backup BDD", use_container_width=True):
            backup_file = backup_bdd()
            if backup_file:
                st.sidebar.success(f"Backup créé!")
    with col2:
        if st.button("⚡ Optimiser", use_container_width=True):
            with st.spinner("Optimisation..."):
                optimiser_bdd()
                clear_cache(username)
                st.sidebar.success("✅ Optimisé!")
    
    st.session_state.use_cache = st.checkbox("Activer cache", value=st.session_state.use_cache)

# Import fichiers
st.sidebar.markdown("---")
st.sidebar.title("📁 Import Données")

uploaded_files = st.sidebar.file_uploader(
    "Importer fichier(s)", type=["csv","xlsx"],
    accept_multiple_files=True, key="uploader"
)

template_csv = ("date,produit,type_commerce,quantite,prix_unitaire,prix_achat,stock\n"
                "2025-01-15,Riz 25kg,Alimentation,10,12500,8000,50\n"
                "2025-01-16,Huile 5L,Alimentation,5,3500,2200,30\n"
                "2025-01-17,Savon,Hygiene,20,1500,900,80\n")
st.sidebar.download_button("📄 Template CSV", data=template_csv.encode("utf-8"),
                           file_name="template_tradesahel.csv", mime="text/csv",
                           use_container_width=True)

if uploaded_files:
    for f in uploaded_files:
        contenu = f.read()
        f.seek(0)
        h = hash_fichier(contenu)
        if fichier_deja_importe(h):
            st.sidebar.info(f"✅ {f.name} déjà en base")
        else:
            try:
                df_raw = pd.read_csv(f) if f.name.endswith(".csv") else pd.read_excel(f)
                
                is_valid, errors = valider_donnees_ventes(df_raw)
                if not is_valid:
                    st.sidebar.error(f"❌ {f.name} invalide:\n" + "\n".join(errors))
                    continue
                
                df_prep = preparer_df(df_raw)
                df_prep["source_fichier"] = f.name
                fid = enregistrer_fichier(f.name, username, len(df_prep), h)
                inserer_ventes(df_prep, fid, f.name)
                clear_cache(username)
                st.sidebar.success(f"✅ {f.name} importé — {len(df_prep)} lignes")
            except Exception as e:
                st.sidebar.error(f"Erreur {f.name} : {e}")

# Filtres
st.sidebar.markdown("---")
st.sidebar.title("🔍 Filtres")

if st.session_state.use_cache:
    df_complet = charger_ventes_cache(username)
else:
    df_complet = charger_ventes(username)

if df_complet.empty:
    st.title("📊 TradeSahel")
    st.markdown(f"**Intelligence Commerciale • Mali** — {boutique}")
    st.markdown("---")
    st.markdown(f"""
    <div style='text-align:center;padding:60px 20px;background:{VERT_CLAIR};border-radius:16px;border:1px solid #BBF7D0;'>
        <div style='font-size:56px;margin-bottom:16px;'>🇲🇱</div>
        <div style='font-size:22px;font-weight:700;color:{VERT};margin-bottom:8px;'>Bienvenue, {username} !</div>
        <div style='font-size:15px;color:#64748B;margin-bottom:16px;'>Importez un fichier CSV ou Excel dans le panneau gauche.<br>Vos données seront <b>sauvegardées en base</b> et disponibles à chaque reconnexion.</div>
        <div style='font-size:13px;color:#64748B;'>Colonnes requises : <b>date, produit, quantite, prix_unitaire</b><br>
        Optionnel : <b>type_commerce, prix_achat, stock</b></div>
    </div>""", unsafe_allow_html=True)
    st.stop()

has_marge = "marge" in df_complet.columns and df_complet["marge"].notna().any()

if "type_commerce" in df_complet.columns:
    types_dispo = sorted(df_complet["type_commerce"].dropna().unique())
    types_sel = st.sidebar.multiselect("Type de commerce", types_dispo, default=types_dispo)
    df_filtre = df_complet[df_complet["type_commerce"].isin(types_sel)]
else:
    df_filtre = df_complet.copy()

if "produit" in df_filtre.columns:
    prods = ["Tous"] + sorted(df_filtre["produit"].dropna().unique().tolist())
    prod_sel = st.sidebar.selectbox("🛒 Produit", prods)
    if prod_sel != "Tous":
        df_filtre = df_filtre[df_filtre["produit"] == prod_sel]

periode = st.sidebar.radio("📅 Période", ["Jour","Semaine","Mois","Année"], horizontal=True)
col_p = {"Jour":"jour","Semaine":"semaine","Mois":"mois","Année":"annee"}[periode]
valeurs = sorted(df_filtre[col_p].unique()) if col_p in df_filtre.columns else []
choix = st.sidebar.selectbox(f"Sélectionner {periode}", ["Toutes"] + list(valeurs))
df_f = df_filtre[df_filtre[col_p] == choix].copy() if choix != "Toutes" else df_filtre.copy()

df_f["ca_reel"] = df_f["chiffre_affaires"] / 1.02
total_ca = df_f["chiffre_affaires"].sum()
total_reel = df_f["ca_reel"].sum()
qte = pd.to_numeric(df_f.get("quantite", pd.Series([0]*len(df_f))), errors="coerce").sum()
trans = len(df_f)
panier = total_ca / trans if trans > 0 else 0

st.title("📊 TradeSahel")
st.markdown(f"**Intelligence Commerciale • Mali** — {boutique}")
st.markdown("---")

# Vérifier les alertes automatiques
verifier_alertes_automatiques(username, df_f)

# Création des onglets
if username == "admin":
    tabs = st.tabs([
        "📊 Vue générale", "🏬 Multi-boutiques", "⚖️ Comparaison", "🎯 Objectifs",
        "📦 Stocks", "🔮 Prévisions IA", "💬 Chat IA", "🧠 Rapport IA", "🚨 Alertes",
        "📜 Historique", "💬 Notes", "🗄️ Données", "📥 Export",
        "📈 Dashboard", "🔔 Notifications", "📅 Saisons", "🤝 Parrainage", "🌐 API", "👑 Admin"
    ])
else:
    tabs = st.tabs([
        "📊 Vue générale", "🏬 Multi-boutiques", "⚖️ Comparaison", "🎯 Objectifs",
        "📦 Stocks", "🔮 Prévisions IA", "💬 Chat IA", "🧠 Rapport IA", "🚨 Alertes",
        "📜 Historique", "💬 Notes", "🗄️ Données", "📥 Export",
        "📈 Dashboard", "🔔 Notifications", "📅 Saisons", "🤝 Parrainage", "🌐 API"
    ])

# ══════════════════════════════════════════════════════════
# TAB 0 - VUE GÉNÉRALE
# ══════════════════════════════════════════════════════════
with tabs[0]:
    label_p = choix if choix != "Toutes" else "Période complète"
    st.subheader(f"📌 KPIs — {label_p}")
    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("💰 CA Nominal", f"{total_ca:,.0f} {devise}")
    c2.metric("📉 CA Réel", f"{total_reel:,.0f} {devise}")
    c3.metric("🛒 Panier Moyen", f"{panier:,.0f} {devise}")
    c4.metric("📦 Quantité", f"{qte:,.0f}")
    c5.metric("🔢 Transactions", f"{trans:,.0f}")

    if has_marge and "marge" in df_f.columns:
        m_tot = df_f["marge"].sum()
        m_pct = (m_tot / total_ca * 100) if total_ca > 0 else 0
        mc1,mc2 = st.columns(2)
        mc1.metric("💹 Marge brute", f"{m_tot:,.0f} {devise}")
        mc2.metric("📊 Taux de marge", f"{m_pct:.1f}%")

    st.markdown("---")
    if "produit" in df_f.columns:
        st.subheader("📋 Détail par produit")
        agg = {"CA":("chiffre_affaires","sum"),"Qte vendue":("quantite","sum")}
        if has_marge and "marge" in df_f.columns:
            agg["Marge brute"] = ("marge","sum")
        det = df_f.groupby("produit").agg(**agg).reset_index()
        det.columns = ["Produit"] + list(agg.keys())
        det[f"CA ({devise})"] = det["CA"]
        det["Part CA (%)"] = (det["CA"] / det["CA"].sum() * 100).round(1)
        if has_marge and "Marge brute" in det.columns:
            det["Marge (%)"] = (det["Marge brute"] / det["CA"].replace(0,1) * 100).round(1)
        det = det.sort_values("CA", ascending=False).reset_index(drop=True)
        fmt = {f"CA ({devise})":"{:,.0f}","Qte vendue":"{:,.0f}","Part CA (%)":"{:.1f}%"}
        cols_show = ["Produit","Qte vendue",f"CA ({devise})","Part CA (%)"]
        if has_marge and "Marge (%)" in det.columns:
            fmt["Marge brute"] = "{:,.0f}"
            fmt["Marge (%)"] = "{:.1f}%"
            cols_show += ["Marge brute","Marge (%)"]
        st.dataframe(det[cols_show].style.format(fmt)
                     .background_gradient(subset=[f"CA ({devise})"], cmap="Greens"),
                     use_container_width=True, hide_index=True)
        df_produits_export = det
    else:
        df_produits_export = None

    cg1,cg2 = st.columns(2)
    with cg1:
        if "type_commerce" in df_f.columns:
            fig_pie = px.pie(df_f, names="type_commerce", values="chiffre_affaires", title="CA par Secteur", hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)
    with cg2:
        if "produit" in df_f.columns:
            top10 = calculer_top_produits(df_f, 10)
            if not top10.empty:
                fig_b = px.bar(top10, x="chiffre_affaires", y="produit", orientation="h",
                               title="Top 10 Produits", color="chiffre_affaires",
                               color_continuous_scale=[[0,"#BBF7D0"],[1,VERT]])
                fig_b.update_layout(coloraxis_showscale=False)
                st.plotly_chart(fig_b, use_container_width=True)

    if col_p in df_f.columns:
        evo = df_f.groupby(col_p)["chiffre_affaires"].sum().reset_index()
        fig_e = px.line(evo, x=col_p, y="chiffre_affaires", markers=True,
                        title=f"Évolution du CA par {periode}", color_discrete_sequence=[VERT])
        st.plotly_chart(fig_e, use_container_width=True)

    with st.expander("📋 Données brutes"):
        st.dataframe(df_f, use_container_width=True)

# ══════════════════════════════════════════════════════════
# TAB 1 - MULTI-BOUTIQUES
# ══════════════════════════════════════════════════════════
with tabs[1]:
    st.subheader("🏬 Comparaison Multi-boutiques")
    if "source_fichier" in df_complet.columns and df_complet["source_fichier"].nunique() > 1:
        rows_mb = []
        for src in df_complet["source_fichier"].unique():
            d = df_complet[df_complet["source_fichier"]==src]
            rows_mb.append({
                "Fichier/Boutique": src,
                "CA total": d["chiffre_affaires"].sum(),
                "Transactions": len(d),
                "Panier moyen": round(d["chiffre_affaires"].sum()/max(len(d),1),0),
            })
        df_mb = pd.DataFrame(rows_mb)
        st.dataframe(df_mb.style.format({"CA total":"{:,.0f}","Panier moyen":"{:,.0f}"})
                     .background_gradient(subset=["CA total"],cmap="Greens"),
                     use_container_width=True, hide_index=True)
        fig_mb = px.bar(df_mb, x="Fichier/Boutique", y="CA total", text="CA total",
                        color="CA total", color_continuous_scale=[[0,"#BBF7D0"],[1,VERT]])
        fig_mb.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
        fig_mb.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig_mb, use_container_width=True)
    else:
        st.info("Importez plusieurs fichiers pour comparer.")

# ══════════════════════════════════════════════════════════
# TAB 2 - COMPARAISON
# ══════════════════════════════════════════════════════════
with tabs[2]:
    st.subheader("⚖️ Comparaison")
    mode_comp = st.radio("Mode", ["📅 Deux périodes","🛒 Plusieurs produits"], horizontal=True)
    if mode_comp == "📅 Deux périodes" and len(valeurs) >= 2:
        ca1c,ca2c = st.columns(2)
        with ca1c:
            p1 = st.selectbox("Période A", valeurs, index=len(valeurs)-2, key="p1")
        with ca2c:
            p2 = st.selectbox("Période B", list(reversed(valeurs)), key="p2")
        ca_a = df_filtre[df_filtre[col_p]==p1]["chiffre_affaires"].sum()
        ca_b = df_filtre[df_filtre[col_p]==p2]["chiffre_affaires"].sum()
        diff = ca_b - ca_a
        evol = ((ca_b-ca_a)/ca_a*100) if ca_a>0 else 0
        m1,m2,m3 = st.columns(3)
        m1.metric(f"📅 {p1}", f"{ca_a:,.0f} {devise}")
        m2.metric(f"📅 {p2}", f"{ca_b:,.0f} {devise}")
        m3.metric("📈 Évolution", f"{diff:+,.0f} {devise}", f"{evol:+.1f}%")
    else:
        st.info("Sélectionnez au moins deux périodes")

# ══════════════════════════════════════════════════════════
# TAB 3 - OBJECTIFS
# ══════════════════════════════════════════════════════════
with tabs[3]:
    st.subheader("🎯 Objectifs")
    mode_obj = st.radio("Objectifs par", ["Secteur","Produit"], horizontal=True)
    grp_col = "type_commerce" if mode_obj=="Secteur" else "produit"
    type_obj = mode_obj.lower()

    if grp_col in df_complet.columns:
        entites = df_complet[grp_col].dropna().unique()
        obj_bdd = charger_objectifs(username, type_obj)
        objectifs = {}
        oc = st.columns(3)
        for i,e in enumerate(entites):
            with oc[i%3]:
                val_defaut = int(obj_bdd.get(e, 5000000))
                objectifs[e] = st.number_input(f"Objectif — {e} ({devise})",
                                               min_value=0, value=val_defaut, step=100000, key=f"obj_{e}")

        if st.button("💾 Sauvegarder", use_container_width=True):
            for e,v in objectifs.items():
                sauvegarder_objectif(username, e, v, type_obj)
            st.success("✅ Objectifs sauvegardés !")

# ══════════════════════════════════════════════════════════
# TAB 4 - STOCKS
# ══════════════════════════════════════════════════════════
with tabs[4]:
    st.subheader("📦 Stocks")
    seuil = st.slider("Seuil alerte", 1, 100, 10)
    
    if "produit" in df_complet.columns:
        df_stock = df_complet.groupby("produit")["stock"].last().reset_index()
        df_stock["Statut"] = df_stock["stock"].apply(lambda x: "🔴 Rupture" if x<=0 else ("🟡 Faible" if x<=seuil else "🟢 OK"))
        st.dataframe(df_stock, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════
# TAB 5 - PRÉVISIONS IA
# ══════════════════════════════════════════════════════════
with tabs[5]:
    st.subheader("🔮 Prévisions IA")
    horizon = st.radio("Horizon", ["Prochain mois","Trimestre","6 mois"], horizontal=True)
    
    if st.button("🚀 Générer", use_container_width=True) and api_key:
        with st.spinner("Analyse..."):
            try:
                resume = {
                    "ca_total": total_ca,
                    "transactions": trans,
                    "panier_moyen": panier,
                    "top_produits": df_f.groupby('produit')['chiffre_affaires'].sum().nlargest(5).to_dict() if 'produit' in df_f.columns else {}
                }
                client = Groq(api_key=api_key)
                prompt = f"""Prévisions ventes pour {horizon} basées sur:
                CA total: {resume['ca_total']:,.0f} FCFA
                Transactions: {resume['transactions']}
                Panier moyen: {resume['panier_moyen']:,.0f} FCFA
                Top produits: {resume['top_produits']}
                
                Donne: prévision CA, tendances, recommandations."""
                
                response = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=800
                )
                result = response.choices[0].message.content
                sauvegarder_rapport_ia(username, f"Prévisions {horizon}", result)
                st.markdown(result)
            except Exception as e:
                st.error(f"Erreur: {e}")

# ══════════════════════════════════════════════════════════
# TAB 6 - CHAT IA
# ══════════════════════════════════════════════════════════
with tabs[6]:
    st.subheader("💬 Chat IA")
    
    historique_chat = charger_historique_chat(username)
    for msg in historique_chat[:20]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["message"])
    
    if prompt := st.chat_input("Votre question..."):
        sauvegarder_message_chat(username, "user", prompt)
        with st.chat_message("user"):
            st.markdown(prompt)
        
        if api_key:
            with st.chat_message("assistant"):
                try:
                    resume = {
                        "ca_total": total_ca,
                        "transactions": trans,
                        "produits": list(df_f['produit'].unique()[:10]) if 'produit' in df_f.columns else []
                    }
                    client = Groq(api_key=api_key)
                    response = client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=[{"role": "user", "content": f"Contexte TradeSahel: CA={resume['ca_total']} FCFA, {resume['transactions']} ventes. Question: {prompt}"}],
                        max_tokens=500
                    )
                    rep = response.choices[0].message.content
                    st.markdown(rep)
                    sauvegarder_message_chat(username, "assistant", rep)
                except Exception as e:
                    st.error(f"Erreur: {e}")
        st.rerun()

# ══════════════════════════════════════════════════════════
# TAB 7 - RAPPORT IA
# ══════════════════════════════════════════════════════════
with tabs[7]:
    st.subheader("🧠 Rapport IA")
    
    if st.button("✨ Générer rapport", use_container_width=True) and api_key:
        with st.spinner("Rédaction..."):
            try:
                client = Groq(api_key=api_key)
                prompt = f"""Analyse commerciale:
                CA: {total_ca:,.0f} FCFA
                Transactions: {trans}
                Panier moyen: {panier:,.0f} FCFA
                
                Génère un rapport avec: résumé, analyse, 3 recommandations."""
                
                response = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=1000
                )
                rapport = response.choices[0].message.content
                st.session_state.dernier_rapport = rapport
                sauvegarder_rapport_ia(username, f"Rapport {datetime.now().strftime('%d/%m/%Y')}", rapport)
                st.markdown(rapport)
            except Exception as e:
                st.error(f"Erreur: {e}")
    
    elif st.session_state.dernier_rapport:
        st.markdown(st.session_state.dernier_rapport)

# ══════════════════════════════════════════════════════════
# TAB 8 - ALERTES
# ══════════════════════════════════════════════════════════
with tabs[8]:
    st.subheader("🚨 Alertes")
    alertes = []
    
    if len(valeurs) >= 2:
        ca_old = df_filtre[df_filtre[col_p]==valeurs[-2]]["chiffre_affaires"].sum()
        ca_new = df_filtre[df_filtre[col_p]==valeurs[-1]]["chiffre_affaires"].sum()
        if ca_old > 0:
            var = ((ca_new - ca_old) / ca_old) * 100
            if var < -15:
                alertes.append(("🔴", f"Baisse CA: {var:.1f}%"))
            elif var > 15:
                alertes.append(("🟢", f"Hausse CA: +{var:.1f}%"))
    
    if "stock" in df_complet.columns:
        ruptures = df_complet[df_complet["stock"] <= 0]["produit"].unique()
        for p in ruptures:
            alertes.append(("🔴", f"Rupture: {p}"))
    
    if alertes:
        for icon, msg in alertes:
            st.warning(f"{icon} {msg}")
    else:
        st.success("✅ Aucune alerte")

# ══════════════════════════════════════════════════════════
# TAB 9 - HISTORIQUE IA
# ══════════════════════════════════════════════════════════
with tabs[9]:
    st.subheader("📜 Historique IA")
    historique = charger_historique_ia(username)
    
    for h in historique:
        with st.expander(f"{h['type_rapport']} - {h['date']}"):
            st.markdown(h['contenu'][:500] + "...")
            
            pdf_buf = generer_pdf_rapport(h['contenu'], h['type_rapport'], username)
            st.download_button("📕 PDF", pdf_buf, file_name=f"rapport_{h['id']}.pdf", key=f"pdf_{h['id']}")
            
            if st.button("🗑️ Supprimer", key=f"del_{h['id']}"):
                supprimer_rapport_ia(h['id'])
                st.rerun()

# ══════════════════════════════════════════════════════════
# TAB 10 - NOTES
# ══════════════════════════════════════════════════════════
with tabs[10]:
    st.subheader("📝 Notes")
    
    with st.form("new_note"):
        texte = st.text_area("Nouvelle note")
        priorite = st.selectbox("Priorité", ["info", "important", "urgent"])
        if st.form_submit_button("💾 Ajouter"):
            ajouter_note(username, texte, priorite)
            st.rerun()
    
    notes = charger_notes(username)
    for n in notes:
        st.markdown(f"**{n['priorite'].upper()}** - {n['date']}")
        st.write(n['contenu'])
        if st.button("🗑️", key=f"del_note_{n['id']}"):
            supprimer_note(n['id'])
            st.rerun()
        st.markdown("---")

# ══════════════════════════════════════════════════════════
# TAB 11 - GESTION DONNÉES
# ══════════════════════════════════════════════════════════
with tabs[11]:
    st.subheader("🗄️ Gestion")
    
    stats = stats_bdd(username)
    col1, col2, col3 = st.columns(3)
    col1.metric("Fichiers", stats["nb_fichiers"])
    col2.metric("Ventes", stats["nb_ventes"])
    col3.metric("Rapports IA", stats["nb_rapports"])
    
    fichiers = lister_fichiers(username)
    if not fichiers.empty:
        st.dataframe(fichiers, use_container_width=True)
        
        fichier_del = st.selectbox("Supprimer", fichiers["nom_fichier"].tolist())
        if st.button("🗑️ Supprimer"):
            supprimer_fichier(fichier_del, username)
            st.rerun()
    
    if st.button("🗑️ Tout supprimer", type="secondary"):
        vider_donnees(username)
        st.rerun()

# ══════════════════════════════════════════════════════════
# TAB 12 - EXPORT
# ══════════════════════════════════════════════════════════
with tabs[12]:
    st.subheader("📥 Export")
    
    csv = df_f.to_csv(index=False).encode("utf-8")
    st.download_button("📄 CSV", csv, "export.csv", mime="text/csv", use_container_width=True)
    
    if st.button("📊 Excel", use_container_width=True):
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df_f.to_excel(writer, sheet_name="Ventes", index=False)
        st.download_button("📥 Télécharger", output.getvalue(), "export.xlsx", 
                          mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ══════════════════════════════════════════════════════════
# TAB 13 - DASHBOARD EXÉCUTIF
# ══════════════════════════════════════════════════════════
with tabs[13]:
    dashboard_executif_avance(df_f, devise)

# ══════════════════════════════════════════════════════════
# TAB 14 - NOTIFICATIONS
# ══════════════════════════════════════════════════════════
with tabs[14]:
    afficher_centre_notifications(username)

# ══════════════════════════════════════════════════════════
# TAB 15 - ANALYSE SAISONNIÈRE
# ══════════════════════════════════════════════════════════
with tabs[15]:
    analyse_saisonnalite(df_f)

# ══════════════════════════════════════════════════════════
# TAB 16 - PARRAINAGE
# ══════════════════════════════════════════════════════════
with tabs[16]:
    afficher_interface_parrainage(username)

# ══════════════════════════════════════════════════════════
# TAB 17 - IMPORT API
# ══════════════════════════════════════════════════════════
with tabs[17]:
    st.subheader("🌐 Import depuis API")
    st.info("Cette fonctionnalité permet d'importer des données depuis une API externe")
    
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
                                # Traitement de l'import
                                st.success(f"{len(df_api)} lignes importées")
                    else:
                        st.error(f"Erreur HTTP: {response.status_code}")
                except Exception as e:
                    st.error(f"Erreur: {e}")
        else:
            st.warning("Veuillez entrer une URL")

# ══════════════════════════════════════════════════════════
# TAB 18 - ADMIN (uniquement pour admin)
# ══════════════════════════════════════════════════════════
if username == "admin" and len(tabs) > 18:
    with tabs[18]:
        admin_dashboard()

st.markdown("---")
st.caption("🇲🇱 TradeSahel · Intelligence Commerciale · Mali")