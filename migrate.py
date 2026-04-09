import sqlite3

def ajouter_colonne_username():
    conn = sqlite3.connect("tradesahel.db")
    cursor = conn.cursor()
    
    # Vérifier si la colonne username existe
    cursor.execute("PRAGMA table_info(ventes)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'username' not in columns:
        print("➕ Ajout de la colonne username...")
        cursor.execute("ALTER TABLE ventes ADD COLUMN username TEXT")
        print("✅ Colonne username ajoutée")
    else:
        print("✅ Colonne username existe déjà")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    ajouter_colonne_username()
    print("✅ Migration terminée!")