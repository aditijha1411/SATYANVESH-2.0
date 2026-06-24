from sqlalchemy.orm import Session
from models.entity import Entity
from models.event import Event
from models.relationship import Relationship
import uuid
from collections import defaultdict


class CorrelationEngine:
    def __init__(self, db: Session, case_id: str):
        self.db = db
        self.case_id = uuid.UUID(case_id)

    def run(self) -> dict:
        self.db.query(Relationship).filter(
            Relationship.case_id == self.case_id
        ).delete()
        self.db.commit()

        events = self.db.query(Event).filter(Event.case_id == self.case_id).all()

        relationships = []
        relationships += self._correlate_communication(events)
        relationships += self._correlate_common_contacts(events)

        saved = 0
        for rel in relationships:
            existing = self.db.query(Relationship).filter(
                Relationship.case_id == self.case_id,
                Relationship.source_entity == rel["source"],
                Relationship.target_entity == rel["target"],
                Relationship.relationship_type == rel["type"]
            ).first()
            if existing:
                existing.weight = existing.weight + 1
            else:
                self.db.add(Relationship(
                    id=uuid.uuid4(),
                    case_id=self.case_id,
                    source_entity=rel["source"],
                    target_entity=rel["target"],
                    relationship_type=rel["type"],
                    weight=rel["weight"],
                    evidence_refs=[]
                ))
                saved += 1

        self.db.commit()
        return {
            "status": "success",
            "relationships_found": saved,
            "events_analyzed": len(events)
        }

    def _correlate_communication(self, events):
        pairs = defaultdict(int)
        for e in events:
            src, tgt = e.source_entity, e.target_entity
            if not src or not tgt or src == tgt:
                continue
            key = tuple(sorted([src, tgt]))
            pairs[key] += 1

        return [
            {"source": src, "target": tgt, "type": "COMMUNICATION",
             "weight": min(10, count)}
            for (src, tgt), count in pairs.items()
        ]

    def _correlate_common_contacts(self, events):
        contact_map = defaultdict(set)
        for e in events:
            if e.source_entity and e.target_entity and e.source_entity != e.target_entity:
                contact_map[e.source_entity].add(e.target_entity)
                contact_map[e.target_entity].add(e.source_entity)

        entities = list(contact_map.keys())
        rels, seen = [], set()
        for i in range(len(entities)):
            for j in range(i + 1, len(entities)):
                e1, e2 = entities[i], entities[j]
                key = tuple(sorted([e1, e2]))
                if key in seen:
                    continue
                seen.add(key)
                common = contact_map[e1] & contact_map[e2] - {e1, e2}
                if common:
                    rels.append({"source": e1, "target": e2,
                                 "type": "COMMON_CONTACTS",
                                 "weight": min(10, len(common))})
        return rels