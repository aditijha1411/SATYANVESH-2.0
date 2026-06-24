import pandas as pd
import os
import sys
from typing import List, Dict, Any
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from parsers.base_parser import BaseParser

BT_ALIASES = {
    "device_address": ["device_address", "mac_address", "bt_address", "source_device"],
    "remote_device": ["remote_device", "remote_mac", "target_device", "connected_device"],
    "timestamp": ["timestamp", "connection_time", "datetime", "date_time"],
    "signal_strength": ["signal_strength", "rssi", "signal", "strength"],
    "device_name": ["device_name", "name", "device"]
}

class BluetoothParser(BaseParser):
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
            return True
        except Exception as e:
            self.errors.append(f"Failed to read file: {str(e)}")
            return False

    def _map_columns(self):
        for standard, aliases in BT_ALIASES.items():
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
                    "device_address": self._get(row, "device_address"),
                    "remote_device": self._get(row, "remote_device"),
                    "timestamp": self._get(row, "timestamp", ""),
                    "signal_strength": self._get(row, "signal_strength"),
                    "device_name": self._get(row, "device_name")
                })
            except Exception as e:
                self.warnings.append(f"Row {idx+1} skipped: {str(e)}")
        return records

    def extract_entities(self, records: List[Dict]) -> List[Dict]:
        entities = {}
        for r in records:
            for field in ["device_address", "remote_device"]:
                val = r.get(field, "").strip()
                if val and val != "nan":
                    if val not in entities:
                        entities[val] = {"type": "bluetooth_device", "value": val, "first_seen": r.get("timestamp", ""), "last_seen": r.get("timestamp", ""), "call_count": 0, "imei_list": [], "imsi_list": [], "locations": []}
                    entities[val]["call_count"] += 1
                    entities[val]["last_seen"] = r.get("timestamp", "")
        return list(entities.values())

    def generate_events(self, records: List[Dict]) -> List[Dict]:
        events = []
        for r in records:
            if r["timestamp"]:
                events.append({
                    "event_type": "BLUETOOTH_PAIRING",
                    "timestamp": r["timestamp"],
                    "source_entity": r.get("device_address"),
                    "target_entity": r.get("remote_device"),
                    "direction": "PAIRING",
                    "duration_seconds": 0,
                    "location": "",
                    "cell_id": "",
                    "imei": "",
                    "evidence_id": self.evidence_id,
                    "case_id": self.case_id
                })
        return events