from sqlalchemy.orm import Session
from typing import List, Dict, Any
from collections import defaultdict
import uuid
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from models.event import Event
from models.entity import Entity

class GeoEngine:
    def __init__(self, db: Session, case_id: str):
        self.db = db
        self.case_id = uuid.UUID(case_id)

    def reconstruct_routes(self, entity_value: str) -> List[Dict]:
        events = self.db.query(Event).filter(
            Event.case_id == self.case_id,
            Event.event_type == "GPS_MOVEMENT",
            Event.source_entity == entity_value
        ).all()
        sorted_events = sorted(events, key=lambda x: x.timestamp or "")
        routes = []
        for event in sorted_events:
            if event.location:
                routes.append({
                    "timestamp": event.timestamp,
                    "location": event.location,
                    "coordinates": event.target_entity
                })
        return routes

    def find_co_locations(self) -> List[Dict]:
        gps_events = self.db.query(Event).filter(
            Event.case_id == self.case_id,
            Event.event_type == "GPS_MOVEMENT"
        ).all()
        location_map = defaultdict(list)
        for event in gps_events:
            if event.location:
                location_map[event.location].append({
                    "entity": event.source_entity,
                    "timestamp": event.timestamp
                })
        co_locations = []
        for location, activities in location_map.items():
            entities = list(set([a["entity"] for a in activities]))
            if len(entities) > 1:
                co_locations.append({
                    "location": location,
                    "entities": entities,
                    "activity_count": len(activities),
                    "events": activities
                })
        return co_locations

    def detect_meeting_points(self, entity1: str, entity2: str) -> List[Dict]:
        events1 = self.db.query(Event).filter(
            Event.case_id == self.case_id,
            Event.event_type == "GPS_MOVEMENT",
            Event.source_entity == entity1
        ).all()
        events2 = self.db.query(Event).filter(
            Event.case_id == self.case_id,
            Event.event_type == "GPS_MOVEMENT",
            Event.source_entity == entity2
        ).all()
        meetings = []
        for e1 in events1:
            for e2 in events2:
                if e1.location == e2.location:
                    meetings.append({
                        "location": e1.location,
                        "entity1_time": e1.timestamp,
                        "entity2_time": e2.timestamp,
                        "confidence": 0.85
                    })
        return meetings

    def generate_heatmap_data(self, entity_value: str = None) -> Dict[str, Any]:
        query = self.db.query(Event).filter(
            Event.case_id == self.case_id,
            Event.event_type == "GPS_MOVEMENT"
        )
        if entity_value:
            query = query.filter(Event.source_entity == entity_value)
        events = query.all()
        location_freq = defaultdict(int)
        for event in events:
            if event.location:
                location_freq[event.location] += 1
        heatmap_points = []
        for location, freq in location_freq.items():
            heatmap_points.append({
                "location": location,
                "frequency": freq,
                "intensity": round(min(freq / 5, 1.0), 2)
            })
        return {
            "entity": entity_value or "all",
            "total_locations": len(heatmap_points),
            "heatmap_points": sorted(heatmap_points, key=lambda x: x["frequency"], reverse=True)
        }

    def geofence_analysis(self, entity_value: str, geofence_location: str) -> List[Dict]:
        events = self.db.query(Event).filter(
            Event.case_id == self.case_id,
            Event.event_type == "GPS_MOVEMENT",
            Event.source_entity == entity_value
        ).all()
        geofence_events = []
        for event in events:
            if event.location and event.location.lower() == geofence_location.lower():
                geofence_events.append({
                    "timestamp": event.timestamp,
                    "location": event.location,
                    "distance_km": 0.0
                })
        return geofence_events