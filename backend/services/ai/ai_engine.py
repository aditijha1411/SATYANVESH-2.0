from sqlalchemy.orm import Session
from typing import List, Dict, Any
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from services.ai.lead_generator import LeadGenerator
from services.ai.pattern_detector import PatternDetector

class AIEngine:
    def __init__(self, db: Session, case_id: str):
        self.db = db
        self.case_id = case_id

    def run_full_analysis(self) -> Dict[str, Any]:
        lead_gen = LeadGenerator(db=self.db, case_id=self.case_id)
        leads = lead_gen.generate()

        detector = PatternDetector(db=self.db, case_id=self.case_id)
        patterns = detector.detect()

        return {
            "case_id": self.case_id,
            "total_leads": len(leads),
            "total_patterns": len(patterns),
            "leads": leads,
            "patterns": patterns
        }