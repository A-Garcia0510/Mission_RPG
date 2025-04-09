# app/routers/__init__.py
from app.routers.characters import router as characters_router
from app.routers.missions import router as missions_router

# Reasignar nombres para mayor claridad
personajes_router = characters_router
misiones_router = missions_router