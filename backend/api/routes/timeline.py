from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database.postgres import get_db

router = APIRouter(prefix="/timeline", tags=["Timeline"])

@router.get("/{case_id}")
def get_full_timeline(case_id: str, db: Session = Depends(get_db)):
    from services.timeline.timeline_engine import TimelineEngine
    engine = TimelineEngine(db=db, case_id=case_id)
    return engine.get_full_timeline()

@router.get("/{case_id}/entity/{entity_value}")
def get_entity_timeline(case_id: str, entity_value: str, db: Session = Depends(get_db)):
    from services.timeline.timeline_engine import TimelineEngine
    engine = TimelineEngine(db=db, case_id=case_id)
    return engine.get_entity_timeline(entity_value)

@router.get("/{case_id}/patterns")
def get_suspicious_patterns(case_id: str, db: Session = Depends(get_db)):
    from services.timeline.timeline_engine import TimelineEngine
    engine = TimelineEngine(db=db, case_id=case_id)
    return engine.detect_suspicious_patterns()

@router.get("/{case_id}/range")
def get_timeline_range(case_id: str, start: str, end: str, db: Session = Depends(get_db)):
    from services.timeline.timeline_engine import TimelineEngine
    engine = TimelineEngine(db=db, case_id=case_id)
    return engine.get_timeline_between(start, end)