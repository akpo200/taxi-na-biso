import sqlite3
from datetime import datetime
import random

DB_NAME = "crm_taxi_na_biso.db"

clients = [
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
    # On s'assure que la table existe avant de peupler
    # Note: On utilise le type INTEGER PRIMARY KEY AUTOINCREMENT pour SQLite par défaut ici
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            telephone TEXT NOT NULL UNIQUE,
            vehicule_prefere TEXT,
            notes TEXT,
            palier TEXT DEFAULT 'Nouveau',
            total_courses INTEGER DEFAULT 0,
            date_creation TEXT
        )
    ''')
    conn.commit()

def populate():
    conn = sqlite3.connect(DB_NAME)
    init_db(conn) # Initialisation ajoutée
    cursor = conn.cursor()
    
    date_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    for nom, tel, vehicule, courses, palier in clients:
        try:
            cursor.execute('''
                INSERT INTO clients (nom, telephone, vehicule_prefere, total_courses, palier, date_creation)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (nom, tel, vehicule, courses, palier, date_now))
        except sqlite3.IntegrityError:
            pass # Éviter les doublons
            
    conn.commit()
    conn.close()
    print("Base de données peuplée avec succès !")

if __name__ == "__main__":
    populate()
