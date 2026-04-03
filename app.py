import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from groq import Groq
from io import BytesIO

# ══════════════════════════════════════════════════════════
# CONFIG PAGE
# ══════════════════════════════════════════════════════════
st.set_page_config(page_title="TradeSahel - Mali", page_icon="🇲🇱", layout="wide")

# ══════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════
for k, v in {
    "authenticated": False,
    "username": "",
    "comptes": {
        "admin": {"password": "admin123", "boutique": "Boutique Principale", "email": "admin@tradesahel.ml"},
        "mali1": {"password": "mali2025", "boutique": "Shop Bamako",          "email": "bamako@tradesahel.ml"},
    },
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ══════════════════════════════════════════════════════════
# CSS PAGE CONNEXION
# ══════════════════════════════════════════════════════════
CSS_LOGIN = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700&family=DM+Sans:wght@400;500&display=swap');

[data-testid="stAppViewContainer"] {
    background: linear-gradient(145deg, #004d1a 0%, #006400 35%, #14B53A 70%, #FCD116 100%);
    min-height: 100vh;
}
[data-testid="stHeader"] { background: transparent; }

.login-wrap {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 88vh;
    padding: 24px;
}
.login-box {
    background: rgba(255,255,255,0.96);
    backdrop-filter: blur(20px);
    border-radius: 28px;
    padding: 52px 48px 44px;
    max-width: 460px;
    width: 100%;
    box-shadow: 0 32px 80px rgba(0,0,0,0.28);
    text-align: center;
}
.flag-wrap {
    font-size: 10px;
    animation: pulse 3s ease-in-out infinite;
    display: block;
    margin-bottom: 12px;
}
@keyframes pulse {
    0%,100% { transform: scale(1); }
    50%      { transform: scale(1.07); }
}
.brand-name {
    font-family: 'Sora', sans-serif;
    font-size: 36px;
    font-weight: 700;
    color: #004d1a;
    letter-spacing: -0.04em;
    margin-bottom: 4px;
}
.brand-sub {
    font-size: 13px;
    color: #64748B;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    font-weight: 500;
    margin-bottom: 28px;
}
.tab-bar {
    display: flex;
    gap: 0;
    border: 1.5px solid #E2E8F0;
    border-radius: 12px;
    overflow: hidden;
    margin-bottom: 24px;
}
.tab-btn {
    flex: 1;
    padding: 10px 6px;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    border: none;
    background: white;
    color: #64748B;
    transition: all .15s;
    font-family: 'DM Sans', sans-serif;
    letter-spacing: .02em;
}
.tab-btn.active {
    background: #006400;
    color: white;
}
.divider {
    height: 1px;
    background: #E2E8F0;
    margin: 20px 0;
}
.demo-box {
    background: #F0FDF4;
    border: 1px solid #BBF7D0;
    border-radius: 10px;
    padding: 12px 16px;
    font-size: 12px;
    color: #166534;
    text-align: left;
    line-height: 1.8;
    margin-top: 14px;
}
.demo-box b { color: #004d1a; }
.success-msg {
    background: #F0FDF4;
    border: 1px solid #86EFAC;
    border-radius: 10px;
    padding: 14px;
    color: #166534;
    font-size: 14px;
    font-weight: 500;
    margin-top: 12px;
}
.error-msg {
    background: #FEF2F2;
    border: 1px solid #FCA5A5;
    border-radius: 10px;
    padding: 14px;
    color: #991B1B;
    font-size: 14px;
    font-weight: 500;
    margin-top: 12px;
}
/* Boutons Streamlit dans la page de connexion */
div[data-testid="stForm"] button[kind="primaryFormSubmit"],
div[data-testid="stForm"] button {
    background: #006400 !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-family: 'DM Sans', sans-serif !important;
    padding: 12px !important;
    transition: background .2s !important;
}
div[data-testid="stForm"] button:hover {
    background: #004d1a !important;
}
</style>
"""

# ══════════════════════════════════════════════════════════
# PAGE CONNEXION
# ══════════════════════════════════════════════════════════
def page_connexion():
    st.markdown(CSS_LOGIN, unsafe_allow_html=True)

    st.markdown("""
    <div class="login-wrap">
      <div class="login-box">
        <span class="flag-wrap">🇲🇱</span>
        <div class="brand-name">TradeSahel</div>
        <div class="brand-sub">Intelligence Commerciale · Mali</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    col = st.columns([1, 2, 1])[1]
    with col:
        # Onglets de navigation
        option = st.radio(
            "",
            ["🔑 Se connecter", "➕ Créer un compte", "🔓 Mot de passe oublié"],
            horizontal=True,
            label_visibility="collapsed",
            key="login_option"
        )

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        # ── SE CONNECTER ──────────────────────────────────
        if option == "🔑 Se connecter":
            with st.form("form_login"):
                user = st.text_input("👤 Identifiant", placeholder="admin ou mali1")
                pwd  = st.text_input("🔑 Mot de passe", type="password", placeholder="••••••••")
                ok   = st.form_submit_button("Se connecter", use_container_width=True)

            if ok:
                comptes = st.session_state.comptes
                if user.strip() in comptes and comptes[user.strip()]["password"] == pwd:
                    st.session_state.authenticated = True
                    st.session_state.username       = user.strip()
                    st.rerun()
                else:
                    st.markdown('<div class="error-msg">❌ Identifiant ou mot de passe incorrect.</div>',
                                unsafe_allow_html=True)

            st.markdown("""<div class="demo-box">
<b>Comptes démo :</b><br>
👤 admin &nbsp;/&nbsp; 🔑 admin123<br>
👤 mali1 &nbsp;/&nbsp; 🔑 mali2025
</div>""", unsafe_allow_html=True)

        # ── CRÉER UN COMPTE ───────────────────────────────
        elif option == "➕ Créer un compte":
            with st.form("form_create"):
                st.markdown("#### Créer votre compte")
                new_user  = st.text_input("👤 Identifiant",       placeholder="ex: boutique_bamako")
                new_email = st.text_input("📧 Email",             placeholder="vous@email.ml")
                new_bout  = st.text_input("🏪 Nom de la boutique", placeholder="ex: Shop Bamako Centre")
                new_pwd   = st.text_input("🔑 Mot de passe",      type="password", placeholder="Minimum 6 caractères")
                new_conf  = st.text_input("🔑 Confirmer mot de passe", type="password")
                ok        = st.form_submit_button("Créer mon compte", use_container_width=True)

            if ok:
                comptes = st.session_state.comptes
                if not new_user.strip():
                    st.markdown('<div class="error-msg">❌ L\'identifiant est obligatoire.</div>',
                                unsafe_allow_html=True)
                elif new_user.strip() in comptes:
                    st.markdown('<div class="error-msg">❌ Cet identifiant existe déjà.</div>',
                                unsafe_allow_html=True)
                elif len(new_pwd) < 6:
                    st.markdown('<div class="error-msg">❌ Le mot de passe doit faire au moins 6 caractères.</div>',
                                unsafe_allow_html=True)
                elif new_pwd != new_conf:
                    st.markdown('<div class="error-msg">❌ Les mots de passe ne correspondent pas.</div>',
                                unsafe_allow_html=True)
                else:
                    comptes[new_user.strip()] = {
                        "password": new_pwd,
                        "boutique": new_bout or new_user.strip(),
                        "email":    new_email,
                    }
                    st.session_state.comptes       = comptes
                    st.session_state.authenticated = True
                    st.session_state.username      = new_user.strip()
                    st.markdown('<div class="success-msg">✅ Compte créé avec succès ! Connexion en cours...</div>',
                                unsafe_allow_html=True)
                    st.rerun()

        # ── MOT DE PASSE OUBLIÉ ───────────────────────────
        elif option == "🔓 Mot de passe oublié":
            with st.form("form_reset"):
                st.markdown("#### Réinitialiser votre mot de passe")
                r_user = st.text_input("👤 Votre identifiant", placeholder="Entrez votre identifiant")
                r_new  = st.text_input("🔑 Nouveau mot de passe",     type="password", placeholder="Minimum 6 caractères")
                r_conf = st.text_input("🔑 Confirmer nouveau mot de passe", type="password")
                ok     = st.form_submit_button("Réinitialiser", use_container_width=True)

            if ok:
                comptes = st.session_state.comptes
                if not r_user.strip():
                    st.markdown('<div class="error-msg">❌ Entrez votre identifiant.</div>',
                                unsafe_allow_html=True)
                elif r_user.strip() not in comptes:
                    st.markdown('<div class="error-msg">❌ Identifiant introuvable.</div>',
                                unsafe_allow_html=True)
                elif len(r_new) < 6:
                    st.markdown('<div class="error-msg">❌ Le mot de passe doit faire au moins 6 caractères.</div>',
                                unsafe_allow_html=True)
                elif r_new != r_conf:
                    st.markdown('<div class="error-msg">❌ Les mots de passe ne correspondent pas.</div>',
                                unsafe_allow_html=True)
                else:
                    comptes[r_user.strip()]["password"] = r_new
                    st.session_state.comptes = comptes
                    st.markdown('<div class="success-msg">✅ Mot de passe réinitialisé ! Vous pouvez maintenant vous connecter.</div>',
                                unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# CONTRÔLE D'ACCÈS
# ══════════════════════════════════════════════════════════
if not st.session_state.authenticated:
    page_connexion()
    st.stop()

# ══════════════════════════════════════════════════════════
# DASHBOARD — identique à ton code original
# ══════════════════════════════════════════════════════════
username = st.session_state.username
boutique = st.session_state.comptes.get(username, {}).get("boutique", username)

st.sidebar.markdown(f"<div style='padding:10px;background:#F0FDF4;border-radius:10px;margin-bottom:8px;'>"
                    f"<div style='font-size:11px;color:#64748B;'>Connecté</div>"
                    f"<div style='font-weight:600;color:#006400;'>👤 {username}</div>"
                    f"<div style='font-size:12px;color:#64748B;'>🏪 {boutique}</div>"
                    f"</div>", unsafe_allow_html=True)

if st.sidebar.button("🚪 Déconnexion", use_container_width=True):
    st.session_state.authenticated = False
    st.session_state.username      = ""
    st.rerun()

devise = "FCFA"

st.title("📊 TradeSahel")
st.markdown("**Intelligence Commerciale • Mali** — Analyse pour tous les secteurs du commerce")
st.markdown("---")

api_key = st.sidebar.text_input("🔑 Clé API Groq", type="password")

st.sidebar.markdown("---")
st.sidebar.title("🏪 Points de vente")
nb = st.sidebar.number_input("Nombre de points de vente", 1, 10, 1)

points_vente = {}
for i in range(int(nb)):
    nom     = st.sidebar.text_input(f"Nom point {i+1}", f"Point {i+1}", key=f"nom{i}")
    fichier = st.sidebar.file_uploader(f"Fichier {i+1}", type=["csv","xlsx","xls"], key=f"f{i}")
    points_vente[nom] = fichier

# ── Chargement des données ────────────────────────────────
def charger(fichier):
    if fichier is None:
        return None
    try:
        df = pd.read_csv(fichier) if fichier.name.endswith(".csv") else pd.read_excel(fichier)
        df.columns = df.columns.str.strip().str.lower()
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            df = df.dropna(subset=["date"])
        if "chiffre_affaires" not in df.columns and {"quantite","prix_unitaire"}.issubset(df.columns):
            df["chiffre_affaires"] = pd.to_numeric(df["quantite"], errors="coerce") * \
                                     pd.to_numeric(df["prix_unitaire"], errors="coerce")
        if "date" in df.columns:
            df["jour"]    = df["date"].dt.strftime("%d/%m/%Y")
            df["semaine"] = df["date"].dt.strftime("Semaine %W")
            df["mois"]    = df["date"].dt.strftime("%B %Y")
            df["annee"]   = df["date"].dt.strftime("%Y")
        if "type_commerce" not in df.columns:
            df["type_commerce"] = "Commerce Général"
        return df
    except Exception as e:
        st.sidebar.error(f"Erreur : {e}")
        return None

dfs = {nom: charger(f) for nom, f in points_vente.items() if f is not None}
dfs = {k: v for k, v in dfs.items() if v is not None and not v.empty}

if not dfs:
    st.info("👈 Importez au moins un fichier pour activer toutes les fonctionnalités.")
    st.stop()

df_complet = pd.concat(dfs.values(), ignore_index=True)

# ── Filtres ───────────────────────────────────────────────
st.sidebar.markdown("---")
periode = st.sidebar.radio("Niveau :", ["Mois","Année"], horizontal=True)
col_p   = "mois" if periode == "Mois" else "annee"

if "type_commerce" in df_complet.columns:
    types_dispo    = sorted(df_complet["type_commerce"].unique())
    types_selection= st.sidebar.multiselect("Type de commerce", types_dispo, default=types_dispo)
    df_filtre      = df_complet[df_complet["type_commerce"].isin(types_selection)]
else:
    df_filtre = df_complet.copy()

valeurs = sorted(df_filtre[col_p].unique())
choix   = st.sidebar.selectbox(f"Sélectionner {periode} :", ["Toutes"] + list(valeurs))
df_f    = df_filtre[df_filtre[col_p] == choix].copy() if choix != "Toutes" else df_filtre.copy()

# ── Calculs de base ───────────────────────────────────────
taux_inflation = 0.02
df_f["ca_reel"] = df_f["chiffre_affaires"] / (1 + taux_inflation)

total_ca   = df_f["chiffre_affaires"].sum()
total_reel = df_f["ca_reel"].sum()
qte        = pd.to_numeric(df_f.get("quantite", pd.Series([0]*len(df_f))), errors="coerce").sum()
trans      = len(df_f)
panier     = total_ca / trans if trans > 0 else 0

# ══════════════════════════════════════════════════════════
# ONGLETS
# ══════════════════════════════════════════════════════════
tabs = st.tabs([
    "📊 Vue générale", "🏪 Multi-points", "⚖️ Comparaison",
    "🎯 Objectifs", "🔮 Prévisions IA", "🚨 Alertes", "📥 Export"
])

# ── TAB 0 — Vue générale ──────────────────────────────────
with tabs[0]:
    label_periode = choix if choix != "Toutes" else "Période complète"
    st.subheader(f"📌 KPIs — {label_periode}")

    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("💰 CA Nominal",   f"{total_ca:,.0f} {devise}")
    c2.metric("📉 CA Réel",      f"{total_reel:,.0f} {devise}")
    c3.metric("🛒 Panier Moyen", f"{panier:,.0f} {devise}")
    c4.metric("📦 Quantité",     f"{qte:,.0f}")
    c5.metric("🔢 Transactions", f"{trans:,.0f}")

    col_g1, col_g2 = st.columns(2)
    with col_g1:
        if "type_commerce" in df_f.columns:
            fig_pie = px.pie(df_f, names="type_commerce", values="chiffre_affaires",
                             title="Répartition du CA par Secteur", hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)
    with col_g2:
        if "produit" in df_f.columns:
            top_prod = df_f.groupby("produit")["chiffre_affaires"].sum().nlargest(10).reset_index()
            fig_bar  = px.bar(top_prod, x="chiffre_affaires", y="produit", orientation="h",
                              title="Top 10 Produits",
                              color="chiffre_affaires", color_continuous_scale=[[0,"#BBF7D0"],[1,"#006400"]])
            fig_bar.update_layout(coloraxis_showscale=False)
            st.plotly_chart(fig_bar, use_container_width=True)

    if "mois" in df_f.columns:
        evo = df_f.groupby("mois")["chiffre_affaires"].sum().reset_index()
        fig_evo = px.line(evo, x="mois", y="chiffre_affaires", markers=True,
                          title="Évolution mensuelle du CA",
                          color_discrete_sequence=["#006400"])
        st.plotly_chart(fig_evo, use_container_width=True)

    with st.expander("📋 Données brutes"):
        st.dataframe(df_f, use_container_width=True)

# ── TAB 1 — Multi-points ─────────────────────────────────
with tabs[1]:
    st.subheader("🏪 Comparaison entre Points de Vente")
    data_multi = []
    for nom, df in dfs.items():
        data_multi.append({
            "Point de Vente": nom,
            "CA Nominal":     df["chiffre_affaires"].sum(),
            "Transactions":   len(df),
            "Panier Moyen":   round(df["chiffre_affaires"].sum()/max(len(df),1), 0),
        })
    df_multi = pd.DataFrame(data_multi)
    st.dataframe(df_multi.style.format({
        "CA Nominal":   "{:,.0f}",
        "Panier Moyen": "{:,.0f}",
    }), use_container_width=True, hide_index=True)

    fig_multi = px.bar(df_multi, x="Point de Vente", y="CA Nominal",
                       text="CA Nominal", title="CA par Point de Vente",
                       color="CA Nominal",
                       color_continuous_scale=[[0,"#BBF7D0"],[1,"#006400"]])
    fig_multi.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
    fig_multi.update_layout(coloraxis_showscale=False)
    st.plotly_chart(fig_multi, use_container_width=True)

# ── TAB 2 — Comparaison périodes ─────────────────────────
with tabs[2]:
    st.subheader("⚖️ Comparaison entre Périodes")
    if len(valeurs) >= 2:
        cp1, cp2 = st.columns(2)
        with cp1:
            p1 = st.selectbox("Période A", valeurs, index=len(valeurs)-2, key="p1")
        with cp2:
            p2 = st.selectbox("Période B", valeurs, index=len(valeurs)-1, key="p2")

        ca1  = df_filtre[df_filtre[col_p]==p1]["chiffre_affaires"].sum()
        ca2  = df_filtre[df_filtre[col_p]==p2]["chiffre_affaires"].sum()
        evol = ((ca2-ca1)/ca1*100) if ca1 > 0 else 0

        cm1,cm2,cm3 = st.columns(3)
        cm1.metric(f"📅 {p1}", f"{ca1:,.0f} {devise}")
        cm2.metric(f"📅 {p2}", f"{ca2:,.0f} {devise}")
        cm3.metric("📈 Évolution", f"{ca2-ca1:+,.0f} {devise}", f"{evol:+.1f}%")

        if "produit" in df_filtre.columns:
            ca_p1 = df_filtre[df_filtre[col_p]==p1].groupby("produit")["chiffre_affaires"].sum().rename(f"CA {p1}")
            ca_p2 = df_filtre[df_filtre[col_p]==p2].groupby("produit")["chiffre_affaires"].sum().rename(f"CA {p2}")
            df_cmp = pd.concat([ca_p1,ca_p2],axis=1).fillna(0).reset_index()
            df_cmp["Évol. (%)"] = ((df_cmp[f"CA {p2}"]-df_cmp[f"CA {p1}"])/
                                   df_cmp[f"CA {p1}"].replace(0,1)*100).round(1)
            st.dataframe(df_cmp.style.background_gradient(subset=["Évol. (%)"],cmap="RdYlGn"),
                         use_container_width=True, hide_index=True)
    else:
        st.info("Pas assez de données pour comparer les périodes.")

# ── TAB 3 — Objectifs ────────────────────────────────────
with tabs[3]:
    st.subheader("🎯 Suivi des Objectifs")
    secteurs = df_complet["type_commerce"].unique() if "type_commerce" in df_complet.columns else ["Global"]
    objectifs = {}
    obj_cols = st.columns(3)
    for i, s in enumerate(secteurs):
        with obj_cols[i%3]:
            objectifs[s] = st.number_input(f"Objectif — {s} ({devise})",
                                           min_value=0, value=5000000, step=100000, key=f"obj_{s}")

    ca_reels = df_f.groupby("type_commerce")["chiffre_affaires"].sum() if "type_commerce" in df_f.columns else pd.Series()
    rows_obj = []
    for s in secteurs:
        r   = ca_reels.get(s, 0)
        o   = objectifs.get(s, 0)
        pct = (r/o*100) if o > 0 else 0
        rows_obj.append({
            "Secteur": s, "Objectif": o, "Réalisé": r,
            "Atteinte (%)": round(pct,1),
            "Statut": "✅ Atteint" if pct>=100 else ("⚠️ En cours" if pct>=50 else "❌ Non atteint")
        })
    df_obj = pd.DataFrame(rows_obj)
    st.dataframe(df_obj.style.format({
        "Objectif":     "{:,.0f}",
        "Réalisé":      "{:,.0f}",
        "Atteinte (%)": "{:.1f}%"
    }).background_gradient(subset=["Atteinte (%)"],cmap="RdYlGn"),
    use_container_width=True, hide_index=True)

    g_cols = st.columns(min(len(rows_obj),3))
    for i,row in enumerate(rows_obj):
        with g_cols[i%3]:
            gc = "#22C55E" if row["Atteinte (%)"]>=100 else ("#F59E0B" if row["Atteinte (%)"]>=50 else "#EF4444")
            fig_g = go.Figure(go.Indicator(
                mode="gauge+number", value=row["Atteinte (%)"],
                title={"text":row["Secteur"],"font":{"size":13}},
                number={"suffix":"%"},
                gauge={"axis":{"range":[0,150]},"bar":{"color":gc},
                       "steps":[{"range":[0,50],"color":"#FEE2E2"},
                                 {"range":[50,100],"color":"#FEF9C3"},
                                 {"range":[100,150],"color":"#DCFCE7"}],
                       "threshold":{"line":{"color":"#006400","width":3},"value":100}}
            ))
            fig_g.update_layout(height=220, margin=dict(t=40,b=10,l=20,r=20),
                                paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_g, use_container_width=True)

# ── TAB 4 — Prévisions IA ────────────────────────────────
with tabs[4]:
    st.subheader("🔮 Prévisions des ventes avec IA")
    horizon = st.radio("Horizon :", ["Prochain mois","Prochain trimestre","6 prochains mois"], horizontal=True)
    if st.button("🚀 Générer les prévisions", use_container_width=True):
        if not api_key:
            st.error("Veuillez entrer votre clé Groq dans le panneau gauche.")
        else:
            with st.spinner("Analyse en cours..."):
                try:
                    hist = df_filtre.groupby(["mois","type_commerce"])["chiffre_affaires"].sum().reset_index().to_string()
                    prompt = f"""Tu es un expert en commerce au Mali.
Analyse ces données de vente et prévois pour {horizon} :
{hist}

Génère :
1. Prévision du CA par secteur (en FCFA)
2. Secteurs en croissance vs déclin
3. 3 recommandations concrètes pour le marché malien"""
                    client = Groq(api_key=api_key)
                    resp   = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role":"user","content":prompt}],
                        max_tokens=1800
                    )
                    result = resp.choices[0].message.content
                    st.session_state.setdefault("historique",[]).append({
                        "date":    pd.Timestamp.now().strftime("%d/%m/%Y %H:%M"),
                        "titre":   f"Prévisions — {horizon}",
                        "contenu": result,
                    })
                    st.markdown(f"<div style='background:#F0FDF4;border:1px solid #BBF7D0;border-radius:14px;"
                                f"padding:24px;font-size:14px;line-height:1.8;'>{result.replace(chr(10),'<br>')}</div>",
                                unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Erreur IA : {e}")

# ── TAB 5 — Alertes ──────────────────────────────────────
with tabs[5]:
    st.subheader("🚨 Alertes Automatiques")
    alertes = []

    if len(valeurs) >= 2:
        ca_der  = df_filtre[df_filtre[col_p]==valeurs[-1]]["chiffre_affaires"].sum()
        ca_av   = df_filtre[df_filtre[col_p]==valeurs[-2]]["chiffre_affaires"].sum()
        if ca_av > 0:
            var = (ca_der-ca_av)/ca_av*100
            if var < -10:
                alertes.append(("🔴", f"Baisse importante de CA : {var:.1f}% entre {valeurs[-2]} et {valeurs[-1]}", "error"))
            elif var >= 15:
                alertes.append(("🟢", f"Hausse de CA : +{var:.1f}% entre {valeurs[-2]} et {valeurs[-1]}", "success"))

    if "type_commerce" in df_f.columns:
        ca_sect = df_f.groupby("type_commerce")["chiffre_affaires"].sum()
        moy     = ca_sect.mean()
        for s,c in ca_sect.items():
            if c < moy*0.4:
                alertes.append(("⚠️", f"{s} est en sous-performance ({c:,.0f} {devise})", "warning"))

    if not df_f.empty and "produit" in df_f.columns:
        best    = df_f.groupby("produit")["chiffre_affaires"].sum().idxmax()
        best_ca = df_f.groupby("produit")["chiffre_affaires"].sum().max()
        alertes.append(("⭐", f"Top produit : {best} ({best_ca:,.0f} {devise})", "info"))

    if alertes:
        for ico,msg,typ in alertes:
            if typ == "error":
                st.error(f"{ico} {msg}")
            elif typ == "success":
                st.success(f"{ico} {msg}")
            elif typ == "warning":
                st.warning(f"{ico} {msg}")
            else:
                st.info(f"{ico} {msg}")
    else:
        st.success("✅ Aucune alerte critique détectée.")

# ── TAB 6 — Export ───────────────────────────────────────
with tabs[6]:
    st.subheader("📥 Export des données")
    cx1, cx2 = st.columns(2)

    with cx1:
        st.markdown("#### 📊 Excel complet")
        if st.button("⬇️ Générer le fichier Excel", use_container_width=True):
            output = BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                wb      = writer.book
                fmt_h   = wb.add_format({"bold":True,"bg_color":"006400","font_color":"FFFFFF",
                                         "border":1,"align":"center","font_name":"Calibri"})
                fmt_num = wb.add_format({"num_format":"#,##0","border":1,"font_name":"Calibri"})

                df_complet.to_excel(writer, sheet_name="Données Brutes", index=False, startrow=1)
                ws1 = writer.sheets["Données Brutes"]
                for ci,h in enumerate(df_complet.columns):
                    ws1.write(1, ci, h, fmt_h)
                ws1.set_column("A:Z", 16)

                if "type_commerce" in df_f.columns:
                    par_sect = df_f.groupby("type_commerce")["chiffre_affaires"].sum().reset_index()
                    par_sect.to_excel(writer, sheet_name="Par Secteur", index=False, startrow=1)
                    ws2 = writer.sheets["Par Secteur"]
                    for ci,h in enumerate(par_sect.columns):
                        ws2.write(1, ci, h, fmt_h)

            output.seek(0)
            st.download_button(
                "📥 Télécharger Excel", output,
                f"TradeSahel_{username}_{pd.Timestamp.now().strftime('%Y%m%d')}.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

    with cx2:
        st.markdown("#### 📄 CSV")
        csv = df_f.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Télécharger CSV", csv,
            f"TradeSahel_{username}.csv",
            "text/csv",
            use_container_width=True
        )

st.markdown("---")
st.caption("🇲🇱 TradeSahel · Intelligence Commerciale · Mali")