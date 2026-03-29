from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles # Nouveau
from fastapi.responses import FileResponse # Nouveau
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
import uvicorn
from datetime import datetime
import os

app = FastAPI(title="Taxi Na Biso CRM API")

# Configuration CORS pour permettre au frontend React de communiquer
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_NAME = "crm_taxi_na_biso.db"

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
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Création de la table clients avec tous les champs nécessaires pour le dashboard
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
    conn.close()

init_db()

# --- Fonctions Utilitaires ---

def get_palier(total_courses: int) -> str:
    """Détermine le palier de fidélité en fonction du nombre de courses."""
    if total_courses == 0:
        return "Nouveau"
    elif 1 <= total_courses <= 5:
        return "Bronze"
    elif 6 <= total_courses <= 15:
        return "Argent"
    elif 16 <= total_courses <= 30:
        return "Or"
    else:
        return "VIP"

# --- Endpoints API ---

@app.get("/api/stats")
def get_stats():
    """Récupère les statistiques globales pour le tableau de bord."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Total clients
    cursor.execute("SELECT COUNT(*) FROM clients")
    total_clients = cursor.fetchone()[0]
    
    # Répartition par palier
    paliers_stats = {
        "Nouveau": 0, "Bronze": 0, "Argent": 0, "Or": 0, "VIP": 0
    }
    cursor.execute("SELECT palier, COUNT(*) FROM clients GROUP BY palier")
    for row in cursor.fetchall():
        if row[0] in paliers_stats:
            paliers_stats[row[0]] = row[1]
            
    # On simule d'autres stats pour l'interface (courses ce mois, etc.)
    # Dans une version future, on calculera ça depuis une table 'courses'
    conn.close()
    
    return {
        "total_clients": total_clients,
        "courses_ce_mois": 0, # TODO: Implémenter table courses
        "total_courses": 0,
        "recompenses": 0,
        "repartition_paliers": paliers_stats
    }

@app.get("/api/clients", response_model=List[Client])
def get_clients(search: Optional[str] = None, palier: Optional[str] = None):
    """Liste tous les clients avec option de filtre."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    query = "SELECT * FROM clients WHERE 1=1"
    params = []
    
    if search:
        query += " AND (nom LIKE ? OR telephone LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])
        
    if palier and palier != "Tous":
        query += " AND palier = ?"
        params.append(palier)
        
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
    """Crée un nouveau client."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    date_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    initial_palier = "Nouveau"
    
    try:
        cursor.execute('''
            INSERT INTO clients (nom, telephone, vehicule_prefere, notes, palier, total_courses, date_creation)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (client.nom, client.telephone, client.vehicule_prefere, client.notes, initial_palier, 0, date_now))
        
        new_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return {
            "id": new_id, **client.model_dump(), 
            "palier": initial_palier, "total_courses": 0, "date_creation": date_now
        }
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Ce numéro de téléphone est déjà enregistré.")

@app.post("/api/clients/{client_id}/add_course")
def add_course(client_id: int):
    """Enregistre une course et met à jour le palier du client."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 1. Obtenir le nombre de courses actuel
    cursor.execute("SELECT total_courses FROM clients WHERE id = ?", (client_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Client non trouvé.")
        
    nb_courses = row[0] + 1
    nouveau_palier = get_palier(nb_courses)
    
    # 2. Mettre à jour le client
    cursor.execute('''
        UPDATE clients SET total_courses = ?, palier = ? WHERE id = ?
    ''', (nb_courses, nouveau_palier, client_id))
    
    conn.commit()
    conn.close()
    return {"message": "Course ajoutée", "nouveau_palier": nouveau_palier, "total_courses": nb_courses}

# --- Gestion du Frontend (All-in-one) ---

# Vérifier si le dossier dist existe (après npm run build)
dist_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")

if os.path.exists(dist_path):
    app.mount("/", StaticFiles(directory=dist_path, html=True), name="static")

    @app.exception_handler(404)
    async def not_found_exception_handler(request, exc):
        """Redirige toutes les routes non-API vers index.html pour React Router."""
        if not request.url.path.startswith("/api"):
            return FileResponse(os.path.join(dist_path, "index.html"))
        return JSONResponse(status_code=404, content={"detail": "Not found"})

if __name__ == "__main__":
    # Récupérer le port Render ou utiliser 8000 par défaut
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
