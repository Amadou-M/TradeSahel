"""
tradesahel_db.py — Base de données complète pour TradeSahel
Version finale avec gestion des stocks (CRUD)
"""

import sqlite3
import pandas as pd
import hashlib
import json
import os
from datetime import datetime
from contextlib import contextmanager

DB_FILE = "tradesahel.db"
COMPTES_FILE = "tradesahel_comptes.json"

# ====================== CONNEXION ======================
@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

# ====================== INITIALISATION ======================
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
            fichier_id      INTEGER,
            date            TEXT,
            produit         TEXT,
            type_commerce   TEXT,
            quantite        REAL,
            prix_unitaire   REAL,
            prix_achat      REAL,
            chiffre_affaires REAL,
            marge           REAL,
            stock           REAL,
            username        TEXT
        );

        CREATE TABLE IF NOT EXISTS historique_ia (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            username     TEXT NOT NULL,
            type_rapport TEXT NOT NULL,
            contenu      TEXT NOT NULL,
            date         TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS objectifs (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            username  TEXT NOT NULL,
            entite    TEXT NOT NULL,
            valeur    REAL NOT NULL,
            type_obj  TEXT NOT NULL,
            UNIQUE(username, entite, type_obj)
        );

        CREATE TABLE IF NOT EXISTS notes (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            username  TEXT NOT NULL,
            contenu   TEXT NOT NULL,
            priorite  TEXT NOT NULL,
            date      TEXT DEFAULT CURRENT_TIMESTAMP
        );

        -- Table Stocks avec CRUD
        CREATE TABLE IF NOT EXISTS stocks (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT NOT NULL,
            produit     TEXT NOT NULL,
            stock       REAL NOT NULL DEFAULT 0,
            date_maj    TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(username, produit)
        );
        """)

# ====================== STOCKS - CRUD ======================
def ajouter_stock(username: str, produit: str, quantite: float):
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO stocks (username, produit, stock)
            VALUES (?, ?, ?)
            ON CONFLICT(username, produit) 
            DO UPDATE SET stock = excluded.stock, date_maj = CURRENT_TIMESTAMP
        """, (username, produit, quantite))

def modifier_stock(username: str, produit: str, nouvelle_quantite: float):
    ajouter_stock(username, produit, nouvelle_quantite)

def supprimer_stock(username: str, produit: str):
    with get_conn() as conn:
        conn.execute("DELETE FROM stocks WHERE username=? AND produit=?", (username, produit))

def charger_stocks(username: str) -> pd.DataFrame:
    with get_conn() as conn:
        return pd.read_sql_query(
            "SELECT produit, stock, date_maj FROM stocks WHERE username=? ORDER BY produit",
            conn, params=(username,)
        )

# ====================== AUTRES FONCTIONS (conservées) ======================
def hash_fichier(contenu: bytes) -> str:
    return hashlib.md5(contenu).hexdigest()

def fichier_deja_importe(hash_md5: str) -> bool:
    with get_conn() as conn:
        row = conn.execute("SELECT 1 FROM fichiers_importes WHERE hash_md5=?", (hash_md5,)).fetchone()
    return row is not None

def enregistrer_fichier(nom_fichier: str, username: str, nb_lignes: int, hash_md5: str) -> int:
    with get_conn() as conn:
        cur = conn.execute("""
            INSERT INTO fichiers_importes (nom_fichier, username, nb_lignes, date_import, hash_md5)
            VALUES (?, ?, ?, ?, ?)
        """, (nom_fichier, username, nb_lignes, datetime.now().isoformat(), hash_md5))
        return cur.lastrowid

def inserer_ventes(df: pd.DataFrame, fichier_id: int, nom_fichier: str):
    df = df.copy()
    df["fichier_id"] = fichier_id
    df["username"] = username if 'username' in globals() else "admin"
    with get_conn() as conn:
        df.to_sql("ventes", conn, if_exists="append", index=False)

def charger_ventes(username: str) -> pd.DataFrame:
    with get_conn() as conn:
        return pd.read_sql_query(
            "SELECT * FROM ventes WHERE username=? ORDER BY date DESC",
            conn, params=(username,)
        )

def lister_fichiers(username: str) -> pd.DataFrame:
    with get_conn() as conn:
        return pd.read_sql_query(
            "SELECT nom_fichier, nb_lignes, date_import FROM fichiers_importes WHERE username=?",
            conn, params=(username,)
        )

def supprimer_fichier(nom_fichier: str, username: str):
    with get_conn() as conn:
        conn.execute("DELETE FROM fichiers_importes WHERE nom_fichier=? AND username=?", (nom_fichier, username))
        conn.execute("DELETE FROM ventes WHERE username=?", (username,))

def vider_donnees(username: str):
    with get_conn() as conn:
        for table in ["ventes", "fichiers_importes", "historique_ia", "objectifs", "notes", "stocks"]:
            conn.execute(f"DELETE FROM {table} WHERE username=?", (username,))

# Historique IA, Objectifs, Notes (conservés)
def sauvegarder_rapport_ia(username: str, type_rapport: str, contenu: str):
    with get_conn() as conn:
        conn.execute("INSERT INTO historique_ia (username, type_rapport, contenu) VALUES (?, ?, ?)",
                     (username, type_rapport, contenu))

def charger_historique_ia(username: str):
    with get_conn() as conn:
        return pd.read_sql_query(
            "SELECT id, type_rapport, contenu, date FROM historique_ia WHERE username=? ORDER BY date DESC",
            conn, params=(username,)
        ).to_dict("records")

def supprimer_rapport_ia(rapport_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM historique_ia WHERE id=?", (rapport_id,))

def sauvegarder_objectif(username: str, entite: str, valeur: float, type_obj: str = "produit"):
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO objectifs (username, entite, valeur, type_obj)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(username, entite, type_obj) DO UPDATE SET valeur=excluded.valeur
        """, (username, entite, valeur, type_obj))

def charger_objectifs(username: str, type_obj: str):
    with get_conn() as conn:
        df = pd.read_sql_query(
            "SELECT entite, valeur FROM objectifs WHERE username=? AND type_obj=?",
            conn, params=(username, type_obj)
        )
    return dict(zip(df["entite"], df["valeur"]))

def ajouter_note(username: str, contenu: str, priorite: str = "info"):
    with get_conn() as conn:
        conn.execute("INSERT INTO notes (username, contenu, priorite) VALUES (?, ?, ?)",
                     (username, contenu, priorite))

def charger_notes(username: str):
    with get_conn() as conn:
        return pd.read_sql_query(
            "SELECT id, contenu, priorite, date FROM notes WHERE username=? ORDER BY date DESC",
            conn, params=(username,)
        ).to_dict("records")

def supprimer_note(note_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM notes WHERE id=?", (note_id,))

def hash_pwd(pwd: str) -> str:
    return hashlib.sha256(pwd.encode()).hexdigest()

def charger_comptes() -> dict:
    if os.path.exists(COMPTES_FILE):
        try:
            with open(COMPTES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    comptes = {
        "admin": {"password": hash_pwd("admin123"), "boutique": "Boutique Principale"},
        "mali1": {"password": hash_pwd("mali2025"), "boutique": "Shop Bamako"}
    }
    sauvegarder_comptes(comptes)
    return comptes

def sauvegarder_comptes(comptes: dict):
    with open(COMPTES_FILE, "w", encoding="utf-8") as f:
        json.dump(comptes, f, ensure_ascii=False, indent=2)

def stats_bdd(username: str) -> dict:
    with get_conn() as conn:
        return {
            "nb_fichiers": conn.execute("SELECT COUNT(*) FROM fichiers_importes WHERE username=?", (username,)).fetchone()[0],
            "nb_ventes": conn.execute("SELECT COUNT(*) FROM ventes WHERE username=?", (username,)).fetchone()[0],
            "nb_rapports": conn.execute("SELECT COUNT(*) FROM historique_ia WHERE username=?", (username,)).fetchone()[0],
            "derniere_import": conn.execute("SELECT date_import FROM fichiers_importes WHERE username=? ORDER BY id DESC LIMIT 1", (username,)).fetchone()[0] or "—"
        }

# Initialisation
init_db()