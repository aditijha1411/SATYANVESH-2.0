from sqlalchemy.orm import Session
from typing import List, Dict, Any
from collections import defaultdict
import uuid
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from models.event import Event
from models.entity import Entity

class PatternDetector:
    def __init__(self, db: Session, case_id: str):
        self.db = db
        self.case_id = uuid.UUID(case_id)

    def detect(self) -> List[Dict[str, Any]]:
        patterns = []
        patterns += self._detect_burst_calls()
        patterns += self._detect_call_before_incident()
        patterns += self._detect_new_numbers()
        return patterns

    def _detect_burst_calls(self) -> List[Dict]:
        patterns = []
        events = self.db.query(Event).filter(
            Event.case_id == self.case_id,
            Event.event_type == "PHONE_CALL"
        ).all()

        hour_buckets = defaultdict(list)
        for event in events:
            if event.timestamp and len(event.timestamp) >= 13:
                bucket = f"{event.timestamp[:10]} {event.timestamp[11:13]}:00"
                hour_buckets[bucket].append(event)

        for hour, evts in hour_buckets.items():
            if len(evts) >= 4:
                entities = list(set([e.source_entity for e in evts if e.source_entity]))
                patterns.append({
                    "pattern_type": "BURST_CALLS",
                    "description": f"{len(evts)} calls detected in a single hour at {hour}",
                    "confidence": 0.75,
                    "entities": entities,
                    "timestamp": hour
                })
        return patterns

    def _detect_call_before_incident(self) -> List[Dict]:
        patterns = []
        events = self.db.query(Event).filter(
            Event.case_id == self.case_id
        ).order_by(Event.timestamp).all()

        gps_events = [e for e in events if e.event_type == "GPS_MOVEMENT"]
        call_events = [e for e in events if e.event_type == "PHONE_CALL"]

        for gps in gps_events:
            if not gps.timestamp:
                continue
            nearby_calls = [
                c for c in call_events
                if c.timestamp and abs(len(c.timestamp) - len(gps.timestamp)) < 2
                and c.timestamp[:13] == gps.timestamp[:13]
                and c.source_entity == gps.source_entity
            ]
            if nearby_calls:
                patterns.append({
                    "pattern_type": "CALL_BEFORE_MOVEMENT",
                    "description": f"{gps.source_entity} made calls around the same time as GPS movement at {gps.location}",
                    "confidence": 0.70,
                    "entities": [gps.source_entity],
                    "timestamp": gps.timestamp
                })
        return patterns

    def _detect_new_numbers(self) -> List[Dict]:
        patterns = []
        entities = self.db.query(Entity).filter(
            Entity.case_id == self.case_id,
            Entity.entity_type == "phone_number"
        ).all()

        for entity in entities:
            if entity.call_count == 1:
                patterns.append({
                    "pattern_type": "ONE_TIME_CONTACT",
                    "description": f"{entity.value} appears only once in records — may be a burner phone or one-time contact",
                    "confidence": 0.65,
                    "entities": [entity.value],
                    "timestamp": entity.first_seen
                })
        return patterns