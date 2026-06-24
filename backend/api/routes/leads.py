from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database.postgres import get_db

router = APIRouter(prefix="/ai", tags=["AI Engine"])

@router.post("/analyze/{case_id}")
def run_ai_analysis(case_id: str, db: Session = Depends(get_db)):
    from services.ai.ai_engine import AIEngine
    engine = AIEngine(db=db, case_id=case_id)
    return engine.run_full_analysis()

@router.post("/leads/{case_id}")
def get_leads_only(case_id: str, db: Session = Depends(get_db)):
    from services.ai.lead_generator import LeadGenerator
    gen = LeadGenerator(db=db, case_id=case_id)
    return {"leads": gen.generate()}

@router.post("/patterns/{case_id}")
def get_patterns_only(case_id: str, db: Session = Depends(get_db)):
    from services.ai.pattern_detector import PatternDetector
    detector = PatternDetector(db=db, case_id=case_id)
    return {"patterns": detector.detect()}