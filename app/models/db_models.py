from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, UniqueConstraint
from app.database.connection import Base

class CallLog(Base):
    __tablename__ = "call_logs"
    __table_args__ = (
        UniqueConstraint('call_id', name='uq_call_id'),
    )

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, nullable=False)
    call_id = Column(String(255), nullable=False, index=True, unique=True)
    worker_id = Column(Integer, nullable=False)
    status = Column(String(50), nullable=False)
    duration_sec = Column(Float, nullable=False)
    word_count = Column(Integer, nullable=False)
    audio_quality = Column(String(50), nullable=False)
    summary_generated = Column(Boolean, nullable=False)
    api_calls = Column(Integer, nullable=False)
    transcription = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)

class SystemLog(Base):
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, nullable=False)
    level = Column(String(50), nullable=False)
    thread_id = Column(String(255), nullable=True)
    component = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)