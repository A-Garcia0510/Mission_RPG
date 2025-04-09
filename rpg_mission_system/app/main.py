from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import characters, missions

# Create database tables
Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title="Sistema de Misiones RPG",  # Título en español
    description="Sistema para gestionar misiones en juegos RPG usando una estructura de datos Cola (FIFO)",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development - restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(characters.router)
app.include_router(missions.router)

@app.get("/")
def read_root():
    return {
        "message": "Bienvenido al Sistema de Misiones RPG",
        "docs": "/docs"
    }