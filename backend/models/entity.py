from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.postgres import Base

class Entity(Base):
    __tablename__ = "entities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False)
    evidence_id = Column(UUID(as_uuid=True), ForeignKey("evidence.id"), nullable=True)
    entity_type = Column(String(50), nullable=False)
    value = Column(String(255), nullable=False)
    label = Column(String(255))
    first_seen = Column(String(100))
    last_seen = Column(String(100))
    call_count = Column(Integer, default=0)
    imei_list = Column(JSON, default=[])
    imsi_list = Column(JSON, default=[])
    locations = Column(JSON, default=[])
    extra_data = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())