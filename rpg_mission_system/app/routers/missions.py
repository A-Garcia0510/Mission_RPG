from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.mission import Mission
from app.models.character import Character
from app.models.character_mission import CharacterMission
from app.schemas.mission import Mission as MissionSchema
from app.schemas.mission import MissionCreate, CharacterMission as CharacterMissionSchema
from app.tda.queue import MissionQueue

router = APIRouter(
    prefix="/misiones",  # Cambiado a español según el PDF
    tags=["missions"]
)

@router.post("/", response_model=MissionSchema)
def create_mission(mission: MissionCreate, db: Session = Depends(get_db)):
    """Create a new mission"""
    db_mission = Mission(**mission.dict())
    db.add(db_mission)
    db.commit()
    db.refresh(db_mission)
    return db_mission

@router.get("/", response_model=List[MissionSchema])
def get_missions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get a list of missions"""
    missions = db.query(Mission).offset(skip).limit(limit).all()
    return missions

@router.get("/{mission_id}", response_model=MissionSchema)
def get_mission(mission_id: int, db: Session = Depends(get_db)):
    """Get a mission by ID"""
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    return mission

# Mantener los endpoints adicionales para compatibilidad
@router.post("/{mission_id}/accept", response_model=CharacterMissionSchema)
def accept_mission(mission_id: int, character_id: int, db: Session = Depends(get_db)):
    """Accept a mission for a character (add to queue)"""
    # Check if mission exists
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    
    # Check if character exists
    character = db.query(Character).filter(Character.id == character_id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    # Check if mission is already accepted by this character
    existing = db.query(CharacterMission).filter(
        CharacterMission.character_id == character_id,
        CharacterMission.mission_id == mission_id,
        CharacterMission.status.in_(["pending", "in_progress"])
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Mission already accepted")
    
    # Use the queue to add the mission
    mission_queue = MissionQueue(db, character_id)
    character_mission = mission_queue.enqueue(mission_id)
    
    return character_mission

@router.post("/{mission_id}/start", response_model=CharacterMissionSchema)
def start_mission(mission_id: int, character_id: int, db: Session = Depends(get_db)):
    """Start the next mission in the queue"""
    # Check if character exists
    character = db.query(Character).filter(Character.id == character_id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    # Use the queue to get the next mission
    mission_queue = MissionQueue(db, character_id)
    next_mission = mission_queue.first()
    
    if not next_mission:
        raise HTTPException(status_code=404, detail="No missions in queue")
    
    if next_mission.mission_id != mission_id:
        raise HTTPException(status_code=400, 
                           detail=f"This mission is not the next in queue. Next mission ID: {next_mission.mission_id}")
    
    # Start the mission
    next_mission.status = "in_progress"
    db.commit()
    db.refresh(next_mission)
    
    return next_mission

@router.post("/{mission_id}/complete", response_model=CharacterMissionSchema)
def complete_mission(mission_id: int, character_id: int, db: Session = Depends(get_db)):
    """Complete the current mission and award XP"""
    # Check if character exists
    character = db.query(Character).filter(Character.id == character_id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    # Check if the mission is in progress
    mission_entry = db.query(CharacterMission).filter(
        CharacterMission.character_id == character_id,
        CharacterMission.mission_id == mission_id,
        CharacterMission.status == "in_progress"
    ).first()
    
    if not mission_entry:
        raise HTTPException(status_code=400, detail="Mission not in progress")
    
    # Use the queue to dequeue (complete) the mission
    mission_queue = MissionQueue(db, character_id)
    completed_mission = mission_queue.dequeue()
    
    # Award XP to character
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    character.experience += mission.xp_reward
    
    # Level up if enough XP (simple leveling system)
    xp_for_next_level = character.level * 100
    if character.experience >= xp_for_next_level:
        character.level += 1
    
    db.commit()
    
    return completed_mission