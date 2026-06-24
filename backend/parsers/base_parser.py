from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import datetime

class BaseParser(ABC):
    def __init__(self, file_path: str, evidence_id: str, case_id: str):
        self.file_path = file_path
        self.evidence_id = evidence_id
        self.case_id = case_id
        self.errors = []
        self.warnings = []

    @abstractmethod
    def validate(self) -> bool:
        pass

    @abstractmethod
    def parse(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def extract_entities(self, records: List[Dict]) -> List[Dict]:
        pass

    @abstractmethod
    def generate_events(self, records: List[Dict]) -> List[Dict]:
        pass

    def run(self) -> Dict[str, Any]:
        if not self.validate():
            return {
                "success": False,
                "errors": self.errors,
                "records": [],
                "entities": [],
                "events": []
            }
        records = self.parse()
        entities = self.extract_entities(records)
        events = self.generate_events(records)
        return {
            "success": True,
            "evidence_id": self.evidence_id,
            "case_id": self.case_id,
            "total_records": len(records),
            "total_entities": len(entities),
            "total_events": len(events),
            "records": records,
            "entities": entities,
            "events": events,
            "errors": self.errors,
            "warnings": self.warnings
        }