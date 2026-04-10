"""Pydantic models for request/response validation."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ============================================================
# Transcription Schemas
# ============================================================
class TranscriptionRequest(BaseModel):
    """Request model for transcription endpoint."""
    callId: str = Field(..., min_length=1, description="Call ID")
    recUrl: str = Field(..., min_length=1, description="Recording URL")

    class Config:
        json_schema_extra = {
            "example": {
                "callId": "CALL_001",
                "recUrl": "https://example.com/recording.wav"
            }
        }


class TranscriptionResponse(BaseModel):
    """Response model for transcription endpoint."""
    status: str = Field(..., description="Status: queued, already_processing, already_completed")
    callId: str = Field(..., description="Call ID")
    queuePosition: Optional[int] = Field(None, description="Position in queue")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "queued",
                "callId": "CALL_001",
                "queuePosition": 5
            }
        }


# ============================================================
# Status & Metrics Schemas
# ============================================================
class StatusResponse(BaseModel):
    """Response model for server status."""
    status: str = Field(..., description="Server status")
    uptime: str = Field(..., description="Server uptime")
    workers: int = Field(..., description="Number of workers")
    queue_size: int = Field(..., description="Current queue size")
    memory_mb: float = Field(..., description="Memory usage in MB")
    cpu_percent: float = Field(..., description="CPU usage percent")
    pid: int = Field(..., description="Process ID")


class MetricsResponse(BaseModel):
    """Response model for metrics."""
    realtime: dict = Field(..., description="Real-time statistics")
    historical: dict = Field(..., description="Historical statistics")
    today: dict = Field(..., description="Today's statistics")
    rate_limit: dict = Field(..., description="Rate limit status")


# ============================================================
# Admin Schemas
# ============================================================
class AdminResponse(BaseModel):
    """Response model for admin endpoints."""
    status: str = Field(..., description="Operation status")
    message: str = Field(..., description="Status message")
    cleared: Optional[int] = Field(None, description="Number of items cleared")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "Operation completed successfully"
            }
        }


# ============================================================
# Database Models (Pydantic - for ORM mapping)
# ============================================================
class CallLogBase(BaseModel):
    """Base model for CallLog."""
    call_id: str
    worker_id: int
    status: str
    duration_sec: float
    word_count: int
    audio_quality: str
    summary_generated: bool
    api_calls: int
    transcription: Optional[str] = None
    summary: Optional[str] = None
    error_message: Optional[str] = None


class CallLogCreate(CallLogBase):
    """Model for creating CallLog."""
    pass


class CallLog(CallLogBase):
    """Model for reading CallLog."""
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True


class SystemLogBase(BaseModel):
    """Base model for SystemLog."""
    level: str
    thread_id: Optional[str] = None
    component: str
    message: str


class SystemLogCreate(SystemLogBase):
    """Model for creating SystemLog."""
    pass


class SystemLog(SystemLogBase):
    """Model for reading SystemLog."""
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True
