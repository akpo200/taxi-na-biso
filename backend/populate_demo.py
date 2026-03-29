import sqlite3
import os
from datetime import datetime
import random

# --- Logic Alignée avec main.py ---
DB_NAME = os.environ.get("DATABASE_URL", "crm_taxi_na_biso.db")
IS_POSTGRES = DB_NAME.startswith("postgres")

def get_db_connection():
    if IS_POSTGRES:
        import psycopg2
        url = DB_NAME
        if "sslmode" not in url:
            url += "?sslmode=require" if "?" in url else "?sslmode=require"
        conn = psycopg2.connect(url)
    else:
        conn = sqlite3.connect(DB_NAME)
    return conn

clients_demo = [
    ("Christelle Mbaye", "+243 81 234 5678", "Basic (Toyota Aygo)", 0, "Nouveau"),
    ("Jean-Claude Bolamba", "+243 82 111 2233", "Confort (SUV)", 12, "Argent"),
    ("Nancy Akpo", "+243 85 999 0011", "VIP (Sedan Luxe)", 45, "VIP"),
    ("Patrick Kalala", "+243 81 888 7766", "Basic (Toyota Aygo)", 4, "Bronze"),
    ("Sarah Mbuyi", "+243 81 555 4433", "Confort (SUV)", 22, "Or"),
    ("Derrick Mavungu", "+243 82 444 3322", "Basic (Toyota Aygo)", 0, "Nouveau"),
    ("Marie-José", "+243 81 000 1122", "VIP (Sedan Luxe)", 8, "Argent"),
]

def init_db(conn):
    cursor = conn.cursor()
    id_type = "SERIAL PRIMARY KEY" if IS_POSTGRES else "INTEGER PRIMARY KEY AUTOINCREMENT"
    
    create_table_query = f'''
        CREATE TABLE IF NOT EXISTS clients (
            id {id_type},
            nom TEXT NOT NULL,
            telephone TEXT NOT NULL UNIQUE,
            vehicule_prefere TEXT,
            notes TEXT,
            palier TEXT DEFAULT 'Nouveau',
            total_courses INTEGER DEFAULT 0,
            date_creation TEXT
        )
    '''
    cursor.execute(create_table_query)
    conn.commit()

def populate():
    print(f"Connexion à la base de données: {'PostgreSQL' if IS_POSTGRES else 'SQLite'}...")
    conn = get_db_connection()
    init_db(conn)
    cursor = conn.cursor()
    
    date_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    for nom, tel, vehicule, courses, palier in clients_demo:
        try:
            # Gestion des paramètres selon le dialecte
            param_char = "$" if IS_POSTGRES else "?"
            p = [param_char] * 6
            if IS_POSTGRES: p = [f"${i+1}" for i in range(6)]
            
            insert_query = f'''
                INSERT INTO clients (nom, telephone, vehicule_prefere, total_courses, palier, date_creation)
                VALUES ({", ".join(p)})
            '''
            cursor.execute(insert_query, (nom, tel, vehicule, courses, palier, date_now))
        except Exception as e:
            # Erreur d'intégrité (doublon) ignorée silencieusement
            pass
            
    conn.commit()
    conn.close()
    print("Base de données peuplée avec succès !")

if __name__ == "__main__":
    populate()
