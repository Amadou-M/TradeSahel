"""
tradesahel_db.py — Couche base de données SQLite pour TradeSahel
Toute la logique BDD est ici, séparée du code Streamlit.
"""
import sqlite3
import pandas as pd
import hashlib
import json
import os
from datetime import datetime
from contextlib import contextmanager

DB_FILE      = "tradesahel.db"
COMPTES_FILE = "tradesahel_comptes.json"

# ══════════════════════════════════════════════════════════
# CONNEXION — context manager, auto-close, thread-safe
# ══════════════════════════════════════════════════════════
@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

# ══════════════════════════════════════════════════════════
# INITIALISATION
# ══════════════════════════════════════════════════════════
def init_db():
    with get_conn() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS fichiers_importes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            nom_fichier TEXT    NOT NULL,
            username    TEXT    NOT NULL,
            nb_lignes   INTEGER NOT NULL,
            date_import TEXT    NOT NULL,
            hash_md5    TEXT    NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS ventes (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            fichier_id      INTEGER NOT NULL REFERENCES fichiers_importes(id) ON DELETE CASCADE,
            date            TEXT,
            produit         TEXT,
            type_commerce   TEXT    DEFAULT 'Commerce General',
            boutique_nom    TEXT    DEFAULT 'Principal',
            quantite        REAL    DEFAULT 0,
            prix_unitaire   REAL    DEFAULT 0,
            prix_achat      REAL,
            chiffre_affaires REAL   DEFAULT 0,
            marge           REAL,
            marge_pct       REAL,
            stock           REAL,
            source_fichier  TEXT
        );

        CREATE TABLE IF NOT EXISTS historique_ia (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT    NOT NULL,
            date     TEXT    NOT NULL,
            type_rapport TEXT NOT NULL,
            contenu  TEXT    NOT NULL
        );

        CREATE TABLE IF NOT EXISTS objectifs (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT    NOT NULL,
            entite   TEXT    NOT NULL,
            valeur   REAL    NOT NULL DEFAULT 0,
            type_obj TEXT    NOT NULL DEFAULT 'secteur',
            UNIQUE(username, entite, type_obj)
        );

        CREATE TABLE IF NOT EXISTS notes (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT    NOT NULL,
            date     TEXT    NOT NULL,
            contenu  TEXT    NOT NULL,
            priorite TEXT    DEFAULT 'info'
        );

        CREATE INDEX IF NOT EXISTS idx_ventes_date ON ventes(date);
        CREATE INDEX IF NOT EXISTS idx_ventes_produit ON ventes(produit);
        CREATE INDEX IF NOT EXISTS idx_ventes_fichier ON ventes(fichier_id);
        CREATE INDEX IF NOT EXISTS idx_hist_username ON historique_ia(username);
        """)

# ══════════════════════════════════════════════════════════
# IMPORT FICHIER
# ══════════════════════════════════════════════════════════
import hashlib as _hashlib

def hash_fichier(contenu_bytes: bytes) -> str:
    return _hashlib.md5(contenu_bytes).hexdigest()

def fichier_deja_importe(hash_md5: str) -> bool:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id FROM fichiers_importes WHERE hash_md5 = ?", (hash_md5,)
        ).fetchone()
        return row is not None

def enregistrer_fichier(nom: str, username: str, nb_lignes: int, hash_md5: str) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO fichiers_importes(nom_fichier,username,nb_lignes,date_import,hash_md5) VALUES(?,?,?,?,?)",
            (nom, username, nb_lignes, datetime.now().strftime("%d/%m/%Y %H:%M"), hash_md5)
        )
        return cur.lastrowid

def inserer_ventes(df: pd.DataFrame, fichier_id: int, nom_fichier: str):
    cols_map = {
        "date": "date", "produit": "produit", "type_commerce": "type_commerce",
        "boutique_nom": "boutique_nom", "quantite": "quantite",
        "prix_unitaire": "prix_unitaire", "prix_achat": "prix_achat",
        "chiffre_affaires": "chiffre_affaires", "marge": "marge",
        "marge_pct": "marge_pct", "stock": "stock",
    }
    rows = []
    for _, r in df.iterrows():
        row = [fichier_id]
        for col_df, col_db in cols_map.items():
            val = r.get(col_df, None)
            if pd.isna(val) if not isinstance(val, str) else False:
                val = None
            elif hasattr(val, "strftime"):
                val = str(val)[:10]
            elif hasattr(val, "item"):
                val = val.item()
            row.append(val)
        row.append(nom_fichier)
        rows.append(tuple(row))

    with get_conn() as conn:
        conn.executemany(
            """INSERT INTO ventes(
                fichier_id,date,produit,type_commerce,boutique_nom,
                quantite,prix_unitaire,prix_achat,chiffre_affaires,
                marge,marge_pct,stock,source_fichier
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            rows
        )

# ══════════════════════════════════════════════════════════
# LECTURE DONNÉES - CORRIGÉE
# ══════════════════════════════════════════════════════════
def charger_ventes(username: str = None) -> pd.DataFrame:
    """Charge toutes les ventes pour un utilisateur ou toutes si username=None"""
    with get_conn() as conn:
        if username:
            # Vérifier d'abord si l'utilisateur a des fichiers
            fichiers = conn.execute(
                "SELECT id FROM fichiers_importes WHERE username=?", (username,)
            ).fetchall()
            
            if not fichiers:
                print(f"DEBUG: Aucun fichier trouvé pour {username}")
                return pd.DataFrame()
            
            query = """
            SELECT v.* FROM ventes v
            JOIN fichiers_importes f ON v.fichier_id = f.id
            WHERE f.username = ?
            ORDER BY v.date
            """
            df = pd.read_sql_query(query, conn, params=(username,))
            print(f"DEBUG: Chargé {len(df)} lignes pour {username}")
        else:
            df = pd.read_sql_query("SELECT * FROM ventes ORDER BY date", conn)
            print(f"DEBUG: Chargé {len(df)} lignes total")

    if df.empty:
        return df
    
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    df["jour"] = df["date"].dt.strftime("%d/%m/%Y")
    df["semaine"] = df["date"].dt.strftime("Sem. %W · %Y")
    df["mois"] = df["date"].dt.strftime("%b %Y")
    df["annee"] = df["date"].dt.strftime("%Y")
    return df

def lister_fichiers(username: str) -> pd.DataFrame:
    with get_conn() as conn:
        return pd.read_sql_query(
            "SELECT nom_fichier, nb_lignes, date_import FROM fichiers_importes WHERE username=? ORDER BY id DESC",
            conn, params=(username,)
        )

def supprimer_fichier(nom_fichier: str, username: str):
    with get_conn() as conn:
        conn.execute(
            "DELETE FROM fichiers_importes WHERE nom_fichier=? AND username=?",
            (nom_fichier, username)
        )

def vider_donnees(username: str):
    with get_conn() as conn:
        conn.execute(
            "DELETE FROM fichiers_importes WHERE username=?", (username,)
        )

# ══════════════════════════════════════════════════════════
# HISTORIQUE IA
# ══════════════════════════════════════════════════════════
def sauvegarder_rapport_ia(username: str, type_rapport: str, contenu: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO historique_ia(username,date,type_rapport,contenu) VALUES(?,?,?,?)",
            (username, datetime.now().strftime("%d/%m/%Y %H:%M"), type_rapport, contenu)
        )

def charger_historique_ia(username: str) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM historique_ia WHERE username=? ORDER BY id DESC",
            (username,)
        ).fetchall()
    return [dict(r) for r in rows]

def supprimer_rapport_ia(rapport_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM historique_ia WHERE id=?", (rapport_id,))

# ══════════════════════════════════════════════════════════
# OBJECTIFS
# ══════════════════════════════════════════════════════════
def sauvegarder_objectif(username: str, entite: str, valeur: float, type_obj: str = "secteur"):
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO objectifs(username,entite,valeur,type_obj) VALUES(?,?,?,?)
               ON CONFLICT(username,entite,type_obj) DO UPDATE SET valeur=excluded.valeur""",
            (username, entite, valeur, type_obj)
        )

def charger_objectifs(username: str, type_obj: str = "secteur") -> dict:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT entite, valeur FROM objectifs WHERE username=? AND type_obj=?",
            (username, type_obj)
        ).fetchall()
    return {r["entite"]: r["valeur"] for r in rows}

# ══════════════════════════════════════════════════════════
# NOTES
# ══════════════════════════════════════════════════════════
def ajouter_note(username: str, contenu: str, priorite: str = "info"):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO notes(username,date,contenu,priorite) VALUES(?,?,?,?)",
            (username, datetime.now().strftime("%d/%m/%Y %H:%M"), contenu, priorite)
        )

def charger_notes(username: str) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM notes WHERE username=? ORDER BY id DESC", (username,)
        ).fetchall()
    return [dict(r) for r in rows]

def supprimer_note(note_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM notes WHERE id=?", (note_id,))

# ══════════════════════════════════════════════════════════
# COMPTES
# ══════════════════════════════════════════════════════════
def hash_pwd(pwd: str) -> str:
    return hashlib.sha256(pwd.encode()).hexdigest()

def charger_comptes() -> dict:
    if os.path.exists(COMPTES_FILE):
        try:
            with open(COMPTES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    comptes = {
        "admin": {"password": hash_pwd("admin123"), "boutique": "Boutique Principale", "email": "admin@tradesahel.ml"},
        "mali1": {"password": hash_pwd("mali2025"), "boutique": "Shop Bamako", "email": "bamako@tradesahel.ml"},
    }
    sauvegarder_comptes(comptes)
    return comptes

def sauvegarder_comptes(comptes: dict):
    with open(COMPTES_FILE, "w", encoding="utf-8") as f:
        json.dump(comptes, f, ensure_ascii=False, indent=2)

# ══════════════════════════════════════════════════════════
# STATISTIQUES BDD
# ══════════════════════════════════════════════════════════
def stats_bdd(username: str) -> dict:
    with get_conn() as conn:
        nb_fichiers = conn.execute(
            "SELECT COUNT(*) FROM fichiers_importes WHERE username=?", (username,)
        ).fetchone()[0]
        nb_ventes = conn.execute(
            """SELECT COUNT(*) FROM ventes v
               JOIN fichiers_importes f ON v.fichier_id=f.id WHERE f.username=?""",
            (username,)
        ).fetchone()[0]
        nb_rapports = conn.execute(
            "SELECT COUNT(*) FROM historique_ia WHERE username=?", (username,)
        ).fetchone()[0]
        derniere_import = conn.execute(
            "SELECT date_import FROM fichiers_importes WHERE username=? ORDER BY id DESC LIMIT 1",
            (username,)
        ).fetchone()
    return {
        "nb_fichiers": nb_fichiers,
        "nb_ventes": nb_ventes,
        "nb_rapports": nb_rapports,
        "derniere_import": derniere_import[0] if derniere_import else "—"
    }

# ══════════════════════════════════════════════════════════
# DIAGNOSTIC - AJOUTÉ
# ══════════════════════════════════════════════════════════
def diagnostique_base(username: str = None):
    """Fonction de diagnostic pour vérifier les données"""
    with get_conn() as conn:
        print("\n=== DIAGNOSTIC BASE DE DONNEES ===")
        
        # Tous les fichiers
        fichiers = conn.execute("SELECT * FROM fichiers_importes").fetchall()
        print(f"Total fichiers: {len(fichiers)}")
        for f in fichiers:
            print(f"  - {dict(f)}")
        
        # Toutes les ventes
        nb_ventes = conn.execute("SELECT COUNT(*) FROM ventes").fetchone()[0]
        print(f"Total ventes: {nb_ventes}")
        
        if nb_ventes > 0:
            sample = conn.execute("SELECT * FROM ventes LIMIT 3").fetchall()
            print("Echantillon ventes:")
            for s in sample:
                print(f"  - {dict(s)}")
        
        if username:
            user_fichiers = conn.execute(
                "SELECT * FROM fichiers_importes WHERE username=?", (username,)
            ).fetchall()
            print(f"\nFichiers pour {username}: {len(user_fichiers)}")
            
            user_ventes = conn.execute(
                """SELECT COUNT(*) FROM ventes v
                   JOIN fichiers_importes f ON v.fichier_id=f.id
                   WHERE f.username=?""",
                (username,)
            ).fetchone()[0]
            print(f"Ventes pour {username}: {user_ventes}")