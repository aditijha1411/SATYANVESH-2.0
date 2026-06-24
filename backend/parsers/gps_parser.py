import pandas as pd
import json
import os
import sys
from typing import List, Dict, Any
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from parsers.base_parser import BaseParser

GPS_ALIASES = {
    "phone_number": ["msisdn", "phone_number", "device_id", "imei", "subscriber"],
    "latitude": ["latitude", "lat", "y"],
    "longitude": ["longitude", "lon", "lng", "long", "x"],
    "timestamp": ["timestamp", "date_time", "datetime", "time", "date"],
    "speed": ["speed", "velocity", "speed_kmh"],
    "accuracy": ["accuracy", "precision", "hdop"],
    "location_name": ["location_name", "location", "address", "place", "area", "landmark"]
}

class GPSParser(BaseParser):
    def __init__(self, file_path, evidence_id, case_id):
        super().__init__(file_path, evidence_id, case_id)
        self.df = None
        self.column_map = {}

    def validate(self) -> bool:
        ext = os.path.splitext(self.file_path)[1].lower()
        if ext not in [".csv", ".xlsx", ".xls", ".json"]:
            self.errors.append(f"Unsupported file type: {ext}")
            return False
        if not os.path.exists(self.file_path):
            self.errors.append("File not found")
            return False
        try:
            if ext == ".json":
                with open(self.file_path, "r") as f:
                    data = json.load(f)
                records = data.get("gps_records", data) if isinstance(data, dict) else data
                self.df = pd.DataFrame(records)
            elif ext == ".csv":
                self.df = pd.read_csv(self.file_path, dtype=str)
            else:
                self.df = pd.read_excel(self.file_path, dtype=str)
            self.df.columns = [c.strip().lower().replace(" ", "_") for c in self.df.columns]
            self._map_columns()
            if "latitude" not in self.column_map or "longitude" not in self.column_map:
                self.errors.append("Could not find latitude/longitude columns")
                return False
            return True
        except Exception as e:
            self.errors.append(f"Failed to read file: {str(e)}")
            return False

    def _map_columns(self):
        for standard, aliases in GPS_ALIASES.items():
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
                    "latitude": float(self._get(row, "latitude", "0")),
                    "longitude": float(self._get(row, "longitude", "0")),
                    "timestamp": self._get(row, "timestamp"),
                    "speed": self._get(row, "speed", "0"),
                    "accuracy": self._get(row, "accuracy"),
                    "location_name": self._get(row, "location_name")
                })
            except Exception as e:
                self.warnings.append(f"Row {idx+1} skipped: {str(e)}")
        return records

    def extract_entities(self, records: List[Dict]) -> List[Dict]:
        entities = {}
        for r in records:
            val = r.get("phone_number", "").strip()
            if val and val != "nan":
                if val not in entities:
                    entities[val] = {"type": "phone_number", "value": val, "first_seen": r["timestamp"], "last_seen": r["timestamp"], "call_count": 0, "imei_list": [], "imsi_list": [], "locations": []}
                entities[val]["call_count"] += 1
                entities[val]["last_seen"] = r["timestamp"]
                loc = r.get("location_name") or f"{r['latitude']},{r['longitude']}"
                if loc and loc not in entities[val]["locations"]:
                    entities[val]["locations"].append(loc)
        return list(entities.values())

    def generate_events(self, records: List[Dict]) -> List[Dict]:
        events = []
        for r in records:
            events.append({
                "event_type": "GPS_MOVEMENT",
                "timestamp": r["timestamp"],
                "source_entity": r.get("phone_number"),
                "target_entity": f"{r['latitude']},{r['longitude']}",
                "direction": "MOVEMENT",
                "duration_seconds": 0,
                "location": r.get("location_name") or f"{r['latitude']},{r['longitude']}",
                "cell_id": "",
                "imei": "",
                "evidence_id": self.evidence_id,
                "case_id": self.case_id
            })
        return events