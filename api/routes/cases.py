from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid, sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database.postgres import get_db
from models.case import Case

router = APIRouter(prefix="/cases", tags=["Cases"])

@router.get("/")
def get_cases(db: Session = Depends(get_db)):
    cases = db.query(Case).all()
    return cases

@router.get("/{case_id}")
def get_case(case_id: str, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.id == uuid.UUID(case_id)).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case

@router.delete("/{case_id}")
def delete_case(case_id: str, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.id == uuid.UUID(case_id)).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    db.delete(case)
    db.commit()
    return {"message": "Case deleted"}