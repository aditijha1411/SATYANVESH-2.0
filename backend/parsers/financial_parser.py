import pandas as pd
import os
import sys
from typing import List, Dict, Any
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from parsers.base_parser import BaseParser

FINANCIAL_ALIASES = {
    "account_number": ["account_number", "account_no", "acc_no", "account", "from_account"],
    "other_account": ["other_account", "to_account", "beneficiary_account", "dest_account"],
    "transaction_type": ["transaction_type", "txn_type", "type", "transaction_mode", "mode"],
    "amount": ["amount", "txn_amount", "transaction_amount", "value", "debit", "credit"],
    "timestamp": ["timestamp", "date", "txn_date", "transaction_date", "datetime"],
    "description": ["description", "remarks", "narration", "details", "note"],
    "balance": ["balance", "closing_balance", "available_balance"],
    "reference": ["reference", "ref_no", "txn_id", "transaction_id", "utr"]
}

class FinancialParser(BaseParser):
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
                self.errors.append("Could not find date/timestamp column")
                return False
            return True
        except Exception as e:
            self.errors.append(f"Failed to read file: {str(e)}")
            return False

    def _map_columns(self):
        for standard, aliases in FINANCIAL_ALIASES.items():
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
                    "account_number": self._get(row, "account_number"),
                    "other_account": self._get(row, "other_account"),
                    "transaction_type": self._get(row, "transaction_type"),
                    "amount": self._get(row, "amount", "0"),
                    "timestamp": self._get(row, "timestamp"),
                    "description": self._get(row, "description"),
                    "balance": self._get(row, "balance"),
                    "reference": self._get(row, "reference")
                })
            except Exception as e:
                self.warnings.append(f"Row {idx+1} skipped: {str(e)}")
        return records

    def extract_entities(self, records: List[Dict]) -> List[Dict]:
        entities = {}
        for r in records:
            for field, etype in [("account_number", "bank_account"), ("other_account", "bank_account")]:
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
            txn_type = r.get("transaction_type", "").upper()
            events.append({
                "event_type": "FINANCIAL_TRANSACTION",
                "timestamp": r["timestamp"],
                "source_entity": r.get("account_number"),
                "target_entity": r.get("other_account"),
                "direction": txn_type or "TRANSFER",
                "duration_seconds": 0,
                "location": "",
                "cell_id": "",
                "imei": "",
                "evidence_id": self.evidence_id,
                "case_id": self.case_id
            })
        return events