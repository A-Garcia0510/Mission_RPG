from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base

class Mission(Base):
    __tablename__ = "missions"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text)
    xp_reward = Column(Integer)
    difficulty = Column(Integer)  # 1-5 scale
    
    # Relationship with characters through character_missions table
    characters = relationship("CharacterMission", back_populates="mission")
    
    def __repr__(self):
        return f"Mission(id={self.id}, title='{self.title}', difficulty={self.difficulty})"