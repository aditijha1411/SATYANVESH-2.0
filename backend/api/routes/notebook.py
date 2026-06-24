from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database.postgres import get_db
from models.notebook import NotebookEntry

router = APIRouter(prefix="/notebook", tags=["Notebook"])

class NotebookEntryCreate(BaseModel):
    entry_type: str
    title: str
    content: Optional[str] = None
    entities_linked: Optional[List[str]] = []
    evidence_linked: Optional[List[str]] = []
    created_by: Optional[str] = "investigator"

class NotebookEntryUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    status: Optional[str] = None
    confidence: Optional[int] = None
    is_pinned: Optional[bool] = None

@router.post("/{case_id}/entry")
def create_entry(case_id: str, entry: NotebookEntryCreate, db: Session = Depends(get_db)):
    new_entry = NotebookEntry(
        id=uuid.uuid4(),
        case_id=uuid.UUID(case_id),
        entry_type=entry.entry_type,
        title=entry.title,
        content=entry.content,
        entities_linked=entry.entities_linked or [],
        evidence_linked=entry.evidence_linked or [],
        created_by=entry.created_by
    )
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)
    return {
        "id": str(new_entry.id),
        "case_id": case_id,
        "entry_type": new_entry.entry_type,
        "title": new_entry.title,
        "status": new_entry.status,
        "created_at": str(new_entry.created_at)
    }

@router.get("/{case_id}/entries")
def get_entries(case_id: str, entry_type: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(NotebookEntry).filter(NotebookEntry.case_id == uuid.UUID(case_id))
    if entry_type:
        query = query.filter(NotebookEntry.entry_type == entry_type)
    entries = query.order_by(NotebookEntry.is_pinned.desc(), NotebookEntry.created_at.desc()).all()
    
    return [
        {
            "id": str(e.id),
            "entry_type": e.entry_type,
            "title": e.title,
            "content": e.content,
            "status": e.status,
            "confidence": e.confidence,
            "entities_linked": e.entities_linked,
            "evidence_linked": e.evidence_linked,
            "is_pinned": e.is_pinned,
            "created_at": str(e.created_at),
            "created_by": e.created_by
        } for e in entries
    ]

@router.get("/{case_id}/entry/{entry_id}")
def get_entry(case_id: str, entry_id: str, db: Session = Depends(get_db)):
    entry = db.query(NotebookEntry).filter(
        NotebookEntry.case_id == uuid.UUID(case_id),
        NotebookEntry.id == uuid.UUID(entry_id)
    ).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    return {
        "id": str(entry.id),
        "entry_type": entry.entry_type,
        "title": entry.title,
        "content": entry.content,
        "status": entry.status,
        "confidence": entry.confidence,
        "entities_linked": entry.entities_linked,
        "evidence_linked": entry.evidence_linked,
        "graph_nodes_linked": entry.graph_nodes_linked,
        "is_pinned": entry.is_pinned,
        "created_at": str(entry.created_at),
        "updated_at": str(entry.updated_at),
        "created_by": entry.created_by
    }

@router.patch("/{case_id}/entry/{entry_id}")
def update_entry(case_id: str, entry_id: str, update: NotebookEntryUpdate, db: Session = Depends(get_db)):
    entry = db.query(NotebookEntry).filter(
        NotebookEntry.case_id == uuid.UUID(case_id),
        NotebookEntry.id == uuid.UUID(entry_id)
    ).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    if update.title:
        entry.title = update.title
    if update.content:
        entry.content = update.content
    if update.status:
        entry.status = update.status
    if update.confidence is not None:
        entry.confidence = update.confidence
    if update.is_pinned is not None:
        entry.is_pinned = update.is_pinned

    entry.updated_at = datetime.utcnow()
    db.commit()
    return {"message": "Entry updated", "entry_id": entry_id}

@router.delete("/{case_id}/entry/{entry_id}")
def delete_entry(case_id: str, entry_id: str, db: Session = Depends(get_db)):
    entry = db.query(NotebookEntry).filter(
        NotebookEntry.case_id == uuid.UUID(case_id),
        NotebookEntry.id == uuid.UUID(entry_id)
    ).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    db.delete(entry)
    db.commit()
    return {"message": "Entry deleted"}

@router.post("/{case_id}/entry/{entry_id}/pin")
def pin_entry(case_id: str, entry_id: str, db: Session = Depends(get_db)):
    entry = db.query(NotebookEntry).filter(
        NotebookEntry.case_id == uuid.UUID(case_id),
        NotebookEntry.id == uuid.UUID(entry_id)
    ).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    entry.is_pinned = True
    db.commit()
    return {"message": "Entry pinned"}

@router.post("/{case_id}/entry/{entry_id}/unpin")
def unpin_entry(case_id: str, entry_id: str, db: Session = Depends(get_db)):
    entry = db.query(NotebookEntry).filter(
        NotebookEntry.case_id == uuid.UUID(case_id),
        NotebookEntry.id == uuid.UUID(entry_id)
    ).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    entry.is_pinned = False
    db.commit()
    return {"message": "Entry unpinned"}

@router.get("/{case_id}/pinned")
def get_pinned_entries(case_id: str, db: Session = Depends(get_db)):
    entries = db.query(NotebookEntry).filter(
        NotebookEntry.case_id == uuid.UUID(case_id),
        NotebookEntry.is_pinned == True
    ).all()
    
    return [
        {
            "id": str(e.id),
            "entry_type": e.entry_type,
            "title": e.title,
            "content": e.content[:100] if e.content else None,
            "status": e.status
        } for e in entries
    ]