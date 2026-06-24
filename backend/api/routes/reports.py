from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import uuid
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database.postgres import get_db
from models.case import Case
from models.evidence import Evidence
from models.entity import Entity
from models.event import Event
from models.relationship import Relationship

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get("/{case_id}/summary")
def get_case_summary(case_id: str, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.id == uuid.UUID(case_id)).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    evidence_list = db.query(Evidence).filter(Evidence.case_id == uuid.UUID(case_id)).all()
    entities = db.query(Entity).filter(Entity.case_id == uuid.UUID(case_id)).all()
    events = db.query(Event).filter(Event.case_id == uuid.UUID(case_id)).all()
    relationships = db.query(Relationship).filter(Relationship.case_id == uuid.UUID(case_id)).all()

    evidence_by_type = {}
    for e in evidence_list:
        t = str(e.evidence_type.value if hasattr(e.evidence_type, 'value') else e.evidence_type)
        evidence_by_type[t] = evidence_by_type.get(t, 0) + 1

    event_by_type = {}
    for e in events:
        event_by_type[e.event_type] = event_by_type.get(e.event_type, 0) + 1

    entity_by_type = {}
    for e in entities:
        entity_by_type[e.entity_type] = entity_by_type.get(e.entity_type, 0) + 1

    top_entities = sorted(entities, key=lambda x: x.call_count or 0, reverse=True)[:10]

    top_relationships = sorted(relationships, key=lambda x: x.weight, reverse=True)[:10]

    timeline = sorted(events, key=lambda x: x.timestamp or "")
    first_event = timeline[0].timestamp if timeline else None
    last_event = timeline[-1].timestamp if timeline else None

    return {
        "report_generated_at": datetime.utcnow().isoformat(),
        "case": {
            "id": str(case.id),
            "case_number": case.case_number,
            "title": case.title,
            "description": case.description,
            "status": str(case.status.value if hasattr(case.status, 'value') else case.status),
            "officer_name": case.officer_name,
            "department": case.department,
            "created_at": str(case.created_at)
        },
        "statistics": {
            "total_evidence": len(evidence_list),
            "total_entities": len(entities),
            "total_events": len(events),
            "total_relationships": len(relationships),
            "evidence_by_type": evidence_by_type,
            "events_by_type": event_by_type,
            "entities_by_type": entity_by_type
        },
        "timeline_range": {
            "first_event": first_event,
            "last_event": last_event
        },
        "top_entities": [
            {
                "value": e.value,
                "type": e.entity_type,
                "activity_count": e.call_count,
                "first_seen": e.first_seen,
                "last_seen": e.last_seen,
                "locations": e.locations
            } for e in top_entities
        ],
        "top_relationships": [
            {
                "source": r.source_entity,
                "target": r.target_entity,
                "type": r.relationship_type,
                "strength": r.weight
            } for r in top_relationships
        ],
        "evidence_inventory": [
            {
                "filename": e.original_filename,
                "type": str(e.evidence_type.value if hasattr(e.evidence_type, 'value') else e.evidence_type),
                "status": str(e.status.value if hasattr(e.status, 'value') else e.status),
                "uploaded_at": str(e.uploaded_at),
                "uploaded_by": e.uploaded_by,
                "hash": e.file_hash_sha256
            } for e in evidence_list
        ]
    }

@router.get("/{case_id}/entities")
def get_entity_report(case_id: str, db: Session = Depends(get_db)):
    entities = db.query(Entity).filter(
        Entity.case_id == uuid.UUID(case_id)
    ).order_by(Entity.call_count.desc()).all()

    return {
        "case_id": case_id,
        "total_entities": len(entities),
        "entities": [
            {
                "id": str(e.id),
                "type": e.entity_type,
                "value": e.value,
                "activity_count": e.call_count,
                "first_seen": e.first_seen,
                "last_seen": e.last_seen,
                "imei_list": e.imei_list,
                "imsi_list": e.imsi_list,
                "locations": e.locations
            } for e in entities
        ]
    }

@router.get("/{case_id}/relationships")
def get_relationship_report(case_id: str, db: Session = Depends(get_db)):
    rels = db.query(Relationship).filter(
        Relationship.case_id == uuid.UUID(case_id)
    ).order_by(Relationship.weight.desc()).all()

    return {
        "case_id": case_id,
        "total_relationships": len(rels),
        "relationships": [
            {
                "id": str(r.id),
                "source": r.source_entity,
                "target": r.target_entity,
                "type": r.relationship_type,
                "strength": r.weight,
                "evidence": r.evidence_refs
            } for r in rels
        ]
    }

@router.get("/{case_id}/timeline")
def get_timeline_report(case_id: str, db: Session = Depends(get_db)):
    events = db.query(Event).filter(
        Event.case_id == uuid.UUID(case_id)
    ).all()
    events_sorted = sorted(events, key=lambda x: x.timestamp or "")

    return {
        "case_id": case_id,
        "total_events": len(events_sorted),
        "events": [
            {
                "id": str(e.id),
                "type": e.event_type,
                "timestamp": e.timestamp,
                "source": e.source_entity,
                "target": e.target_entity,
                "direction": e.direction,
                "duration_seconds": e.duration_seconds,
                "location": e.location,
                "cell_id": e.cell_id
            } for e in events_sorted
        ]
    }