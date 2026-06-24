from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import sys, os, uuid
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from database.postgres import get_db
from models.event import Event
from models.entity import Entity

router = APIRouter(prefix="/geo", tags=["Geospatial"])

@router.get("/locations/{case_id}")
def get_locations(case_id: str, db: Session = Depends(get_db)):
    """Return all events that have GPS coordinates or location strings."""
    events = db.query(Event).filter(
        Event.case_id == uuid.UUID(case_id)
    ).all()

    points = []
    for e in events:
        loc = e.location or ""
        # Check if location has lat,lng format e.g. "17.4126,78.4071"
        if "," in loc:
            parts = loc.split(",")
            try:
                lat = float(parts[0].strip())
                lng = float(parts[1].strip())
                points.append({
                    "lat": lat,
                    "lng": lng,
                    "label": e.source_entity or "",
                    "event_type": e.event_type,
                    "timestamp": str(e.timestamp) if e.timestamp else "",
                    "location_name": loc,
                    "entity": e.source_entity
                })
                continue
            except ValueError:
                pass
        # Non-coordinate location string — still return it for display
        if loc:
            points.append({
                "lat": None,
                "lng": None,
                "label": e.source_entity or "",
                "event_type": e.event_type,
                "timestamp": str(e.timestamp) if e.timestamp else "",
                "location_name": loc,
                "entity": e.source_entity
            })

    return points

@router.get("/route/{case_id}/{entity}")
def get_entity_route(case_id: str, entity: str, db: Session = Depends(get_db)):
    """Return chronological location trail for a specific entity."""
    events = db.query(Event).filter(
        Event.case_id == uuid.UUID(case_id),
        Event.source_entity == entity
    ).order_by(Event.timestamp).all()

    route = []
    for e in events:
        loc = e.location or ""
        if "," in loc:
            parts = loc.split(",")
            try:
                lat = float(parts[0].strip())
                lng = float(parts[1].strip())
                route.append({
                    "lat": lat, "lng": lng,
                    "timestamp": str(e.timestamp) if e.timestamp else "",
                    "event_type": e.event_type,
                    "location_name": loc
                })
            except ValueError:
                pass
    return route

@router.get("/entities/{case_id}")
def get_geo_entities(case_id: str, db: Session = Depends(get_db)):
    """Return entities that have location data."""
    entities = db.query(Entity).filter(
        Entity.case_id == uuid.UUID(case_id)
    ).all()

    result = []
    for e in entities:
        locs = e.locations or []
        if locs:
            result.append({
                "id": str(e.id),
                "value": e.value,
                "type": e.entity_type,
                "locations": locs,
                "call_count": e.call_count
            })
    return result