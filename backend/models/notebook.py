from sqlalchemy import Column, String, DateTime, Text, Integer, ForeignKey, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.postgres import Base

class NotebookEntry(Base):
    __tablename__ = "notebook_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False)
    entry_type = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text)
    entities_linked = Column(JSON, default=[])
    evidence_linked = Column(JSON, default=[])
    graph_nodes_linked = Column(JSON, default=[])
    status = Column(String(50), default="PENDING")
    confidence = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String(100))
    is_pinned = Column(Boolean, default=False)