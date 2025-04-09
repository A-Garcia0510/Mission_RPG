from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.character_mission import CharacterMission

class MissionQueue:    
    def __init__(self, db: Session, character_id: int):
        """Inicializa la cola de misiones para un personaje específico"""
        self.db = db
        self.character_id = character_id
    
    def is_empty(self) -> bool:
        """Verifica si la cola de misiones está vacía"""
        return self.size() == 0
    
    def size(self) -> int:
        """Devuelve el número de misiones en la cola"""
        return self.db.query(CharacterMission).filter(
            CharacterMission.character_id == self.character_id,
            CharacterMission.status.in_(["pending", "in_progress"])
        ).count()
    
    def enqueue(self, mission_id: int) -> CharacterMission:
        """Agrega una misión al final de la cola"""
        # Obtener la siguiente posición en la cola
        max_position = self.db.query(func.max(CharacterMission.queue_position)).filter(
            CharacterMission.character_id == self.character_id
        ).scalar() or 0
        
        # Crear una nueva misión de personaje con la siguiente posición
        character_mission = CharacterMission(
            character_id=self.character_id,
            mission_id=mission_id,
            queue_position=max_position + 1,
            status="pending"
        )
        
        self.db.add(character_mission)
        self.db.commit()
        self.db.refresh(character_mission)
        
        return character_mission
    
    def dequeue(self) -> CharacterMission:
        """Elimina y devuelve la misión al frente de la cola (marcar como completada)"""
        # Obtener la misión con la posición más baja en la cola que no esté completada
        mission = self.first()
        
        if mission:
            # Marcar como completada
            mission.status = "completed"
            mission.completed_at = func.now()
            self.db.commit()
            self.db.refresh(mission)
        
        return mission
    
    def first(self) -> CharacterMission:
        """Devuelve la misión al frente de la cola sin eliminarla"""
        return self.db.query(CharacterMission).filter(
            CharacterMission.character_id == self.character_id,
            CharacterMission.status.in_(["pending", "in_progress"])
        ).order_by(CharacterMission.queue_position).first()
    
    def get_all(self):
        """Devuelve todas las misiones en la cola en orden"""
        return self.db.query(CharacterMission).filter(
            CharacterMission.character_id == self.character_id
        ).order_by(CharacterMission.queue_position).all()
    
    def start_next_mission(self) -> CharacterMission:
        """Inicia la siguiente misión pendiente (primera en la cola)"""
        # Obtener la primera misión pendiente
        mission = self.db.query(CharacterMission).filter(
            CharacterMission.character_id == self.character_id,
            CharacterMission.status == "pending"
        ).order_by(CharacterMission.queue_position).first()
        
        if mission:
            mission.status = "in_progress"
            self.db.commit()
            self.db.refresh(mission)
        
        return mission