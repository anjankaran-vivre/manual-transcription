"""Transcription controller with validation."""

from app import task_queue
from app.models.call_tracker import call_tracker
from app.services.zoho_service import ZohoService
from app.logging.log_streamer import log_streamer
from app.controllers.schemas import TranscriptionRequest, TranscriptionResponse


class TranscriptionController:
    """Controller for transcription operations."""

    @staticmethod
    async def handle_oauth_callback(code: str = None) -> dict:
        """
        Handle OAuth callback from Zoho.
        
        Args:
            code: OAuth authorization code
            
        Returns:
            dict: Success or error message
        """
        if code:
            try:
                ZohoService.generate_access_token(code)
                log_streamer.info("OAuth", f"Tokens saved successfully")
                return {"message": "Tokens saved successfully!"}
            except Exception as e:
                log_streamer.error("OAuth", f"OAuth error: {e}")
                raise
        return {"message": "Send POST with callId and recUrl"}

    @staticmethod
    async def submit_transcription(request: TranscriptionRequest) -> TranscriptionResponse:
        """
        Submit a call for transcription.
        
        Args:
            request: TranscriptionRequest with callId and recUrl
            
        Returns:
            TranscriptionResponse: Status and queue position
            
        Raises:
            ValueError: If call is already processing or completed
            HTTPException: If validation fails
        """
        call_id = request.callId
        rec_url = request.recUrl

        # Check if already processing or completed
        if call_tracker.is_processing(call_id):
            log_streamer.info("API", f"Call {call_id} already processing")
            return TranscriptionResponse(status="already_processing", callId=call_id)
        
        if call_tracker.is_completed(call_id):
            log_streamer.info("API", f"Call {call_id} already completed")
            return TranscriptionResponse(status="already_completed", callId=call_id)

        # Add to queue - ASYNC put
        await task_queue.put({"callId": call_id, "recUrl": rec_url})
        log_streamer.info("API", f"Call {call_id} queued for processing")
        
        return TranscriptionResponse(
            status="queued",
            callId=call_id,
            queuePosition=task_queue.qsize()
        )
