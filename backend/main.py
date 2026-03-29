from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
import uvicorn
from datetime import datetime
import os

app = FastAPI(title="Taxi Na Biso CRM API")

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Configuration Base de Données (Production vs Local) ---
# Si DATABASE_URL est présent (Render Postgres), on l'utilise
# Pour l'instant on garde sqlite3 pour la simplicité, mais on prépare la structure
# TODO: Passer à SQLAlchemy pour un vrai support multi-dialecte Postgres
DB_NAME = os.environ.get("DATABASE_URL", "crm_taxi_na_biso.db")
IS_POSTGRES = DB_NAME.startswith("postgres")

def get_db_connection():
    if IS_POSTGRES:
        import psycopg2
        # On injecte sslmode=require pour Render
        url = DB_NAME
        if "sslmode" not in url:
            url += "?sslmode=require" if "?" in url else "?sslmode=require"
        conn = psycopg2.connect(url)
    else:
        conn = sqlite3.connect(DB_NAME)
    return conn

# --- Modèles Pydantic ---

class Course(BaseModel):
    distance: float
    prix: int
    date: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

class ClientBase(BaseModel):
    nom: str
    telephone: str
    vehicule_prefere: str = "Basic (Toyota Aygo)"
    notes: Optional[str] = None

class ClientCreate(ClientBase):
    pass

class Client(ClientBase):
    id: int
    palier: str
    total_courses: int
    date_creation: str

# --- Initialisation de la Base de Données ---

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Syntaxe compatible SQLite/Postgres pour la création de table
    # Attention: SQLite utilise AUTOINCREMENT, Postgres utilise SERIAL ou IDENTITY
    id_type = "SERIAL" if IS_POSTGRES else "INTEGER PRIMARY KEY AUTOINCREMENT"
    
    create_table_query = f'''
        CREATE TABLE IF NOT EXISTS clients (
            id {id_type if not IS_POSTGRES else "SERIAL PRIMARY KEY"},
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
    conn.close()

init_db()

# --- Fonctions Utilitaires ---

def get_palier(total_courses: int) -> str:
    """Détermine le palier de fidélité."""
    if total_courses == 0: return "Nouveau"
    elif 1 <= total_courses <= 5: return "Bronze"
    elif 6 <= total_courses <= 15: return "Argent"
    elif 16 <= total_courses <= 30: return "Or"
    else: return "VIP"

# --- Endpoints API ---

@app.get("/api/stats")
def get_stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM clients")
    total_clients = cursor.fetchone()[0]
    
    paliers_stats = {"Nouveau": 0, "Bronze": 0, "Argent": 0, "Or": 0, "VIP": 0}
    cursor.execute("SELECT palier, COUNT(*) FROM clients GROUP BY palier")
    for row in cursor.fetchall():
        if row[0] in paliers_stats:
            paliers_stats[row[0]] = row[1]
            
    # Calculer le nombre de courses total (somme de total_courses des clients)
    cursor.execute("SELECT SUM(total_courses) FROM clients")
    total_courses = cursor.fetchone()[0] or 0
    
    conn.close()
    
    return {
        "total_clients": total_clients,
        "courses_ce_mois": total_courses, # Utiliser le total pour la démo
        "total_courses": total_courses,
        "recompenses": total_clients // 2, # Simulation
        "repartition_paliers": paliers_stats
    }

@app.get("/api/clients", response_model=List[Client])
def get_clients(search: Optional[str] = None, palier: Optional[str] = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT id, nom, telephone, vehicule_prefere, notes, palier, total_courses, date_creation FROM clients WHERE 1=1"
    params = []
    
    if search:
        # Postgres utilise ILIKE pour le cas insensible, SQLite utilise LIKE par défaut
        like_op = "ILIKE" if IS_POSTGRES else "LIKE"
        query += f" AND (nom {like_op} ? OR telephone {like_op} ?)"
        params.extend([f"%{search}%", f"%{search}%"])
        
    if palier and palier != "Tous":
        query += " AND palier = ?"
        params.append(palier)
    
    # Conversion du format de paramètres pour Postgres ($1, $2) vs SQLite (?)
    if IS_POSTGRES:
        for i in range(len(params)):
            query = query.replace("?", f"${i+1}", 1)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    return [
        {
            "id": r[0], "nom": r[1], "telephone": r[2], 
            "vehicule_prefere": r[3], "notes": r[4], 
            "palier": r[5], "total_courses": r[6], "date_creation": r[7]
        } for r in rows
    ]

@app.post("/api/clients", response_model=Client)
def create_client(client: ClientCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    date_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    initial_palier = "Nouveau"
    
    try:
        # Syntaxe de paramètres
        param_char = "$" if IS_POSTGRES else "?"
        p = [param_char] * 7
        if IS_POSTGRES: p = [f"${i+1}" for i in range(7)]
        
        insert_query = f'''
            INSERT INTO clients (nom, telephone, vehicule_prefere, notes, palier, total_courses, date_creation)
            VALUES ({", ".join(p)})
        '''
        
        if IS_POSTGRES:
            insert_query += " RETURNING id"
            cursor.execute(insert_query, (client.nom, client.telephone, client.vehicule_prefere, client.notes, initial_palier, 0, date_now))
            new_id = cursor.fetchone()[0]
        else:
            cursor.execute(insert_query, (client.nom, client.telephone, client.vehicule_prefere, client.notes, initial_palier, 0, date_now))
            new_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        return {
            "id": new_id, **client.model_dump(), 
            "palier": initial_palier, "total_courses": 0, "date_creation": date_now
        }
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/clients/{client_id}/add_course")
def add_course(client_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Obtenir le nombre de courses actuel
    param_char = "$1" if IS_POSTGRES else "?"
    cursor.execute(f"SELECT total_courses FROM clients WHERE id = {param_char}", (client_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Client non trouvé.")
        
    nb_courses = row[0] + 1
    nouveau_palier = get_palier(nb_courses)
    
    # 2. Mettre à jour le client
    p1, p2, p3 = ("$1", "$2", "$3") if IS_POSTGRES else ("?", "?", "?")
    cursor.execute(f'''
        UPDATE clients SET total_courses = {p1}, palier = {p2} WHERE id = {p3}
    ''', (nb_courses, nouveau_palier, client_id))
    
    conn.commit()
    conn.close()
    return {"message": "Course ajoutée", "nouveau_palier": nouveau_palier, "total_courses": nb_courses}

# --- Gestion du Frontend (All-in-one) ---

# Chemin vers les fichiers statiques de React (après build)
# On cherche soit à côté soit un cran au dessus selon l'environnement
base_dir = os.path.dirname(__file__)
dist_path = os.path.join(base_dir, "..", "frontend", "dist")

if os.path.exists(dist_path):
    app.mount("/", StaticFiles(directory=dist_path, html=True), name="static")

    @app.exception_handler(404)
    async def not_found_exception_handler(request, exc):
        # Pour React Router, on redirige tout vers index.html sauf /api
        if not request.url.path.startswith("/api"):
            return FileResponse(os.path.join(dist_path, "index.html"))
        return JSONResponse(status_code=404, content={"detail": "Not found"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
