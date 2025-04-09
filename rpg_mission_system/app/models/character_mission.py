from sqlalchemy import Column, Integer, ForeignKey, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base

class CharacterMission(Base):
    __tablename__ = "character_missions"
    
    id = Column(Integer, primary_key=True, index=True)
    character_id = Column(Integer, ForeignKey("characters.id"))
    mission_id = Column(Integer, ForeignKey("missions.id"))
    
    # Queue position/ordering - used for FIFO queue implementation
    queue_position = Column(Integer, nullable=False)
    
    # Status: "pending", "in_progress", "completed"
    status = Column(String, default="pending")
    
    # Timestamps
    accepted_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    character = relationship("Character", back_populates="missions")
    mission = relationship("Mission", back_populates="characters")
    
    def __repr__(self):
        return f"CharacterMission(character_id={self.character_id}, mission_id={self.mission_id}, status='{self.status}')"