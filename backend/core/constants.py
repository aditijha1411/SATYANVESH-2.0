from sqlalchemy.orm import Session
from typing import List, Dict, Any
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from models.entity import Entity
from models.event import Event
from models.relationship import Relationship
import uuid

class CorrelationEngine:
    def __init__(self, db: Session, case_id: str):
        self.db = db
        self.case_id = uuid.UUID(case_id)

    def run(self) -> Dict[str, Any]:
        events = self.db.query(Event).filter(Event.case_id == self.case_id).all()
        entities = self.db.query(Entity).filter(Entity.case_id == self.case_id).all()

        relationships = []
        relationships += self._correlate_by_communication(events)
        relationships += self._correlate_by_location(events)
        relationships += self._correlate_by_time(events)
        relationships += self._correlate_shared_devices(entities)

        saved = self._save_relationships(relationships)

        return {
            "total_events": len(events),
            "total_entities": len(entities),
            "relationships_found": len(relationships),
            "relationships_saved": saved
        }

    def _correlate_by_communication(self, events: List) -> List[Dict]:
        relationships = []
        comm_events = [e for e in events if e.event_type in ["PHONE_CALL", "SMS", "WHATSAPP_MESSAGE", "WHATSAPP_CALL"]]
        pairs = {}
        for event in comm_events:
            if event.source_entity and event.target_entity:
                key = tuple(sorted([event.source_entity, event.target_entity]))
                if key not in pairs:
                    pairs[key] = {"count": 0, "events": []}
                pairs[key]["count"] += 1
                pairs[key]["events"].append(str(event.id))

        for (a, b), data in pairs.items():
            relationships.append({
                "source": a,
                "target": b,
                "relationship_type": "COMMUNICATED_WITH",
                "weight": data["count"],
                "evidence": data["events"][:5]
            })
        return relationships

    def _correlate_by_location(self, events: List) -> List[Dict]:
        relationships = []
        location_events = [e for e in events if e.location and e.location != ""]
        location_map = {}
        for event in location_events:
            loc = event.location.strip()
            if loc not in location_map:
                location_map[loc] = []
            if event.source_entity:
                location_map[loc].append(event.source_entity)

        for location, entities in location_map.items():
            unique = list(set(entities))
            if len(unique) > 1:
                for i in range(len(unique)):
                    for j in range(i + 1, len(unique)):
                        relationships.append({
                            "source": unique[i],
                            "target": unique[j],
                            "relationship_type": "CO_LOCATED",
                            "weight": 1,
                            "evidence": [location]
                        })
        return relationships

    def _correlate_by_time(self, events: List) -> List[Dict]:
        relationships = []
        from collections import defaultdict
        time_buckets = defaultdict(list)
        for event in events:
            if event.timestamp and len(event.timestamp) >= 13:
                bucket = event.timestamp[:13]
                if event.source_entity:
                    time_buckets[bucket].append(event.source_entity)

        for bucket, entities in time_buckets.items():
            unique = list(set(entities))
            if len(unique) > 1:
                for i in range(len(unique)):
                    for j in range(i + 1, len(unique)):
                        relationships.append({
                            "source": unique[i],
                            "target": unique[j],
                            "relationship_type": "ACTIVE_SAME_TIME",
                            "weight": 1,
                            "evidence": [bucket]
                        })
        return relationships

    def _correlate_shared_devices(self, entities: List) -> List[Dict]:
        relationships = []
        imei_map = {}
        for entity in entities:
            if entity.imei_list:
                for imei in entity.imei_list:
                    if imei not in imei_map:
                        imei_map[imei] = []
                    imei_map[imei].append(entity.value)

        for imei, entity_values in imei_map.items():
            unique = list(set(entity_values))
            if len(unique) > 1:
                for i in range(len(unique)):
                    for j in range(i + 1, len(unique)):
                        relationships.append({
                            "source": unique[i],
                            "target": unique[j],
                            "relationship_type": "SHARED_DEVICE",
                            "weight": 5,
                            "evidence": [imei]
                        })
        return relationships

    def _save_relationships(self, relationships: List[Dict]) -> int:
        saved = 0
        for rel in relationships:
            existing = self.db.query(Relationship).filter(
                Relationship.case_id == self.case_id,
                Relationship.source_entity == rel["source"],
                Relationship.target_entity == rel["target"],
                Relationship.relationship_type == rel["relationship_type"]
            ).first()
            if existing:
                existing.weight += rel["weight"]
                self.db.commit()
            else:
                new_rel = Relationship(
                    id=uuid.uuid4(),
                    case_id=self.case_id,
                    source_entity=rel["source"],
                    target_entity=rel["target"],
                    relationship_type=rel["relationship_type"],
                    weight=rel["weight"],
                    evidence_refs=rel["evidence"]
                )
                self.db.add(new_rel)
                saved += 1
        self.db.commit()
        return saved