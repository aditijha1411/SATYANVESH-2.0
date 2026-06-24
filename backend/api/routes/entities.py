from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import sys, os, uuid
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database.postgres import get_db
from models.entity import Entity
from models.event import Event

router = APIRouter(prefix="/entities", tags=["Entities"])

@router.get("/{case_id}")
def get_entities(case_id: str, db: Session = Depends(get_db)):
    entities = db.query(Entity).filter(
        Entity.case_id == uuid.UUID(case_id)
    ).all()
    return [{
        "id": str(e.id),
        "type": e.entity_type,
        "value": e.value,
        "call_count": e.call_count,
        "first_seen": e.first_seen,
        "last_seen": e.last_seen,
        "locations": e.locations or [],
        "imei_list": e.imei_list or [],
        "imsi_list": e.imsi_list or []
    } for e in entities]

@router.get("/{case_id}/{entity_value}/timeline")
def get_entity_timeline(case_id: str, entity_value: str, db: Session = Depends(get_db)):
    events = db.query(Event).filter(
        Event.case_id == uuid.UUID(case_id),
        Event.source_entity == entity_value
    ).order_by(Event.timestamp).all()
    return [{
        "id": str(e.id),
        "event_type": e.event_type,
        "timestamp": str(e.timestamp) if e.timestamp else "",
        "target": e.target_entity,
        "direction": e.direction,
        "duration": e.duration_seconds,
        "location": e.location,
        "cell_id": e.cell_id
    } for e in events]

@router.delete("/{case_id}/{entity_id}")
def delete_entity(case_id: str, entity_id: str, db: Session = Depends(get_db)):
    entity = db.query(Entity).filter(
        Entity.id == uuid.UUID(entity_id),
        Entity.case_id == uuid.UUID(case_id)
    ).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    db.delete(entity)
    db.commit()
    return {"message": "Entity deleted"}