from sqlalchemy.orm import Session
from typing import List, Dict, Any
import uuid
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from models.entity import Entity
from models.event import Event
from models.relationship import Relationship

class LeadGenerator:
    def __init__(self, db: Session, case_id: str):
        self.db = db
        self.case_id = uuid.UUID(case_id)

    def generate(self) -> List[Dict[str, Any]]:
        leads = []
        leads += self._high_frequency_contact()
        leads += self._shared_device_users()
        leads += self._location_overlap()
        leads += self._financial_to_communication_link()
        leads += self._dormant_then_active()
        return sorted(leads, key=lambda x: x["confidence"], reverse=True)

    def _high_frequency_contact(self) -> List[Dict]:
        leads = []
        rels = self.db.query(Relationship).filter(
            Relationship.case_id == self.case_id,
            Relationship.relationship_type == "COMMUNICATED_WITH"
        ).all()
        for rel in rels:
            if rel.weight >= 5:
                confidence = min(0.5 + (rel.weight * 0.05), 0.95)
                leads.append({
                    "lead_type": "HIGH_FREQUENCY_CONTACT",
                    "title": f"Frequent communication between {rel.source_entity} and {rel.target_entity}",
                    "description": f"These two numbers contacted each other {rel.weight} times. High frequency contact may indicate coordination.",
                    "entities_involved": [rel.source_entity, rel.target_entity],
                    "confidence": round(confidence, 2),
                    "evidence_ids": rel.evidence_refs,
                    "recommended_action": f"Obtain full call records and message content for {rel.source_entity} and {rel.target_entity}"
                })
        return leads

    def _shared_device_users(self) -> List[Dict]:
        leads = []
        rels = self.db.query(Relationship).filter(
            Relationship.case_id == self.case_id,
            Relationship.relationship_type == "SHARED_DEVICE"
        ).all()
        for rel in rels:
            leads.append({
                "lead_type": "SHARED_DEVICE",
                "title": f"Shared device detected between {rel.source_entity} and {rel.target_entity}",
                "description": f"Numbers {rel.source_entity} and {rel.target_entity} used the same physical device (IMEI). This strongly suggests these numbers belong to the same person or co-conspirators.",
                "entities_involved": [rel.source_entity, rel.target_entity],
                "confidence": 0.92,
                "evidence_ids": rel.evidence_refs,
                "recommended_action": "Verify device ownership and check if both numbers were active simultaneously"
            })
        return leads

    def _location_overlap(self) -> List[Dict]:
        leads = []
        rels = self.db.query(Relationship).filter(
            Relationship.case_id == self.case_id,
            Relationship.relationship_type == "CO_LOCATED"
        ).all()
        for rel in rels:
            leads.append({
                "lead_type": "LOCATION_OVERLAP",
                "title": f"Co-location detected: {rel.source_entity} and {rel.target_entity}",
                "description": f"These entities were detected at the same location: {rel.evidence_refs}. Physical proximity may indicate a meeting.",
                "entities_involved": [rel.source_entity, rel.target_entity],
                "confidence": 0.75,
                "evidence_ids": rel.evidence_refs,
                "recommended_action": "Cross-reference location timing with communication events to confirm meeting"
            })
        return leads

    def _financial_to_communication_link(self) -> List[Dict]:
        leads = []
        financial_events = self.db.query(Event).filter(
            Event.case_id == self.case_id,
            Event.event_type == "FINANCIAL_TRANSACTION"
        ).all()
        comm_events = self.db.query(Event).filter(
            Event.case_id == self.case_id,
            Event.event_type.in_(["PHONE_CALL", "WHATSAPP_CALL", "SMS"])
        ).all()

        financial_entities = set()
        for e in financial_events:
            if e.source_entity:
                financial_entities.add(e.source_entity)
            if e.target_entity:
                financial_entities.add(e.target_entity)

        comm_entities = set()
        for e in comm_events:
            if e.source_entity:
                comm_entities.add(e.source_entity)
            if e.target_entity:
                comm_entities.add(e.target_entity)

        overlap = financial_entities.intersection(comm_entities)
        for entity in overlap:
            leads.append({
                "lead_type": "FINANCIAL_COMMUNICATION_LINK",
                "title": f"Entity {entity} appears in both financial and communication records",
                "description": f"This entity has both financial transactions and communication events. This may indicate financial coordination.",
                "entities_involved": [entity],
                "confidence": 0.78,
                "evidence_ids": [],
                "recommended_action": f"Map all financial transactions of {entity} against communication timeline"
            })
        return leads

    def _dormant_then_active(self) -> List[Dict]:
        leads = []
        entities = self.db.query(Entity).filter(
            Entity.case_id == self.case_id
        ).all()
        for entity in entities:
            if entity.first_seen and entity.last_seen:
                if entity.first_seen != entity.last_seen:
                    if entity.call_count and entity.call_count >= 3:
                        leads.append({
                            "lead_type": "ACTIVE_ENTITY",
                            "title": f"Entity {entity.value} shows significant activity",
                            "description": f"Active from {entity.first_seen} to {entity.last_seen} with {entity.call_count} recorded events.",
                            "entities_involved": [entity.value],
                            "confidence": 0.60,
                            "evidence_ids": [],
                            "recommended_action": f"Build full profile for {entity.value} across all evidence sources"
                        })
        return leads