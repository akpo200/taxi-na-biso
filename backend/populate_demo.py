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

def populate():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    date_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    for nom, tel, vehicule, courses, palier in clients:
        try:
            cursor.execute('''
                INSERT INTO clients (nom, telephone, vehicule_prefere, total_courses, palier, date_creation)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (nom, tel, vehicule, courses, palier, date_now))
        except sqlite3.IntegrityError:
            pass # Éviter les doublons lors des relancements
            
    conn.commit()
    conn.close()
    print("Base de données peuplée avec succès !")

if __name__ == "__main__":
    populate()
