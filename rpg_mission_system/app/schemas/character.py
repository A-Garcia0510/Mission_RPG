from pydantic import BaseModel
from typing import List, Optional

# Character base schema with common attributes
class CharacterBase(BaseModel):
    name: str
    level: int = 1
    experience: int = 0

# Schema for creating a character
class CharacterCreate(CharacterBase):
    pass

# Schema for character in database (includes ID)
class Character(CharacterBase):
    id: int
    
    class Config:
        orm_mode = True

# Schema for detailed character info including missions
class CharacterDetail(Character):
    mission_count: int = 0
    pending_missions: int = 0
    
    class Config:
        orm_mode = True