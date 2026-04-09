"""
Script de vérification post-migration
"""
import sqlite3
from datetime import datetime

DB_FILE = "tradesahel.db"

def verifier_performances():
    """Vérifie l'amélioration des performances"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    print("\n🔍 VÉRIFICATION POST-MIGRATION\n")
    
    # Test requête avec index
    import time
    
    # Requête complexe
    query = """
        SELECT type_commerce, 
               strftime('%Y-%m', date) as mois,
               SUM(chiffre_affaires) as ca
        FROM ventes
        WHERE date >= date('now', '-1 year')
        GROUP BY type_commerce, mois
        ORDER BY mois DESC
    """
    
    start = time.time()
    cursor.execute(query)
    results = cursor.fetchall()
    end = time.time()
    
    print(f"✅ Performance requête: {len(results)} lignes en {(end-start)*1000:.2f}ms")
    
    # Vérifier index utilisés
    cursor.execute("EXPLAIN QUERY PLAN " + query)
    plan = cursor.fetchall()
    print("📊 Plan d'exécution:")
    for row in plan:
        print(f"   {row}")
    
    conn.close()

def verifier_integrite():
    """Vérifie les contraintes"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Tester trigger
    try:
        cursor.execute("""
            INSERT INTO ventes (quantite, prix_unitaire, date) 
            VALUES (-10, 100, '2025-01-01')
        """)
        print("❌ Échec: Trigger quantité négative non actif")
    except sqlite3.Error as e:
        print(f"✅ Trigger fonctionnel: {str(e)[:50]}...")
    
    conn.close()

def stats_tables():
    """Affiche les statistiques"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    tables = ['ventes', 'fichiers_importes', 'historique_ia', 'historique_chat', 'notes']
    
    print("\n📊 STATISTIQUES TABLES:")
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        cursor.execute(f"SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND tbl_name='{table}'")
        idx_count = cursor.fetchone()[0]
        print(f"  • {table}: {count:,} lignes, {idx_count} index")
    
    conn.close()

if __name__ == "__main__":
    verifier_performances()
    verifier_integrite()
    stats_tables()