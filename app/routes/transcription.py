"""Transcription routes."""

from fastapi import APIRouter, HTTPException, Form
from app.controllers.transcription import TranscriptionController
from app.controllers.schemas import TranscriptionRequest, TranscriptionResponse

router = APIRouter()

@router.get("/server_transcription")
async def server_transcription_get(code: str = None):
    """Handle OAuth callback"""
    try:
        return await TranscriptionController.handle_oauth_callback(code)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/server_transcription", response_model=TranscriptionResponse)
async def server_transcription_post(callId: str = Form(...), recUrl: str = Form(...)):
    """Main endpoint for receiving transcription requests (accepts form data)"""
    try:
        request = TranscriptionRequest(callId=callId, recUrl=recUrl)
        return await TranscriptionController.submit_transcription(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}