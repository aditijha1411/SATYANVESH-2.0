from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.postgres import Base

class Relationship(Base):
    __tablename__ = "relationships"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False)
    source_entity = Column(String(255), nullable=False)
    target_entity = Column(String(255), nullable=False)
    relationship_type = Column(String(100), nullable=False)
    weight = Column(Integer, default=1)
    evidence_refs = Column(JSON, default=[])
    created_at = Column(DateTime(timezone=True), server_default=func.now())