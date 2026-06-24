from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import sys, os, uuid
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database.postgres import get_db
from models.event import Event

router = APIRouter(prefix="/events", tags=["Events"])

@router.get("/{case_id}")
def get_events(case_id: str, db: Session = Depends(get_db)):
    events = db.query(Event).filter(
        Event.case_id == uuid.UUID(case_id)
    ).order_by(Event.timestamp).all()
    return [{
        "id": str(e.id),
        "event_type": e.event_type,
        "timestamp": str(e.timestamp) if e.timestamp else "",
        "source": e.source_entity,
        "target": e.target_entity,
        "direction": e.direction,
        "duration": e.duration_seconds,
        "location": e.location,
        "cell_id": e.cell_id,
        "imei": e.imei
    } for e in events]

@router.get("/{case_id}/entity/{entity_value}")
def get_events_by_entity(case_id: str, entity_value: str, db: Session = Depends(get_db)):
    events = db.query(Event).filter(
        Event.case_id == uuid.UUID(case_id),
        Event.source_entity == entity_value
    ).order_by(Event.timestamp).all()
    return [{
        "id": str(e.id),
        "event_type": e.event_type,
        "timestamp": str(e.timestamp) if e.timestamp else "",
        "source": e.source_entity,
        "target": e.target_entity,
        "location": e.location,
        "duration": e.duration_seconds
    } for e in events]