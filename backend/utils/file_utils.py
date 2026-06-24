import os
import shutil
import hashlib
from pathlib import Path

ALLOWED_EXTENSIONS = {
    ".csv", ".xlsx", ".xls", ".json", ".db", ".sqlite",
    ".txt", ".log", ".xml", ".jpg", ".jpeg", ".png",
    ".pdf", ".zip", ".7z"
}

def get_file_extension(filename: str) -> str:
    return Path(filename).suffix.lower()

def is_allowed_file(filename: str) -> bool:
    return get_file_extension(filename) in ALLOWED_EXTENSIONS

def compute_sha256(file_path: str) -> str:
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def detect_evidence_type(filename: str) -> str:
    name = filename.lower()
    if any(x in name for x in ["cdr", "call", "sms"]):
        return "cdr"
    elif any(x in name for x in ["ipdr", "internet", "data_record"]):
        return "ipdr"
    elif any(x in name for x in ["gps", "location", "track"]):
        return "gps"
    elif any(x in name for x in ["browser", "history", "chrome", "firefox"]):
        return "browser"
    elif any(x in name for x in ["wifi", "wi_fi", "wireless"]):
        return "wifi"
    elif any(x in name for x in ["bluetooth", "bt_"]):
        return "bluetooth"
    elif any(x in name for x in ["bank", "transaction", "financial", "account"]):
        return "financial"
    elif any(x in name for x in ["email", "mail", "outlook"]):
        return "email"
    elif any(x in name for x in ["whatsapp", "wa_", "chat"]):
        return "whatsapp"
    elif any(x in name for x in ["iot", "device", "sensor"]):
        return "iot"
    elif get_file_extension(filename) in [".jpg", ".jpeg", ".png"]:
        return "image"
    elif get_file_extension(filename) == ".pdf":
        return "pdf"
    else:
        return "unknown"

def save_uploaded_file(file_content: bytes, destination: str) -> None:
    os.makedirs(os.path.dirname(destination), exist_ok=True)
    with open(destination, "wb") as f:
        f.write(file_content)

def get_file_size(file_path: str) -> int:
    return os.path.getsize(file_path)