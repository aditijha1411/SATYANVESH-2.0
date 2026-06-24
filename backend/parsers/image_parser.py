import os
import sys
from typing import List, Dict, Any
from pathlib import Path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from parsers.base_parser import BaseParser

class ImageParser(BaseParser):
    def __init__(self, file_path, evidence_id, case_id):
        super().__init__(file_path, evidence_id, case_id)

    def validate(self) -> bool:
        ext = os.path.splitext(self.file_path)[1].lower()
        if ext not in [".jpg", ".jpeg", ".png", ".gif", ".bmp"]:
            self.errors.append(f"Unsupported image type: {ext}")
            return False
        if not os.path.exists(self.file_path):
            self.errors.append("File not found")
            return False
        return True

    def parse(self) -> List[Dict[str, Any]]:
        records = []
        try:
            from PIL import Image
            from PIL.ExifTags import TAGS
            img = Image.open(self.file_path)
            exif_data = img._getexif() if hasattr(img, '_getexif') else {}
            
            record = {
                "filename": os.path.basename(self.file_path),
                "file_path": self.file_path,
                "image_format": img.format,
                "width": img.width,
                "height": img.height,
                "timestamp": "",
                "gps_latitude": None,
                "gps_longitude": None
            }

            if exif_data:
                for tag_id, value in exif_data.items():
                    tag_name = TAGS.get(tag_id, tag_id)
                    if tag_name == "DateTime":
                        record["timestamp"] = str(value)
                    elif tag_name == "GPSInfo":
                        try:
                            gps_data = value
                            lat = self._convert_to_degrees(gps_data[2])
                            lon = self._convert_to_degrees(gps_data[4])
                            record["gps_latitude"] = lat
                            record["gps_longitude"] = lon
                        except:
                            pass
            
            records.append(record)
        except Exception as e:
            self.warnings.append(f"Could not read image metadata: {str(e)}")
        
        return records

    def _convert_to_degrees(self, value):
        try:
            d, m, s = value
            return d + (m / 60.0) + (s / 3600.0)
        except:
            return None

    def extract_entities(self, records: List[Dict]) -> List[Dict]:
        entities = []
        for r in records:
            if r.get("gps_latitude") and r.get("gps_longitude"):
                entities.append({
                    "type": "location",
                    "value": f"{r['gps_latitude']},{r['gps_longitude']}",
                    "first_seen": r.get("timestamp", ""),
                    "last_seen": r.get("timestamp", ""),
                    "call_count": 1,
                    "imei_list": [],
                    "imsi_list": [],
                    "locations": [r["filename"]]
                })
        return entities

    def generate_events(self, records: List[Dict]) -> List[Dict]:
        events = []
        for r in records:
            events.append({
                "event_type": "IMAGE_CAPTURED",
                "timestamp": r.get("timestamp", ""),
                "source_entity": r["filename"],
                "target_entity": f"{r.get('gps_latitude', '')},{r.get('gps_longitude', '')}" if r.get("gps_latitude") else "",
                "direction": "CAPTURE",
                "duration_seconds": 0,
                "location": f"{r.get('gps_latitude', '')},{r.get('gps_longitude', '')}" if r.get("gps_latitude") else "",
                "cell_id": "",
                "imei": "",
                "evidence_id": self.evidence_id,
                "case_id": self.case_id
            })
        return events