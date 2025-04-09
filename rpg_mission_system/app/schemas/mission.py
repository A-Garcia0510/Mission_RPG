from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# Mission base schema with common attributes
class MissionBase(BaseModel):
    title: str
    description: str
    xp_reward: int
    difficulty: int

# Schema for creating a mission
class MissionCreate(MissionBase):
    pass

# Schema for mission in database (includes ID)
class Mission(MissionBase):
    id: int
    
    class Config:
        orm_mode = True

# Schema for character mission relationship
class CharacterMissionBase(BaseModel):
    mission_id: int
    status: str
    queue_position: int

# Schema for character mission relationship in database
class CharacterMission(CharacterMissionBase):
    id: int
    character_id: int
    accepted_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True

# Schema for character's mission queue
class MissionQueueItem(BaseModel):
    id: int
    title: str
    description: str
    xp_reward: int
    difficulty: int
    status: str
    queue_position: int
    accepted_at: datetime
    
    class Config:
        orm_mode = True