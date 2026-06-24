from sqlalchemy import Column, String, DateTime, Text, Integer, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
import enum
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.postgres import Base

class EvidenceType(str, enum.Enum):
    CDR = "cdr"
    IPDR = "ipdr"
    GPS = "gps"
    BROWSER = "browser"
    WIFI = "wifi"
    BLUETOOTH = "bluetooth"
    FINANCIAL = "financial"
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    IMAGE = "image"
    IOT = "iot"
    PDF = "pdf"
    MANUAL = "manual"
    UNKNOWN = "unknown"

class EvidenceStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    VALIDATED = "validated"
    PARSING = "parsing"
    PARSED = "parsed"
    FAILED = "failed"

class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False)
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size_bytes = Column(Integer)
    file_hash_sha256 = Column(String(64), nullable=False)
    evidence_type = Column(Enum(EvidenceType), default=EvidenceType.UNKNOWN)
    status = Column(Enum(EvidenceStatus), default=EvidenceStatus.UPLOADED)
    source_description = Column(Text)
    uploaded_by = Column(String(100))
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    parsed_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text)