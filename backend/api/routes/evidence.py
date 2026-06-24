from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from datetime import datetime
import uuid
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database.postgres import get_db
from models.evidence import Evidence, EvidenceType, EvidenceStatus
from models.entity import Entity
from models.event import Event
from models.case import Case
from utils.file_utils import (
    is_allowed_file, compute_sha256,
    detect_evidence_type, save_uploaded_file
)

router = APIRouter(prefix="/evidence", tags=["Evidence"])

UPLOAD_BASE = "data/evidence_store"

@router.post("/upload")
async def upload_evidence(
    case_id: str = Form(...),
    source_description: str = Form(""),
    uploaded_by: str = Form("investigator"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    case = db.query(Case).filter(Case.id == uuid.UUID(case_id)).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    if not is_allowed_file(file.filename):
        raise HTTPException(status_code=400, detail=f"File type not allowed: {file.filename}")

    file_content = await file.read()
    file_size = len(file_content)

    if file_size > 500 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large. Max 500MB.")

    evidence_id = uuid.uuid4()
    ext = os.path.splitext(file.filename)[1].lower()
    stored_filename = f"{evidence_id}{ext}"
    file_path = os.path.join(UPLOAD_BASE, case_id, stored_filename)

    save_uploaded_file(file_content, file_path)

    file_hash = compute_sha256(file_path)
    evidence_type = detect_evidence_type(file.filename)

    existing_hash = db.query(Evidence).filter(
        Evidence.file_hash_sha256 == file_hash,
        Evidence.case_id == uuid.UUID(case_id)
    ).first()
    if existing_hash:
        os.remove(file_path)
        raise HTTPException(status_code=400, detail="Duplicate file already exists in this case")

    new_evidence = Evidence(
        id=evidence_id,
        case_id=uuid.UUID(case_id),
        original_filename=file.filename,
        stored_filename=stored_filename,
        file_path=file_path,
        file_size_bytes=file_size,
        file_hash_sha256=file_hash,
        evidence_type=EvidenceType(evidence_type),
        status=EvidenceStatus.UPLOADED,
        source_description=source_description,
        uploaded_by=uploaded_by,
        uploaded_at=datetime.utcnow()
    )
    db.add(new_evidence)
    db.commit()
    db.refresh(new_evidence)

    return {
        "message": "Evidence uploaded successfully",
        "evidence_id": str(new_evidence.id),
        "original_filename": file.filename,
        "evidence_type": evidence_type,
        "file_size_bytes": file_size,
        "file_hash_sha256": file_hash,
        "status": "uploaded"
    }

@router.get("/case/{case_id}")
def get_case_evidence(case_id: str, db: Session = Depends(get_db)):
    evidence_list = db.query(Evidence).filter(
        Evidence.case_id == uuid.UUID(case_id)
    ).all()
    result = []
    for e in evidence_list:
        result.append({
            "id": str(e.id),
            "original_filename": e.original_filename,
            "evidence_type": e.evidence_type,
            "file_size_bytes": e.file_size_bytes,
            "status": e.status,
            "uploaded_at": e.uploaded_at,
            "uploaded_by": e.uploaded_by,
            "source_description": e.source_description
        })
    return result

@router.get("/{evidence_id}")
def get_evidence(evidence_id: str, db: Session = Depends(get_db)):
    evidence = db.query(Evidence).filter(
        Evidence.id == uuid.UUID(evidence_id)
    ).first()
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")
    return {
        "id": str(evidence.id),
        "case_id": str(evidence.case_id),
        "original_filename": evidence.original_filename,
        "evidence_type": evidence.evidence_type,
        "file_size_bytes": evidence.file_size_bytes,
        "file_hash_sha256": evidence.file_hash_sha256,
        "status": evidence.status,
        "uploaded_at": evidence.uploaded_at,
        "source_description": evidence.source_description
    }

@router.post("/{evidence_id}/parse")
def parse_evidence(evidence_id: str, db: Session = Depends(get_db)):
    from parsers.cdr_parser import CDRParser
    from parsers.ipdr_parser import IPDRParser
    from parsers.gps_parser import GPSParser
    from parsers.financial_parser import FinancialParser
    from parsers.whatsapp_parser import WhatsAppParser
    from parsers.browser_parser import BrowserParser
    from parsers.bluetooth_parser import BluetoothParser
    evidence = db.query(Evidence).filter(
        Evidence.id == uuid.UUID(evidence_id)
    ).first()
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")

    PARSER_MAP = {
        "cdr": CDRParser,
        "ipdr": IPDRParser,
        "gps": GPSParser,
        "financial": FinancialParser,
        "whatsapp": WhatsAppParser,
        "browser": BrowserParser,
        "bluetooth": BluetoothParser
    }

    evidence_type = str(evidence.evidence_type.value if hasattr(evidence.evidence_type, 'value') else evidence.evidence_type)
    ParserClass = PARSER_MAP.get(evidence_type)

    if not ParserClass:
        raise HTTPException(status_code=400, detail=f"No parser available for evidence type: {evidence_type}")

    parser = ParserClass(
        file_path=evidence.file_path,
        evidence_id=str(evidence.id),
        case_id=str(evidence.case_id)
    )
    result = parser.run()

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["errors"])

    saved_entities = 0
    for entity_data in result["entities"]:
        existing = db.query(Entity).filter(
            Entity.case_id == evidence.case_id,
            Entity.value == entity_data["value"]
        ).first()
        if not existing:
            entity = Entity(
                id=uuid.uuid4(),
                case_id=evidence.case_id,
                evidence_id=evidence.id,
                entity_type=entity_data["type"],
                value=entity_data["value"],
                first_seen=entity_data.get("first_seen"),
                last_seen=entity_data.get("last_seen"),
                call_count=entity_data.get("call_count", 0),
                imei_list=entity_data.get("imei_list", []),
                imsi_list=entity_data.get("imsi_list", []),
                locations=entity_data.get("locations", [])
            )
            db.add(entity)
            saved_entities += 1

    saved_events = 0
    for event_data in result["events"]:
        event = Event(
            id=uuid.uuid4(),
            case_id=evidence.case_id,
            evidence_id=evidence.id,
            event_type=event_data["event_type"],
            timestamp=event_data["timestamp"],
            source_entity=event_data["source_entity"],
            target_entity=event_data["target_entity"],
            direction=event_data["direction"],
            duration_seconds=event_data.get("duration_seconds", 0),
            location=event_data.get("location", ""),
            cell_id=event_data.get("cell_id", ""),
            imei=event_data.get("imei", "")
        )
        db.add(event)
        saved_events += 1

    evidence.status = EvidenceStatus.PARSED
    evidence.parsed_at = datetime.utcnow()
    db.commit()

    return {
        "message": "Evidence parsed and saved successfully",
        "evidence_id": evidence_id,
        "evidence_type": evidence_type,
        "total_records": result["total_records"],
        "entities_saved": saved_entities,
        "events_saved": saved_events,
        "warnings": result["warnings"]
    }
@router.delete("/{evidence_id}")
def delete_evidence(evidence_id: str, db: Session = Depends(get_db)):
    evidence = db.query(Evidence).filter(
        Evidence.id == uuid.UUID(evidence_id)
    ).first()
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")
    
    # Delete the physical file
    if os.path.exists(evidence.file_path):
        os.remove(evidence.file_path)
    
    db.delete(evidence)
    db.commit()
    return {"message": "Evidence deleted successfully"}