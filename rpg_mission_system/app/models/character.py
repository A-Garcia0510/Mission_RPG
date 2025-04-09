from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base

class Character(Base):
    __tablename__ = "characters"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    level = Column(Integer, default=1)
    experience = Column(Integer, default=0)
    
    # Relationship with missions through character_missions table
    missions = relationship("CharacterMission", back_populates="character")
    
    def __repr__(self):
        return f"Character(id={self.id}, name='{self.name}', level={self.level})"