from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.character import Character
from app.models.character_mission import CharacterMission
from app.models.mission import Mission
from app.schemas.character import Character as CharacterSchema
from app.schemas.character import CharacterCreate, CharacterDetail
from app.schemas.mission import MissionQueueItem, CharacterMission as CharacterMissionSchema
from app.tda.queue import MissionQueue

router = APIRouter(
    prefix="/personajes",  # Cambiado a español según el PDF
    tags=["characters"]
)

@router.post("/", response_model=CharacterSchema)
def create_character(character: CharacterCreate, db: Session = Depends(get_db)):
    """Create a new character"""
    db_character = Character(**character.dict())
    db.add(db_character)
    db.commit()
    db.refresh(db_character)
    return db_character

@router.get("/", response_model=List[CharacterSchema])
def get_characters(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get a list of characters"""
    characters = db.query(Character).offset(skip).limit(limit).all()
    return characters

@router.get("/{character_id}", response_model=CharacterDetail)
def get_character(character_id: int, db: Session = Depends(get_db)):
    """Get a character by ID with mission stats"""
    character = db.query(Character).filter(Character.id == character_id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    # Get mission counts for the character details
    pending_missions = db.query(CharacterMission).filter(
        CharacterMission.character_id == character_id,
        CharacterMission.status.in_(["pending", "in_progress"])
    ).count()
    
    mission_count = db.query(CharacterMission).filter(
        CharacterMission.character_id == character_id
    ).count()
    
    # Crear manualmente el objeto de respuesta para asegurar que todos los campos estén presentes
    response = {
        "id": character.id,
        "name": character.name,
        "level": character.level,
        "experience": character.experience,
        "mission_count": mission_count,
        "pending_missions": pending_missions
    }
    
    return response

@router.get("/{character_id}/misiones", response_model=List[MissionQueueItem])
def get_character_missions(character_id: int, db: Session = Depends(get_db)):
    """Get all missions for a character in queue order"""
    character = db.query(Character).filter(Character.id == character_id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    # Get all missions with join to get mission details
    missions = db.query(
        CharacterMission.id,
        CharacterMission.status,
        CharacterMission.queue_position,
        CharacterMission.accepted_at,
        Character.id.label("character_id"),
        Character.name.label("character_name"),
        Mission.id.label("mission_id"),
        Mission.title,
        Mission.description,
        Mission.xp_reward,
        Mission.difficulty
    ).join(
        Mission, CharacterMission.mission_id == Mission.id
    ).join(
        Character, CharacterMission.character_id == Character.id
    ).filter(
        CharacterMission.character_id == character_id
    ).order_by(CharacterMission.queue_position.asc()).all()
    
    return missions

@router.post("/{character_id}/misiones/{mission_id}", response_model=CharacterMissionSchema)
def accept_mission(character_id: int, mission_id: int, db: Session = Depends(get_db)):
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

@router.post("/{character_id}/completar", response_model=CharacterMissionSchema)
def complete_current_mission(character_id: int, db: Session = Depends(get_db)):
    """Complete the current mission in the queue and award XP"""
    # Check if character exists
    character = db.query(Character).filter(Character.id == character_id).first()
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    # Use the queue to get the next mission
    mission_queue = MissionQueue(db, character_id)
    current_mission = mission_queue.first()
    
    if not current_mission:
        raise HTTPException(status_code=404, detail="No missions in queue")
    
    if current_mission.status != "in_progress":
        # Start the mission first if it's not already in progress
        current_mission.status = "in_progress"
        db.commit()
    
    # Complete the mission
    completed_mission = mission_queue.dequeue()
    
    # Award XP to character
    mission = db.query(Mission).filter(Mission.id == completed_mission.mission_id).first()
    character.experience += mission.xp_reward
    
    # Level up if enough XP (simple leveling system)
    xp_for_next_level = character.level * 100
    if character.experience >= xp_for_next_level:
        character.level += 1
    
    db.commit()
    
    return completed_mission