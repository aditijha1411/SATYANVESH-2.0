import pandas as pd
import os
import sys
from typing import List, Dict, Any
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from parsers.base_parser import BaseParser

WHATSAPP_ALIASES = {
    "phone_number": ["phone_number", "msisdn", "sender", "from", "user"],
    "other_party": ["other_party", "recipient", "to", "contact", "receiver"],
    "message_type": ["message_type", "type", "msg_type", "chat_type"],
    "timestamp": ["timestamp", "date_time", "datetime", "date", "time", "sent_at"],
    "duration": ["duration", "call_duration"],
    "status": ["status", "delivery_status", "msg_status"]
}

class WhatsAppParser(BaseParser):
    def __init__(self, file_path, evidence_id, case_id):
        super().__init__(file_path, evidence_id, case_id)
        self.df = None
        self.column_map = {}

    def validate(self) -> bool:
        ext = os.path.splitext(self.file_path)[1].lower()
        if ext not in [".csv", ".xlsx", ".xls" ".txt"]:
            self.errors.append(f"Unsupported file type: {ext}")
            return False
        if not os.path.exists(self.file_path):
            self.errors.append("File not found")
            return False
        try:
            self.df = pd.read_csv(self.file_path, dtype=str) if ext == ".csv" else pd.read_excel(self.file_path, dtype=str)
            self.df.columns = [c.strip().lower().replace(" ", "_") for c in self.df.columns]
            self._map_columns()
            if "timestamp" not in self.column_map:
                self.errors.append("Could not find timestamp column")
                return False
            return True
        except Exception as e:
            self.errors.append(f"Failed to read file: {str(e)}")
            return False

    def _map_columns(self):
        for standard, aliases in WHATSAPP_ALIASES.items():
            for alias in aliases:
                if alias in self.df.columns:
                    self.column_map[standard] = alias
                    break

    def _get(self, row, field, default=""):
        col = self.column_map.get(field)
        if col and col in row:
            val = row[col]
            return str(val).strip() if pd.notna(val) else default
        return default

    def parse(self) -> List[Dict[str, Any]]:
        records = []
        for idx, row in self.df.iterrows():
            try:
                records.append({
                    "row_number": idx + 1,
                    "phone_number": self._get(row, "phone_number"),
                    "other_party": self._get(row, "other_party"),
                    "message_type": self._get(row, "message_type", "TEXT"),
                    "timestamp": self._get(row, "timestamp"),
                    "duration": self._get(row, "duration", "0"),
                    "status": self._get(row, "status")
                })
            except Exception as e:
                self.warnings.append(f"Row {idx+1} skipped: {str(e)}")
        return records

    def extract_entities(self, records: List[Dict]) -> List[Dict]:
        entities = {}
        for r in records:
            for field in ["phone_number", "other_party"]:
                val = r.get(field, "").strip()
                if val and val != "nan":
                    if val not in entities:
                        entities[val] = {"type": "phone_number", "value": val, "first_seen": r["timestamp"], "last_seen": r["timestamp"], "call_count": 0, "imei_list": [], "imsi_list": [], "locations": []}
                    entities[val]["call_count"] += 1
                    entities[val]["last_seen"] = r["timestamp"]
        return list(entities.values())

    def generate_events(self, records: List[Dict]) -> List[Dict]:
        events = []
        for r in records:
            msg_type = r.get("message_type", "").upper()
            event_type = "WHATSAPP_CALL" if "CALL" in msg_type else "WHATSAPP_MESSAGE"
            events.append({
                "event_type": event_type,
                "timestamp": r["timestamp"],
                "source_entity": r.get("phone_number"),
                "target_entity": r.get("other_party"),
                "direction": "OUTGOING",
                "duration_seconds": int(float(r["duration"])) if r["duration"] else 0,
                "location": "",
                "cell_id": "",
                "imei": "",
                "evidence_id": self.evidence_id,
                "case_id": self.case_id
            })
        return events