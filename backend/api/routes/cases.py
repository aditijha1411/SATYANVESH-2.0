from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database.postgres import get_db
from models.case import Case, CaseStatus

router = APIRouter(prefix="/cases", tags=["Cases"])

class CaseCreate(BaseModel):
    case_number: str
    title: str
    description: Optional[str] = None
    officer_name: Optional[str] = None
    officer_badge: Optional[str] = None
    department: Optional[str] = None

class CaseResponse(BaseModel):
    id: str
    case_number: str
    title: str
    description: Optional[str]
    status: str
    officer_name: Optional[str]
    officer_badge: Optional[str]
    department: Optional[str]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True

@router.post("/", response_model=CaseResponse)
def create_case(case: CaseCreate, db: Session = Depends(get_db)):
    existing = db.query(Case).filter(Case.case_number == case.case_number).first()
    if existing:
        raise HTTPException(status_code=400, detail="Case number already exists")
    new_case = Case(
        id=uuid.uuid4(),
        case_number=case.case_number,
        title=case.title,
        description=case.description,
        officer_name=case.officer_name,
        officer_badge=case.officer_badge,
        department=case.department,
        status=CaseStatus.OPEN
    )
    db.add(new_case)
    db.commit()
    db.refresh(new_case)
    new_case.id = str(new_case.id)
    return new_case

@router.get("/", response_model=list[CaseResponse])
def get_all_cases(db: Session = Depends(get_db)):
    cases = db.query(Case).all()
    for c in cases:
        c.id = str(c.id)
    return cases

@router.get("/{case_id}", response_model=CaseResponse)
def get_case(case_id: str, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.id == uuid.UUID(case_id)).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    case.id = str(case.id)
    return case

@router.patch("/{case_id}/status")
def update_case_status(case_id: str, status: str, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.id == uuid.UUID(case_id)).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    case.status = status
    if status == "closed":
        case.closed_at = datetime.utcnow()
    db.commit()
    return {"message": f"Case status updated to {status}"}

@router.delete("/{case_id}")
def delete_case(case_id: str, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.id == uuid.UUID(case_id)).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    db.delete(case)
    db.commit()
    return {"message": "Case deleted"}