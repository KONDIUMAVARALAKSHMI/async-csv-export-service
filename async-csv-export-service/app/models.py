from sqlalchemy import Column, String, DateTime, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    signup_date = Column(DateTime(timezone=True), default=datetime.utcnow)
    country_code = Column(String(2), nullable=False)
    subscription_tier = Column(String(50), default='free')
    lifetime_value = Column(Numeric(10, 2), default=0.00)

class Export(Base):
    __tablename__ = "exports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status = Column(String, nullable=False) # pending, processing, completed, failed, cancelled
    total_rows = Column(Integer, default=0)
    processed_rows = Column(Integer, default=0)
    percentage = Column(Integer, default=0)
    error = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    file_path = Column(String, nullable=True)
    
    # Storage for filters and options
    filters = Column(String, nullable=True) 
    columns = Column(String, nullable=True)