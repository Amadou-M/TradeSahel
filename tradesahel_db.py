"""
tradesahel_db.py - Base de données pour TradeSahel
Version complète et stable
"""

import sqlite3
import pandas as pd
import hashlib
import json
import os
import shutil
from datetime import datetime, timedelta
from contextlib import contextmanager

DB_FILE = "tradesahel.db"
COMPTES_FILE = "tradesahel_comptes.json"
BACKUP_DIR = "backups"

if not os.path.exists(BACKUP_DIR):
    os.makedirs(BACKUP_DIR)

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

def init_db():
    with get_conn() as conn:
        # Table fichiers_importes
        conn.execute("""
        CREATE TABLE IF NOT EXISTS fichiers_importes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            nom_fichier TEXT    NOT NULL,
            username    TEXT    NOT NULL,
            nb_lignes   INTEGER NOT NULL,
            date_import TEXT    NOT NULL,
            hash_md5    TEXT    NOT NULL UNIQUE
        )
        """)
        
        # Table ventes
        conn.execute("""
        CREATE TABLE IF NOT EXISTS ventes (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            fichier_id       INTEGER,
            date             TEXT,
            produit          TEXT,
            type_commerce    TEXT,
            quantite         REAL,
            prix_unitaire    REAL,
            prix_achat       REAL,
            chiffre_affaires REAL,
            marge            REAL,
            stock            REAL,
            username         TEXT,
            source_fichier   TEXT,
            ca_reel          REAL,
            marge_pct        REAL,
            cout_total       REAL,
            jour             TEXT,
            semaine          TEXT,
            mois             TEXT,
            annee            TEXT
        )
        """)
        
        # Table historique_ia
        conn.execute("""
        CREATE TABLE IF NOT EXISTS historique_ia (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            username     TEXT NOT NULL,
            type_rapport TEXT NOT NULL,
            contenu      TEXT NOT NULL,
            date         TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Table chat_history
        conn.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            username  TEXT NOT NULL,
            role      TEXT NOT NULL,
            message   TEXT NOT NULL,
            date      TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Table objectifs
        conn.execute("""
        CREATE TABLE IF NOT EXISTS objectifs (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            username  TEXT NOT NULL,
            entite    TEXT NOT NULL,
            valeur    REAL NOT NULL,
            type_obj  TEXT NOT NULL,
            UNIQUE(username, entite, type_obj)
        )
        """)
        
        # Table notes
        conn.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            username  TEXT NOT NULL,
            contenu   TEXT NOT NULL,
            priorite  TEXT NOT NULL,
            date      TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Table stocks
        conn.execute("""
        CREATE TABLE IF NOT EXISTS stocks (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT NOT NULL,
            produit     TEXT NOT NULL,
            stock       REAL NOT NULL DEFAULT 0,
            date_maj    TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(username, produit)
        )
        """)

def backup_bdd():
    if not os.path.exists(DB_FILE):
        return None
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(BACKUP_DIR, f"tradesahel_backup_{timestamp}.db")
    shutil.copy2(DB_FILE, backup_file)
    return backup_file

def optimiser_bdd():
    with get_conn() as conn:
        conn.execute("VACUUM")
        conn.execute("ANALYZE")

def get_performance_stats(hours: int = 24):
    return []

def clear_cache(username: str = None):
    pass

def lister_backups():
    if not os.path.exists(BACKUP_DIR):
        return []
    files = [f for f in os.listdir(BACKUP_DIR) if f.endswith('.db')]
    files.sort(reverse=True)
    return files

def valider_donnees_ventes(df: pd.DataFrame):
    errors = []
    required = ["date", "produit", "quantite", "prix_unitaire"]
    for col in required:
        if col not in df.columns:
            errors.append(f"Colonne manquante : {col}")
    return len(errors) == 0, errors

def sauvegarder_message_chat(username: str, role: str, message: str):
    with get_conn() as conn:
        conn.execute("INSERT INTO chat_history (username, role, message) VALUES (?, ?, ?)",
                     (username, role, message))

def charger_historique_chat(username: str):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, role, message, date FROM chat_history WHERE username=? ORDER BY date DESC LIMIT 100",
            (username,)
        ).fetchall()
    return [dict(row) for row in rows]

def supprimer_historique_chat(username: str):
    with get_conn() as conn:
        conn.execute("DELETE FROM chat_history WHERE username=?", (username,))

def hash_fichier(contenu: bytes) -> str:
    return hashlib.md5(contenu).hexdigest()

def fichier_deja_importe(hash_md5: str) -> bool:
    with get_conn() as conn:
        return conn.execute("SELECT 1 FROM fichiers_importes WHERE hash_md5=?", (hash_md5,)).fetchone() is not None

def enregistrer_fichier(nom_fichier: str, username: str, nb_lignes: int, hash_md5: str) -> int:
    with get_conn() as conn:
        cur = conn.execute("""
            INSERT INTO fichiers_importes (nom_fichier, username, nb_lignes, date_import, hash_md5)
            VALUES (?, ?, ?, ?, ?)
        """, (nom_fichier, username, nb_lignes, datetime.now().isoformat(), hash_md5))
        return cur.lastrowid

def inserer_ventes(df: pd.DataFrame, fichier_id: int, nom_fichier: str):
    with get_conn() as conn:
        for _, row in df.iterrows():
            try:
                conn.execute("""
                    INSERT INTO ventes (
                        fichier_id, date, produit, type_commerce, quantite, 
                        prix_unitaire, prix_achat, chiffre_affaires, marge, 
                        stock, username, source_fichier
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    fichier_id,
                    str(row.get('date', '')),
                    str(row.get('produit', '')),
                    str(row.get('type_commerce', 'Commerce Général')),
                    float(row.get('quantite', 0)) if pd.notna(row.get('quantite')) else 0,
                    float(row.get('prix_unitaire', 0)) if pd.notna(row.get('prix_unitaire')) else 0,
                    float(row.get('prix_achat', 0)) if pd.notna(row.get('prix_achat')) else None,
                    float(row.get('chiffre_affaires', 0)) if pd.notna(row.get('chiffre_affaires')) else 0,
                    float(row.get('marge', 0)) if pd.notna(row.get('marge')) else None,
                    float(row.get('stock', 100)) if pd.notna(row.get('stock')) else 100,
                    row.get('username'),
                    nom_fichier
                ))
            except Exception as e:
                print(f"Erreur insertion: {e}")

def charger_ventes(username: str) -> pd.DataFrame:
    with get_conn() as conn:
        df = pd.read_sql_query(
            "SELECT * FROM ventes WHERE username=? OR username IS NULL ORDER BY date DESC",
            conn, params=(username,)
        )
    
    if df.empty:
        return df
    
    if 'username' in df.columns:
        mask = df['username'].isna()
        if mask.any():
            with get_conn() as conn:
                for idx in df[mask].index:
                    try:
                        conn.execute("UPDATE ventes SET username=? WHERE id=?", (username, df.loc[idx, 'id']))
                    except:
                        pass
    
    if 'date' in df.columns and not df.empty:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df['jour'] = df['date'].dt.strftime('%d/%m/%Y')
        df['semaine'] = df['date'].dt.strftime('Sem. %W · %Y')
        df['mois'] = df['date'].dt.strftime('%b %Y')
        df['annee'] = df['date'].dt.strftime('%Y')
    
    return df

def lister_fichiers(username: str):
    with get_conn() as conn:
        return pd.read_sql_query(
            "SELECT nom_fichier, nb_lignes, date_import FROM fichiers_importes WHERE username=? ORDER BY id DESC",
            conn, params=(username,)
        )

def supprimer_fichier(nom_fichier: str, username: str):
    with get_conn() as conn:
        row = conn.execute("SELECT id FROM fichiers_importes WHERE nom_fichier=? AND username=?", 
                          (nom_fichier, username)).fetchone()
        if row:
            conn.execute("DELETE FROM ventes WHERE fichier_id=?", (row['id'],))
            conn.execute("DELETE FROM fichiers_importes WHERE id=?", (row['id'],))

def vider_donnees(username: str):
    with get_conn() as conn:
        conn.execute("DELETE FROM ventes WHERE username=?", (username,))
        conn.execute("DELETE FROM fichiers_importes WHERE username=?", (username,))
        conn.execute("DELETE FROM historique_ia WHERE username=?", (username,))
        conn.execute("DELETE FROM objectifs WHERE username=?", (username,))
        conn.execute("DELETE FROM notes WHERE username=?", (username,))
        conn.execute("DELETE FROM stocks WHERE username=?", (username,))
        conn.execute("DELETE FROM chat_history WHERE username=?", (username,))

def sauvegarder_rapport_ia(username: str, type_rapport: str, contenu: str):
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO historique_ia (username, type_rapport, contenu, date)
            VALUES (?, ?, ?, ?)
        """, (username, type_rapport, contenu, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

def charger_historique_ia(username: str):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, type_rapport, contenu, date FROM historique_ia WHERE username=? ORDER BY date DESC",
            (username,)
        ).fetchall()
    return [dict(row) for row in rows]

def supprimer_rapport_ia(rapport_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM historique_ia WHERE id=?", (rapport_id,))

def sauvegarder_objectif(username: str, entite: str, valeur: float, type_obj: str = "secteur"):
    with get_conn() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO objectifs (username, entite, valeur, type_obj)
            VALUES (?, ?, ?, ?)
        """, (username, entite, valeur, type_obj))

def charger_objectifs(username: str, type_obj: str = "secteur") -> dict:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT entite, valeur FROM objectifs WHERE username=? AND type_obj=?",
            (username, type_obj)
        ).fetchall()
    return {row['entite']: row['valeur'] for row in rows}

def ajouter_note(username: str, contenu: str, priorite: str = "info"):
    with get_conn() as conn:
        conn.execute("INSERT INTO notes (username, contenu, priorite) VALUES (?, ?, ?)",
                     (username, contenu, priorite))

def charger_notes(username: str):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, contenu, priorite, date FROM notes WHERE username=? ORDER BY date DESC",
            (username,)
        ).fetchall()
    return [dict(row) for row in rows]

def supprimer_note(note_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM notes WHERE id=?", (note_id,))

def modifier_note(note_id: int, nouveau_contenu: str, nouvelle_priorite: str):
    with get_conn() as conn:
        conn.execute("""
            UPDATE notes SET contenu = ?, priorite = ?, date = ? WHERE id = ?
        """, (nouveau_contenu, nouvelle_priorite, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), note_id))

def ajouter_stock(username: str, produit: str, quantite: float):
    with get_conn() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO stocks (username, produit, stock)
            VALUES (?, ?, ?)
        """, (username, produit, quantite))

def charger_stocks(username: str) -> pd.DataFrame:
    with get_conn() as conn:
        return pd.read_sql_query(
            "SELECT produit, stock, date_maj FROM stocks WHERE username=? ORDER BY produit",
            conn, params=(username,)
        )

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
        "admin": {"password": hash_pwd("admin123"), "boutique": "Boutique Principale", "email": "admin@tradesahel.ml"},
        "mali1": {"password": hash_pwd("mali2025"), "boutique": "Shop Bamako", "email": "bamako@tradesahel.ml"}
    }
    sauvegarder_comptes(comptes)
    return comptes

def sauvegarder_comptes(comptes: dict):
    with open(COMPTES_FILE, "w", encoding="utf-8") as f:
        json.dump(comptes, f, ensure_ascii=False, indent=2)

def stats_bdd(username: str) -> dict:
    with get_conn() as conn:
        nb_fichiers = conn.execute("SELECT COUNT(*) FROM fichiers_importes WHERE username=?", (username,)).fetchone()[0]
        nb_ventes = conn.execute("SELECT COUNT(*) FROM ventes WHERE username=?", (username,)).fetchone()[0]
        nb_rapports = conn.execute("SELECT COUNT(*) FROM historique_ia WHERE username=?", (username,)).fetchone()[0]
        nb_notes = conn.execute("SELECT COUNT(*) FROM notes WHERE username=?", (username,)).fetchone()[0]
        nb_chat = conn.execute("SELECT COUNT(*) FROM chat_history WHERE username=?", (username,)).fetchone()[0]
        
        derniere_row = conn.execute("SELECT date_import FROM fichiers_importes WHERE username=? ORDER BY id DESC LIMIT 1", (username,)).fetchone()
        derniere_import = derniere_row['date_import'] if derniere_row else "—"
        
    return {
        "nb_fichiers": nb_fichiers,
        "nb_ventes": nb_ventes,
        "nb_rapports": nb_rapports,
        "nb_notes": nb_notes,
        "nb_chat": nb_chat,
        "derniere_import": derniere_import
    }

# Initialiser la BDD
init_db()
print("✅ Base de données initialisée")