from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database.postgres import get_db
from models.entity import Entity
from models.event import Event
from models.relationship import Relationship
import uuid

router = APIRouter(prefix="/graph", tags=["Knowledge Graph"])

@router.post("/correlate/{case_id}")
def run_correlation(case_id: str, db: Session = Depends(get_db)):
    from services.correlation.correlation_engine import CorrelationEngine
    engine = CorrelationEngine(db=db, case_id=case_id)
    result = engine.run()
    return result

@router.get("/entities/{case_id}")
def get_entities(case_id: str, db: Session = Depends(get_db)):
    entities = db.query(Entity).filter(
        Entity.case_id == uuid.UUID(case_id)
    ).all()
    return [{"id": str(e.id), "type": e.entity_type, "value": e.value,
             "activity_count": e.call_count, "first_seen": e.first_seen,
             "last_seen": e.last_seen, "locations": e.locations,
             "imei_list": e.imei_list, "imsi_list": e.imsi_list} for e in entities]

@router.get("/relationships/{case_id}")
def get_relationships(case_id: str, db: Session = Depends(get_db)):
    rels = db.query(Relationship).filter(
        Relationship.case_id == uuid.UUID(case_id)
    ).all()
    return [{"id": str(r.id), "source": r.source_entity, "target": r.target_entity,
             "type": r.relationship_type, "weight": r.weight,
             "evidence": r.evidence_refs} for r in rels]

@router.get("/events/{case_id}")
def get_events(case_id: str, db: Session = Depends(get_db)):
    events = db.query(Event).filter(
        Event.case_id == uuid.UUID(case_id)
    ).all()
    return [{"id": str(e.id), "type": e.event_type, "timestamp": e.timestamp,
             "source": e.source_entity, "target": e.target_entity,
             "direction": e.direction, "duration": e.duration_seconds,
             "location": e.location} for e in events]

@router.get("/geo/routes/{case_id}/{entity}")
def get_entity_route(case_id: str, entity: str, db: Session = Depends(get_db)):
    from services.geo.geo_engine import GeoEngine
    engine = GeoEngine(db=db, case_id=case_id)
    return {"entity": entity, "route": engine.reconstruct_routes(entity)}

@router.get("/geo/colocations/{case_id}")
def get_colocations(case_id: str, db: Session = Depends(get_db)):
    from services.geo.geo_engine import GeoEngine
    engine = GeoEngine(db=db, case_id=case_id)
    return engine.find_co_locations()

@router.get("/geo/meetings/{case_id}")
def get_meetings(case_id: str, entity1: str, entity2: str, db: Session = Depends(get_db)):
    from services.geo.geo_engine import GeoEngine
    engine = GeoEngine(db=db, case_id=case_id)
    return engine.detect_meeting_points(entity1, entity2)

@router.get("/geo/heatmap/{case_id}")
def get_heatmap(case_id: str, entity: str = None, db: Session = Depends(get_db)):
    from services.geo.geo_engine import GeoEngine
    engine = GeoEngine(db=db, case_id=case_id)
    return engine.generate_heatmap_data(entity)

@router.get("/geo/geofence/{case_id}")
def get_geofence(case_id: str, entity: str, location: str, db: Session = Depends(get_db)):
    from services.geo.geo_engine import GeoEngine
    engine = GeoEngine(db=db, case_id=case_id)
    return engine.geofence_analysis(entity, location)