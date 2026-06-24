import pandas as pd
import os
import sys
from typing import List, Dict, Any
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from parsers.base_parser import BaseParser

REQUIRED_COLUMNS = {
    "phone_number", "call_type", "duration", "timestamp"
}

CDR_COLUMN_ALIASES = {
    "phone_number": ["phone_number", "msisdn", "calling_number", "number", "mobile", "phone", "caller", "a_party"],
    "other_party": ["other_party", "called_number", "b_party", "destination", "dialed_number", "contact"],
    "call_type": ["call_type", "type", "call_direction", "direction", "record_type"],
    "duration": ["duration", "call_duration", "duration_seconds", "duration_sec", "dur"],
    "timestamp": ["timestamp", "date_time", "call_time", "datetime", "date", "time", "call_date"],
    "imei": ["imei", "device_imei", "handset_imei"],
    "imsi": ["imsi", "subscriber_imsi"],
    "cell_id": ["cell_id", "cell_tower", "tower_id", "bts_id", "site_id"],
    "location": ["location", "address", "area", "city", "region"]
}

class CDRParser(BaseParser):

    def __init__(self, file_path: str, evidence_id: str, case_id: str):
        super().__init__(file_path, evidence_id, case_id)
        self.df = None
        self.column_map = {}

    def validate(self) -> bool:
        ext = os.path.splitext(self.file_path)[1].lower()
        if ext not in [".csv", ".xlsx", ".xls"]:
            self.errors.append(f"Unsupported file type: {ext}. CDR parser supports CSV and Excel.")
            return False
        if not os.path.exists(self.file_path):
            self.errors.append(f"File not found: {self.file_path}")
            return False
        try:
            if ext == ".csv":
                self.df = pd.read_csv(self.file_path, dtype=str)
            else:
                self.df = pd.read_excel(self.file_path, dtype=str)
            self.df.columns = [c.strip().lower().replace(" ", "_") for c in self.df.columns]
            self._map_columns()
            if "phone_number" not in self.column_map:
                self.errors.append("Could not find phone number column. Expected columns like: msisdn, phone_number, calling_number")
                return False
            if "timestamp" not in self.column_map:
                self.errors.append("Could not find timestamp column. Expected columns like: timestamp, date_time, call_time")
                return False
            return True
        except Exception as e:
            self.errors.append(f"Failed to read file: {str(e)}")
            return False

    def _map_columns(self):
        for standard_name, aliases in CDR_COLUMN_ALIASES.items():
            for alias in aliases:
                if alias in self.df.columns:
                    self.column_map[standard_name] = alias
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
                record = {
                    "row_number": idx + 1,
                    "phone_number": self._get(row, "phone_number"),
                    "other_party": self._get(row, "other_party"),
                    "call_type": self._get(row, "call_type", "UNKNOWN"),
                    "duration_seconds": self._parse_duration(self._get(row, "duration", "0")),
                    "timestamp": self._parse_timestamp(self._get(row, "timestamp")),
                    "imei": self._get(row, "imei"),
                    "imsi": self._get(row, "imsi"),
                    "cell_id": self._get(row, "cell_id"),
                    "location": self._get(row, "location"),
                    "raw_row": row.to_dict()
                }
                records.append(record)
            except Exception as e:
                self.warnings.append(f"Row {idx+1} skipped: {str(e)}")
        return records

    def _parse_duration(self, value: str) -> int:
        try:
            return int(float(value))
        except:
            return 0

    def _parse_timestamp(self, value: str) -> str:
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%d-%m-%Y %H:%M:%S",
            "%d/%m/%Y %H:%M:%S",
            "%Y/%m/%d %H:%M:%S",
            "%d-%m-%Y %H:%M",
            "%Y-%m-%dT%H:%M:%S",
            "%d-%m-%Y",
            "%Y-%m-%d"
        ]
        for fmt in formats:
            try:
                return datetime.strptime(value.strip(), fmt).isoformat()
            except:
                continue
        self.warnings.append(f"Could not parse timestamp: {value}")
        return value

    def extract_entities(self, records: List[Dict]) -> List[Dict]:
        entities = {}
        for record in records:
            for field in ["phone_number", "other_party"]:
                number = record.get(field, "").strip()
                if number and number != "nan":
                    if number not in entities:
                        entities[number] = {
                            "type": "phone_number",
                            "value": number,
                            "first_seen": record["timestamp"],
                            "last_seen": record["timestamp"],
                            "call_count": 0,
                            "imei_list": set(),
                            "imsi_list": set(),
                            "locations": set()
                        }
                    entities[number]["call_count"] += 1
                    entities[number]["last_seen"] = record["timestamp"]
                    if record.get("imei"):
                        entities[number]["imei_list"].add(record["imei"])
                    if record.get("imsi"):
                        entities[number]["imsi_list"].add(record["imsi"])
                    if record.get("location"):
                        entities[number]["locations"].add(record["location"])

        result = []
        for number, data in entities.items():
            data["imei_list"] = list(data["imei_list"])
            data["imsi_list"] = list(data["imsi_list"])
            data["locations"] = list(data["locations"])
            result.append(data)
        return result

    def generate_events(self, records: List[Dict]) -> List[Dict]:
        events = []
        for record in records:
            call_type = record.get("call_type", "").upper()
            if "OUT" in call_type or "MO" in call_type:
                direction = "OUTGOING"
            elif "IN" in call_type or "MT" in call_type:
                direction = "INCOMING"
            elif "SMS" in call_type:
                direction = "SMS"
            else:
                direction = call_type or "UNKNOWN"

            event = {
                "event_type": "PHONE_CALL" if "SMS" not in direction else "SMS",
                "timestamp": record["timestamp"],
                "source_entity": record["phone_number"],
                "target_entity": record["other_party"],
                "direction": direction,
                "duration_seconds": record["duration_seconds"],
                "location": record["location"],
                "cell_id": record["cell_id"],
                "imei": record["imei"],
                "evidence_id": self.evidence_id,
                "case_id": self.case_id
            }
            events.append(event)
        return events