import pandas as pd
import os
import sys
from typing import List, Dict, Any
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from parsers.base_parser import BaseParser

IPDR_ALIASES = {
    "phone_number": ["msisdn", "phone_number", "subscriber", "mobile", "number"],
    "ip_address": ["ip_address", "ip", "source_ip", "src_ip", "assigned_ip"],
    "destination_ip": ["destination_ip", "dest_ip", "remote_ip", "server_ip"],
    "url": ["url", "domain", "website", "host", "destination_url"],
    "timestamp": ["timestamp", "date_time", "start_time", "datetime", "date"],
    "duration": ["duration", "session_duration", "time_spent"],
    "data_volume": ["data_volume", "bytes", "data_bytes", "volume", "data_used"],
    "protocol": ["protocol", "proto", "service"],
    "imei": ["imei", "device_imei"],
    "cell_id": ["cell_id", "tower_id", "bts_id"]
}

class IPDRParser(BaseParser):
    def __init__(self, file_path, evidence_id, case_id):
        super().__init__(file_path, evidence_id, case_id)
        self.df = None
        self.column_map = {}

    def validate(self) -> bool:
        ext = os.path.splitext(self.file_path)[1].lower()
        if ext not in [".csv", ".xlsx", ".xls"]:
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
        for standard, aliases in IPDR_ALIASES.items():
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
                    "ip_address": self._get(row, "ip_address"),
                    "destination_ip": self._get(row, "destination_ip"),
                    "url": self._get(row, "url"),
                    "timestamp": self._get(row, "timestamp"),
                    "duration": self._get(row, "duration", "0"),
                    "data_volume": self._get(row, "data_volume", "0"),
                    "protocol": self._get(row, "protocol"),
                    "imei": self._get(row, "imei"),
                    "cell_id": self._get(row, "cell_id")
                })
            except Exception as e:
                self.warnings.append(f"Row {idx+1} skipped: {str(e)}")
        return records

    def extract_entities(self, records: List[Dict]) -> List[Dict]:
        entities = {}
        for r in records:
            for field, etype in [("ip_address", "ip_address"), ("phone_number", "phone_number"), ("url", "url")]:
                val = r.get(field, "").strip()
                if val and val != "nan":
                    if val not in entities:
                        entities[val] = {"type": etype, "value": val, "first_seen": r["timestamp"], "last_seen": r["timestamp"], "call_count": 0, "imei_list": [], "imsi_list": [], "locations": []}
                    entities[val]["call_count"] += 1
                    entities[val]["last_seen"] = r["timestamp"]
        return list(entities.values())

    def generate_events(self, records: List[Dict]) -> List[Dict]:
        events = []
        for r in records:
            events.append({
                "event_type": "INTERNET_SESSION",
                "timestamp": r["timestamp"],
                "source_entity": r.get("phone_number") or r.get("ip_address"),
                "target_entity": r.get("url") or r.get("destination_ip"),
                "direction": "OUTGOING",
                "duration_seconds": int(float(r["duration"])) if r["duration"] else 0,
                "location": "",
                "cell_id": r.get("cell_id"),
                "imei": r.get("imei"),
                "evidence_id": self.evidence_id,
                "case_id": self.case_id
            })
        return events