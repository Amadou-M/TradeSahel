import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from groq import Groq
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from docx import Document as DocxDocument
from docx.shared import RGBColor

# Module BDD local
from tradesahel_db import (
    init_db, hash_fichier, fichier_deja_importe,
    enregistrer_fichier, inserer_ventes,
    charger_ventes, lister_fichiers, supprimer_fichier, vider_donnees,
    sauvegarder_rapport_ia, charger_historique_ia, supprimer_rapport_ia,
    sauvegarder_objectif, charger_objectifs,
    ajouter_note, charger_notes, supprimer_note, modifier_note,
    hash_pwd, charger_comptes, sauvegarder_comptes, stats_bdd,
    sauvegarder_message_chat, charger_historique_chat, supprimer_historique_chat
)

# ══════════════════════════════════════════════════════════
# CONSTANTES & CONFIG
# ══════════════════════════════════════════════════════════
VERT       = "#006400"
VERT_FONCE = "#004d1a"
VERT_CLAIR = "#F0FDF4"

st.set_page_config(page_title="TradeSahel - Mali", page_icon="🇲🇱", layout="wide")
init_db()

# ══════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════
for k, v in {
    "authenticated": False,
    "username": "",
    "dernier_rapport": "",
    "chat_history": [],
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

if "comptes" not in st.session_state:
    st.session_state.comptes = charger_comptes()

# ══════════════════════════════════════════════════════════
# CSS LOGIN (identique à votre code original)
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
# PAGE CONNEXION (identique à votre code original)
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
# UTILITAIRES
# ══════════════════════════════════════════════════════════
username = st.session_state.username
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
    return df

# ══════════════════════════════════════════════════════════
# FONCTIONS POUR RAPPORTS PDF/WORD
# ══════════════════════════════════════════════════════════
def generer_pdf_rapport(contenu: str, titre: str, username: str):
    """Génère un PDF à partir du rapport IA"""
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
    """Génère un document Word à partir du rapport IA"""
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
st.sidebar.markdown(
    f"<div style='padding:10px;background:{VERT_CLAIR};border-radius:10px;margin-bottom:8px;'>"
    f"<div style='font-size:11px;color:#64748B;'>Connecté</div>"
    f"<div style='font-weight:600;color:{VERT};'>👤 {username}</div>"
    f"<div style='font-size:12px;color:#64748B;'>🏪 {boutique}</div>"
    f"</div>", unsafe_allow_html=True)

if st.sidebar.button("🚪 Déconnexion", use_container_width=True):
    st.session_state.authenticated = False
    st.rerun()

st.sidebar.markdown("---")
api_key = st.sidebar.text_input("🔑 Clé API Groq", type="password")

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
                df_prep = preparer_df(df_raw)
                df_prep["source_fichier"] = f.name
                fid = enregistrer_fichier(f.name, username, len(df_prep), h)
                inserer_ventes(df_prep, fid, f.name)
                st.sidebar.success(f"✅ {f.name} importé — {len(df_prep)} lignes")
            except Exception as e:
                st.sidebar.error(f"Erreur {f.name} : {e}")

# Filtres
st.sidebar.markdown("---")
st.sidebar.title("🔍 Filtres")

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

# Gestion stock automatique
if "stock" not in df_complet.columns:
    df_complet["stock"] = 100
has_stock = True

has_marge = "marge" in df_complet.columns and df_complet["marge"].notna().any()

# Filtres
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

# Calculs
df_f["ca_reel"] = df_f["chiffre_affaires"] / 1.02
total_ca = df_f["chiffre_affaires"].sum()
total_reel = df_f["ca_reel"].sum()
qte = pd.to_numeric(df_f.get("quantite", pd.Series([0]*len(df_f))), errors="coerce").sum()
trans = len(df_f)
panier = total_ca / trans if trans > 0 else 0

# En-tête
st.title("📊 TradeSahel")
st.markdown(f"**Intelligence Commerciale • Mali** — {boutique}")
st.markdown("---")

# Onglets
tabs = st.tabs([
    "📊 Vue générale","🏬 Multi-boutiques","⚖️ Comparaison",
    "🎯 Objectifs","📦 Stocks","🔮 Prévisions IA",
    "💬 Chat IA","🧠 Rapport IA","🚨 Alertes",
    "📜 Historique","💬 Notes","🗄️ Données","📥 Export"
])

# ══════════════════════════════════════════════════════════
# TAB 0 — VUE GÉNÉRALE (identique à votre code original)
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
            top10 = df_f.groupby("produit")["chiffre_affaires"].sum().nlargest(10).reset_index()
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
# TAB 1 — MULTI-BOUTIQUES (identique)
# ══════════════════════════════════════════════════════════
with tabs[1]:
    st.subheader("🏬 Comparaison Multi-boutiques / fichiers")
    if "source_fichier" in df_complet.columns and df_complet["source_fichier"].nunique() > 1:
        rows_mb = []
        for src in df_complet["source_fichier"].unique():
            d = df_complet[df_complet["source_fichier"]==src]
            rows_mb.append({
                "Fichier/Boutique": src,
                "CA total": d["chiffre_affaires"].sum(),
                "Transactions": len(d),
                "Panier moyen": round(d["chiffre_affaires"].sum()/max(len(d),1),0),
                "Produits uniques": d["produit"].nunique() if "produit" in d.columns else 0,
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
        st.info("Importez plusieurs fichiers pour comparer plusieurs boutiques.")

# ══════════════════════════════════════════════════════════
# TAB 2 — COMPARAISON (identique)
# ══════════════════════════════════════════════════════════
with tabs[2]:
    st.subheader("⚖️ Comparaison")
    mode_comp = st.radio("Mode", ["📅 Deux périodes","🛒 Plusieurs produits"], horizontal=True)
    if mode_comp == "📅 Deux périodes":
        if len(valeurs) >= 2:
            ca1c,ca2c = st.columns(2)
            with ca1c:
                st.markdown(f"<div style='font-weight:600;color:{VERT};margin-bottom:6px;'>Période A</div>", unsafe_allow_html=True)
                p1 = st.selectbox("", valeurs, index=len(valeurs)-2, key="p1")
            with ca2c:
                st.markdown("<div style='font-weight:600;color:#10B981;margin-bottom:6px;'>Période B</div>", unsafe_allow_html=True)
                p2 = st.selectbox("", list(reversed(valeurs)), key="p2")
            ca_a = df_filtre[df_filtre[col_p]==p1]["chiffre_affaires"].sum()
            ca_b = df_filtre[df_filtre[col_p]==p2]["chiffre_affaires"].sum()
            diff = ca_b - ca_a
            evol = ((ca_b-ca_a)/ca_a*100) if ca_a>0 else 0
            m1,m2,m3 = st.columns(3)
            m1.metric(f"📅 {p1}", f"{ca_a:,.0f} {devise}")
            m2.metric(f"📅 {p2}", f"{ca_b:,.0f} {devise}")
            m3.metric("📈 Évolution", f"{diff:+,.0f} {devise}", f"{evol:+.1f}%")
            if "produit" in df_filtre.columns:
                s1 = df_filtre[df_filtre[col_p]==p1].groupby("produit")["chiffre_affaires"].sum().rename(f"CA {p1}")
                s2 = df_filtre[df_filtre[col_p]==p2].groupby("produit")["chiffre_affaires"].sum().rename(f"CA {p2}")
                df_cmp = pd.concat([s1,s2],axis=1).fillna(0).reset_index()
                df_cmp["Évol. (%)"] = ((df_cmp[f"CA {p2}"]-df_cmp[f"CA {p1}"])/df_cmp[f"CA {p1}"].replace(0,1)*100).round(1)
                df_cmp["Tendance"] = df_cmp["Évol. (%)"].apply(lambda x:"📈 Hausse" if x>0 else("📉 Baisse" if x<0 else"➡️ Stable"))
                st.dataframe(df_cmp.style.background_gradient(subset=["Évol. (%)"],cmap="RdYlGn"), use_container_width=True, hide_index=True)
        else:
            st.info("Pas assez de périodes disponibles.")
    else:
        if "produit" in df_filtre.columns:
            prods_cmp = st.multiselect("Produits", df_filtre["produit"].unique())
            if prods_cmp:
                df_plot = df_filtre[df_filtre["produit"].isin(prods_cmp)]
                fig_lp = px.line(df_plot.groupby([col_p,"produit"])["chiffre_affaires"].sum().reset_index(),
                                  x=col_p, y="chiffre_affaires", color="produit", markers=True)
                st.plotly_chart(fig_lp, use_container_width=True)

# ══════════════════════════════════════════════════════════
# TAB 3 — OBJECTIFS (identique)
# ══════════════════════════════════════════════════════════
with tabs[3]:
    st.subheader("🎯 Suivi des Objectifs")
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
                                               min_value=0, value=val_defaut, step=100000, key=f"obj_{type_obj}_{e}")

        col_sauv = st.columns([3,1])
        with col_sauv[1]:
            if st.button("💾 Sauvegarder les objectifs", use_container_width=True):
                for e,v in objectifs.items():
                    sauvegarder_objectif(username, e, v, type_obj)
                st.success("✅ Objectifs sauvegardés !")

        ca_r = df_f.groupby(grp_col)["chiffre_affaires"].sum() if grp_col in df_f.columns else pd.Series()
        rows_obj = []
        for e in entites:
            r = ca_r.get(e,0)
            o = objectifs.get(e,0)
            p = (r/o*100) if o>0 else 0
            rows_obj.append({"Entité":e,"Objectif":o,"Réalisé":r,"Atteinte (%)":round(p,1),
                             "Statut":"✅ Atteint" if p>=100 else("⚠️ En cours" if p>=50 else"❌ Non atteint")})
        df_obj = pd.DataFrame(rows_obj)
        st.dataframe(df_obj.style.format({"Objectif":"{:,.0f}","Réalisé":"{:,.0f}","Atteinte (%)":"{:.1f}%"})
                     .background_gradient(subset=["Atteinte (%)"],cmap="RdYlGn"),
                     use_container_width=True, hide_index=True)
        gc = st.columns(min(len(rows_obj),3))
        for i,row in enumerate(rows_obj):
            with gc[i%3]:
                cj = "#22C55E" if row["Atteinte (%)"]>=100 else("#F59E0B" if row["Atteinte (%)"]>=50 else"#EF4444")
                fig_g = go.Figure(go.Indicator(mode="gauge+number",value=row["Atteinte (%)"],
                    title={"text":row["Entité"],"font":{"size":12}},number={"suffix":"%"},
                    gauge={"axis":{"range":[0,150]},"bar":{"color":cj},
                           "steps":[{"range":[0,50],"color":"#FEE2E2"},{"range":[50,100],"color":"#FEF9C3"},{"range":[100,150],"color":"#DCFCE7"}],
                           "threshold":{"line":{"color":VERT,"width":3},"value":100}}))
                fig_g.update_layout(height=210,margin=dict(t=40,b=10,l=20,r=20),paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig_g, use_container_width=True)

# ══════════════════════════════════════════════════════════
# TAB 4 — STOCKS (amélioré)
# ══════════════════════════════════════════════════════════
with tabs[4]:
    st.subheader("📦 Gestion des Stocks")
    
    if "stock" not in df_complet.columns:
        df_complet["stock"] = 100
        st.info("ℹ️ Colonne 'stock' ajoutée automatiquement avec valeur par défaut (100)")
    
    seuil = st.slider("🚨 Seuil d'alerte stock", 1, 100, 10)
    df_sk = df_complet.dropna(subset=["stock"])
    
    if "produit" in df_sk.columns and not df_sk.empty:
        df_last = df_sk.sort_values("date").groupby("produit")[["stock"]].last().reset_index()
        df_last["stock"] = pd.to_numeric(df_last["stock"], errors="coerce").fillna(100)
        df_last["Statut"] = df_last["stock"].apply(lambda x:"🔴 Rupture" if x<=0 else("🟡 Faible" if x<=seuil else"🟢 OK"))
        
        sk1,sk2,sk3 = st.columns(3)
        sk1.metric("🔴 Rupture", (df_last["Statut"] == "🔴 Rupture").sum())
        sk2.metric("🟡 Faible", (df_last["Statut"] == "🟡 Faible").sum())
        sk3.metric("🟢 OK", (df_last["Statut"] == "🟢 OK").sum())
        
        st.dataframe(df_last.rename(columns={"produit":"Produit","stock":"Stock restant"})
                     .sort_values("Stock restant"), use_container_width=True, hide_index=True)
        
        fig_sk = px.bar(df_last.sort_values("stock"), x="stock", y="produit", orientation="h",
                        title="Niveaux de stock", color="stock",
                        color_continuous_scale=[[0,"#DC2626"],[0.2,"#F59E0B"],[1,"#22C55E"]])
        fig_sk.add_vline(x=seuil, line_dash="dash", line_color="#DC2626", annotation_text=f"Seuil : {seuil}")
        fig_sk.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig_sk, use_container_width=True)
    else:
        st.warning("Aucune donnée de produit trouvée. Importez un fichier avec des produits.")

# ══════════════════════════════════════════════════════════
# TAB 5 — PRÉVISIONS IA (identique)
# ══════════════════════════════════════════════════════════
with tabs[5]:
    st.subheader("🔮 Prévisions des ventes avec IA")
    horizon = st.radio("Horizon :", ["Prochain mois","Prochain trimestre","6 prochains mois"], horizontal=True)
    if st.button("🚀 Générer les prévisions", use_container_width=True):
        if not api_key:
            st.error("Entrez votre clé Groq dans le panneau gauche.")
        else:
            with st.spinner("Analyse en cours..."):
                try:
                    histo = df_filtre.groupby(["mois","type_commerce"])["chiffre_affaires"].sum().reset_index().to_string()
                    prompt = f"""Tu es un expert du commerce au Mali (FCFA).
Analyse cet historique et prevois pour {horizon} :
{histo}
1. Prévision CA par secteur (fourchette basse/haute en FCFA)
2. Secteurs en croissance vs déclin avec justification
3. Impact saisonnalité malienne (Ramadan, récoltes, hivernage, fêtes)
4. 3 recommandations concrètes
5. Niveau de confiance (Elevé/Moyen/Faible) et pourquoi"""
                    client = Groq(api_key=api_key)
                    resp = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role":"system","content":"Expert commerce Mali, PME africaines."},
                                  {"role":"user","content":prompt}], max_tokens=2000)
                    result = resp.choices[0].message.content
                    sauvegarder_rapport_ia(username, f"Previsions — {horizon}", result)
                    st.markdown(f"<div style='background:{VERT_CLAIR};border:1px solid #BBF7D0;border-radius:14px;padding:24px;font-size:14px;line-height:1.8;'>{result.replace(chr(10),'<br>')}</div>", unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Erreur IA : {e}")

# ══════════════════════════════════════════════════════════
# TAB 6 — CHAT IA AVEC HISTORIQUE (NOUVEAU)
# ══════════════════════════════════════════════════════════
with tabs[6]:
    st.subheader("💬 Chat IA Commerce")
    
    # Charger l'historique
    historique_chat = charger_historique_chat(username)
    
    # Afficher l'historique
    for msg in historique_chat:
        with st.chat_message(msg["role"]):
            st.markdown(msg["message"])
    
    # Nouveau message
    if prompt_chat := st.chat_input("Posez votre question sur vos ventes, stocks, produits..."):
        sauvegarder_message_chat(username, "user", prompt_chat)
        
        with st.chat_message("user"):
            st.markdown(prompt_chat)
        
        with st.chat_message("assistant"):
            if not api_key:
                rep = "Entrez votre clé API Groq dans le panneau gauche."
                st.warning(rep)
            else:
                with st.spinner("L'IA analyse..."):
                    try:
                        context = df_f.head(80).to_string(index=False)
                        client = Groq(api_key=api_key)
                        resp = client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[{"role":"system","content":"Assistant expert commerce Mali."},
                                      {"role":"user","content":f"Données :\n{context}\n\nQuestion : {prompt_chat}"}],
                            max_tokens=1000)
                        rep = resp.choices[0].message.content
                        st.markdown(rep)
                    except Exception as e:
                        rep = f"Erreur IA : {e}"
                        st.error(rep)
            
            sauvegarder_message_chat(username, "assistant", rep)
        
        st.rerun()
    
    # Boutons de gestion
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📜 Voir historique complet", use_container_width=True):
            with st.expander("📋 Historique complet des conversations"):
                for msg in historique_chat[-20:]:
                    st.markdown(f"**{msg['role']}** ({msg['date']}): {msg['message'][:200]}...")
    
    with col2:
        if st.button("🗑️ Effacer tout l'historique", use_container_width=True):
            supprimer_historique_chat(username)
            st.success("✅ Historique effacé !")
            st.rerun()

# ══════════════════════════════════════════════════════════
# TAB 7 — RAPPORT IA (identique)
# ══════════════════════════════════════════════════════════
with tabs[7]:
    st.subheader("🧠 Rapport Commercial IA")
    if st.button("✨ Générer le rapport complet", use_container_width=True):
        if not api_key:
            st.error("Entrez votre clé Groq dans le panneau gauche.")
        else:
            with st.spinner("Rédaction du rapport..."):
                try:
                    det_str = ""
                    if "produit" in df_f.columns:
                        det = df_f.groupby("produit").agg(qte=("quantite","sum"),ca=("chiffre_affaires","sum")).reset_index()
                        det_str = " | ".join([f"{r.produit}: {r.qte:.0f} u., {r.ca:,.0f} FCFA" for r in det.itertuples()])
                    marge_str = ""
                    if has_marge and "marge" in df_f.columns:
                        m = df_f["marge"].sum()
                        marge_str = f"\nMarge brute : {m:,.0f} FCFA ({m/total_ca*100:.1f}%)" if total_ca>0 else ""
                    prompt_r = f"""Analyste commercial expert marché malien.
Boutique : {boutique} | Période : {choix} | FCFA
CA nominal : {total_ca:,.0f} | CA réel : {total_reel:,.0f} | Transactions : {trans} | Panier : {panier:,.0f}{marge_str}
Produits : {det_str or 'Non disponible'}

1. RÉSUMÉ EXÉCUTIF (3 lignes avec chiffres clés)
2. ANALYSE DES PERFORMANCES (par produit/secteur)
3. POINTS FORTS (minimum 3)
4. POINTS DE VIGILANCE (minimum 2)
5. RECOMMANDATIONS STRATÉGIQUES (adaptées au Mali)
6. PLAN D ACTION (3 actions avec KPI mesurable)"""
                    client = Groq(api_key=api_key)
                    resp = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role":"system","content":"Expert analyse financière PME africaines, Mali."},
                                  {"role":"user","content":prompt_r}],
                        max_tokens=2500, temperature=0.6)
                    rapport = resp.choices[0].message.content
                    st.session_state.dernier_rapport = rapport
                    sauvegarder_rapport_ia(username, f"Rapport — {choix}", rapport)
                    st.success("✅ Rapport généré et sauvegardé en base !")
                    st.markdown(f"<div style='background:{VERT_CLAIR};border:1px solid #BBF7D0;border-radius:14px;padding:28px;font-size:14px;line-height:1.9;'>{rapport.replace(chr(10),'<br>')}</div>", unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Erreur IA : {e}")
    elif st.session_state.dernier_rapport:
        st.markdown(f"<div style='background:{VERT_CLAIR};border:1px solid #BBF7D0;border-radius:14px;padding:28px;font-size:14px;line-height:1.9;'>{st.session_state.dernier_rapport.replace(chr(10),'<br>')}</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# TAB 8 — ALERTES (identique)
# ══════════════════════════════════════════════════════════
with tabs[8]:
    st.subheader("🚨 Alertes Automatiques")
    seuil_baisse = st.slider("Seuil alerte baisse CA (%)", 5, 50, 15)
    alertes = []
    if len(valeurs) >= 2:
        ca_d = df_filtre[df_filtre[col_p]==valeurs[-1]]["chiffre_affaires"].sum()
        ca_a = df_filtre[df_filtre[col_p]==valeurs[-2]]["chiffre_affaires"].sum()
        if ca_a > 0:
            var = (ca_d-ca_a)/ca_a*100
            if var <= -seuil_baisse:
                alertes.append(("🔴",f"Baisse CA : {var:.1f}% entre {valeurs[-2]} et {valeurs[-1]}","error"))
            elif var >= 15:
                alertes.append(("🟢",f"Hausse CA : +{var:.1f}% entre {valeurs[-2]} et {valeurs[-1]}","success"))
    if "type_commerce" in df_f.columns:
        cs = df_f.groupby("type_commerce")["chiffre_affaires"].sum()
        moy = cs.mean()
        for s,c in cs.items():
            if c < moy*0.4:
                alertes.append(("⚠️",f"{s} en sous-performance ({c:,.0f} {devise})","warning"))
    if not df_f.empty and "produit" in df_f.columns:
        best = df_f.groupby("produit")["chiffre_affaires"].sum().idxmax()
        best_ca = df_f.groupby("produit")["chiffre_affaires"].sum().max()
        alertes.append(("⭐",f"Top produit : {best} ({best_ca:,.0f} {devise})","info"))
    if "stock" in df_complet.columns and "produit" in df_complet.columns:
        df_rupt = df_complet[pd.to_numeric(df_complet["stock"],errors="coerce")==0]
        for p in df_rupt["produit"].unique():
            alertes.append(("🔴",f"Rupture de stock : {p}","error"))
    if alertes:
        for ico,msg,typ in alertes:
            {"error":st.error,"success":st.success,"warning":st.warning,"info":st.info}[typ](f"{ico} {msg}")
    else:
        st.success("✅ Aucune alerte critique détectée.")

# ══════════════════════════════════════════════════════════
# TAB 9 — HISTORIQUE IA AVEC PDF/WORD (NOUVEAU)
# ══════════════════════════════════════════════════════════
with tabs[9]:
    st.subheader("📜 Historique des rapports IA")
    historique = charger_historique_ia(username)
    
    if not historique:
        st.info("Aucun rapport généré. Utilisez Prévisions IA ou Rapport IA.")
    else:
        st.caption(f"{len(historique)} rapport(s) sauvegardé(s) en base de données")
        
        for h in historique:
            with st.expander(f"📄 {h['type_rapport']} — {h['date']}"):
                st.markdown(f"<div style='background:{VERT_CLAIR};border:1px solid #BBF7D0;border-radius:10px;padding:16px;font-size:13px;line-height:1.7;'>{h['contenu'].replace(chr(10),'<br>')}</div>", unsafe_allow_html=True)
                
                col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
                
                with col1:
                    st.download_button("📄 TXT", data=h["contenu"].encode("utf-8"),
                        file_name=f"rapport_{h['date'][:10]}.txt", mime="text/plain", key=f"txt_{h['id']}")
                
                with col2:
                    pdf_buf = generer_pdf_rapport(h["contenu"], h["type_rapport"], username)
                    st.download_button("📕 PDF", data=pdf_buf,
                        file_name=f"rapport_{h['date'][:10]}.pdf", mime="application/pdf", key=f"pdf_{h['id']}")
                
                with col3:
                    word_buf = generer_word_rapport(h["contenu"], h["type_rapport"], username)
                    st.download_button("📘 WORD", data=word_buf,
                        file_name=f"rapport_{h['date'][:10]}.docx", 
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        key=f"word_{h['id']}")
                
                with col4:
                    if st.button("🗑️ Supprimer", key=f"del_{h['id']}"):
                        supprimer_rapport_ia(h["id"])
                        st.rerun()

# ══════════════════════════════════════════════════════════
# TAB 10 — NOTES AVEC MODIFICATION (NOUVEAU)
# ══════════════════════════════════════════════════════════
with tabs[10]:
    st.subheader("💬 Notes & Observations")
    
    # Formulaire pour ajouter une note
    with st.form("form_note"):
        texte = st.text_area("Ajouter une note", placeholder="Ex: Ventes élevées en janvier, vérifier les stocks de riz...")
        priorite = st.selectbox("Priorité", ["info", "important", "urgent"])
        if st.form_submit_button("💾 Sauvegarder", use_container_width=True) and texte:
            ajouter_note(username, texte, priorite)
            st.success("✅ Note sauvegardée !")
            st.rerun()
    
    st.markdown("---")
    
    # Afficher les notes existantes
    notes = charger_notes(username)
    cls_map = {"urgent": "#FEF2F2", "important": "#FFFBEB", "info": VERT_CLAIR}
    brd_map = {"urgent": "#FCA5A5", "important": "#FCD34D", "info": "#BBF7D0"}
    ico_map = {"urgent": "🔴", "important": "🟠", "info": "🔵"}
    
    if not notes:
        st.info("Aucune note pour le moment. Ajoutez votre première note ci-dessus.")
    else:
        for n in notes:
            with st.container():
                # État de modification
                edit_key = f"edit_{n['id']}"
                if edit_key not in st.session_state:
                    st.session_state[edit_key] = False
                
                col_n, col_e, col_s, col_d = st.columns([5, 1, 1, 1])
                
                with col_n:
                    bg_col = cls_map.get(n["priorite"], VERT_CLAIR)
                    brd_col = brd_map.get(n["priorite"], "#BBF7D0")
                    ico = ico_map.get(n["priorite"], "📝")
                    
                    if st.session_state[edit_key]:
                        # Mode édition
                        nouveau_texte = st.text_area("Modifier", n["contenu"], key=f"text_{n['id']}")
                        nouvelle_priorite = st.selectbox("Priorité", ["info", "important", "urgent"], 
                                                          index=["info", "important", "urgent"].index(n["priorite"]),
                                                          key=f"prio_{n['id']}")
                        if st.button("💾 Enregistrer", key=f"save_{n['id']}"):
                            modifier_note(n["id"], nouveau_texte, nouvelle_priorite)
                            st.session_state[edit_key] = False
                            st.rerun()
                    else:
                        html_n = f"""
                        <div style='background:{bg_col};border:1px solid {brd_col};
                             border-radius:8px;padding:10px 14px;margin-bottom:6px;'>
                            <div style='font-size:10px;color:#64748B;margin-bottom:4px;'>
                                {ico} {n['date']} · {n['priorite'].upper()}
                            </div>
                            <div style='font-size:13px;'>{n['contenu']}</div>
                        </div>
                        """
                        st.markdown(html_n, unsafe_allow_html=True)
                
                with col_e:
                    if not st.session_state[edit_key]:
                        if st.button("✏️ Modifier", key=f"edit_btn_{n['id']}"):
                            st.session_state[edit_key] = True
                            st.rerun()
                
                with col_s:
                    if not st.session_state[edit_key]:
                        pass  # Espace
                
                with col_d:
                    if not st.session_state[edit_key]:
                        if st.button("🗑️", key=f"del_note_{n['id']}"):
                            supprimer_note(n["id"])
                            st.rerun()

# ══════════════════════════════════════════════════════════
# TAB 11 — GESTION DES DONNÉES (identique)
# ══════════════════════════════════════════════════════════
with tabs[11]:
    st.subheader("🗄️ Gestion de la base de données")
    
    stats = stats_bdd(username)
    s1,s2,s3,s4,s5,s6 = st.columns(6)
    s1.metric("📁 Fichiers", stats["nb_fichiers"])
    s2.metric("📊 Lignes", stats["nb_ventes"])
    s3.metric("🤖 Rapports IA", stats["nb_rapports"])
    s4.metric("💬 Messages", stats.get("nb_chat", 0))
    s5.metric("📝 Notes", stats.get("nb_notes", 0))
    s6.metric("📅 Dernier import", stats["derniere_import"])
    
    st.markdown("---")
    st.subheader("📁 Fichiers importés")
    df_fichiers = lister_fichiers(username)
    if not df_fichiers.empty:
        st.dataframe(df_fichiers.rename(columns={
            "nom_fichier":"Fichier","nb_lignes":"Lignes","date_import":"Date import"}),
            use_container_width=True, hide_index=True)
        
        st.markdown("---")
        fichier_del = st.selectbox("Supprimer un fichier", df_fichiers["nom_fichier"].tolist())
        if st.button(f"🗑️ Supprimer {fichier_del} et ses données", use_container_width=True):
            supprimer_fichier(fichier_del, username)
            st.success(f"✅ {fichier_del} supprimé.")
            st.rerun()
    else:
        st.info("Aucun fichier importé.")
    
    st.markdown("---")
    with st.expander("⚠️ Zone dangereuse"):
        st.warning("Cette action supprime TOUTES vos données. Elle est irréversible.")
        if st.button("🗑️ Vider toutes mes données", type="secondary", use_container_width=True):
            vider_donnees(username)
            supprimer_historique_chat(username)
            st.success("✅ Toutes vos données ont été supprimées.")
            st.rerun()

# ══════════════════════════════════════════════════════════
# TAB 12 — EXPORT (identique)
# ══════════════════════════════════════════════════════════
with tabs[12]:
    st.subheader("📥 Export des données")
    cx1,cx2,cx3,cx4 = st.columns(4)
    
    with cx1:
        st.markdown("#### 📄 PDF")
        if st.button("⬇️ Générer PDF", use_container_width=True):
            try:
                dp = df_produits_export if "df_produits_export" in dir() else None
                pdf_buf = generer_pdf_standard(boutique, username, choix, devise,
                                      total_ca, total_reel, panier, qte, trans,
                                      st.session_state.dernier_rapport, dp, has_marge)
                st.download_button("📥 Télécharger PDF", data=pdf_buf,
                    file_name=f"TradeSahel_{username}_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf", use_container_width=True)
            except Exception as e:
                st.error(f"Erreur PDF : {e}")
    
    with cx2:
        st.markdown("#### 📊 Excel")
        if st.button("⬇️ Générer Excel", use_container_width=True):
            output = BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                wb = writer.book
                fmh = wb.add_format({"bold":True,"bg_color":"006400","font_color":"FFFFFF","border":1,"align":"center","font_name":"Calibri"})
                df_complet.to_excel(writer, sheet_name="Données Brutes", index=False, startrow=1)
                ws1 = writer.sheets["Données Brutes"]
                for ci,h in enumerate(df_complet.columns):
                    ws1.write(1,ci,h,fmh)
                ws1.set_column("A:Z",16)
                if "produit" in df_f.columns:
                    pp = df_f.groupby("produit")["chiffre_affaires"].sum().sort_values(ascending=False).reset_index()
                    pp.to_excel(writer, sheet_name="Par Produit", index=False, startrow=1)
                    ws2 = writer.sheets["Par Produit"]
                    for ci,h in enumerate(pp.columns):
                        ws2.write(1,ci,h,fmh)
                if "type_commerce" in df_f.columns:
                    ps = df_f.groupby("type_commerce")["chiffre_affaires"].sum().reset_index()
                    ps.to_excel(writer, sheet_name="Par Secteur", index=False, startrow=1)
                    ws3 = writer.sheets["Par Secteur"]
                    for ci,h in enumerate(ps.columns):
                        ws3.write(1,ci,h,fmh)
            output.seek(0)
            st.download_button("📥 Télécharger Excel", data=output,
                file_name=f"TradeSahel_{username}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True)
    
    with cx3:
        st.markdown("#### 📋 CSV")
        csv = df_f.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Télécharger CSV", data=csv,
            file_name=f"TradeSahel_{username}_{choix.replace(' ','_')}.csv",
            mime="text/csv", use_container_width=True)
    
    with cx4:
        st.markdown("#### 📄 Template")
        template = ("date,produit,type_commerce,quantite,prix_unitaire,prix_achat,stock\n"
                    "2025-01-15,Riz 25kg,Alimentation,10,12500,8000,50\n"
                    "2025-01-16,Huile 5L,Alimentation,5,3500,2200,30\n")
        st.download_button("⬇️ Template CSV", data=template.encode("utf-8"),
            file_name="template_tradesahel.csv", mime="text/csv", use_container_width=True)

st.markdown("---")
st.caption("🇲🇱 TradeSahel · Intelligence Commerciale · Mali")