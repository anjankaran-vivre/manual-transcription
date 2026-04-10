import eventlet
from app.config import settings
from app.models.call_tracker import call_tracker
from app.services.audio_service import AudioService
from app.services.groq_service import GroqService
from app.services.zoho_service import ZohoService
from app.services.email_service import EmailService
from app.logging.db_logger import DBLogger
from app.logging.log_streamer import log_streamer


def process_call(job, worker_id):
    """Process a single call transcription job"""
    call_id = job["callId"]
    rec_url = job["recUrl"]
    start_time = eventlet.hubs.get_hub().clock()
    audio_file = None
    total_api_calls = 0
    
    if not call_tracker.try_acquire(call_id):
        log_streamer.info("Worker", f"Worker {worker_id}: Call {call_id} already processing/skipped")
        return
    
    log_streamer.info("Worker", f"Worker {worker_id}: STARTED → Call {call_id}")
    eventlet.sleep(settings.PROCESS_DELAY)  # Respect delay

    try:
        # 1. Download Audio
        audio_file, success, error_msg = AudioService.download_audio(rec_url, call_id, worker_id)
        if not success:
            DBLogger.log_call(call_id, worker_id, "download_failed", error_msg=error_msg)
            EmailService.send_failure_alert(call_id, error_msg, "Download Failed")
            call_tracker.mark_completed(call_id, success=False)
            return

        # 2. Transcribe with Groq (bulletproof version)
        transcript, status, raw_transcript, api_calls = GroqService.transcribe_audio(audio_file, call_id)
        total_api_calls += api_calls

        # 3. Default values
        audio_quality = "good"
        summary_generated = False
        summary = ""

        # 4. Generate Summary based on status
        if status == "success" and len(transcript.split()) >= 10:
            summary, summary_generated = GroqService.generate_summary(transcript, call_id)
            if summary_generated:
                total_api_calls += 1
        elif status == "success":
            summary = "PURPOSE: Brief conversation\nOUTCOME: Limited content for summary"
        elif status == "no_speech":
            transcript = "No clear speech detected in recording"
            summary = "PURPOSE: No speech detected\nOUTCOME: Recording appears silent or empty"
            audio_quality = "silent"
        elif status == "unclear_audio":
            transcript = "No clear speech detected in recording"
            summary = "PURPOSE: Audio quality too poor\nOUTCOME: Transcription not possible"
            audio_quality = "unclear"
        else:  # error
            transcript = "Transcription unavailable due to technical issue"
            summary = "PURPOSE: Processing failed\nOUTCOME: Please check manually"
            audio_quality = "error"
            EmailService.send_failure_alert(call_id, f"Transcription failed: {status}", "Processing Error")

        # 5. Update Zoho CRM
        zoho_success = ZohoService.update_call(call_id, transcript, summary)
        if not zoho_success:
            log_streamer.warning("Worker", f"Call {call_id}: Zoho update failed (but transcription ok)")

        # 6. Log to CSV
        duration = eventlet.hubs.get_hub().clock() - start_time
        word_count = len(transcript.split()) if "No clear speech" not in transcript and "unavailable" not in transcript.lower() else 0

        DBLogger.log_call(
            call_id=call_id,
            worker_id=worker_id,
            status=status,
            duration=duration,
            word_count=word_count,
            audio_quality=audio_quality,
            summary_generated=summary_generated,
            api_calls=total_api_calls,
            transcription=transcript[:1000],  # avoid huge logs
            summary=summary
        )

        call_tracker.mark_completed(call_id, success=True)
        log_streamer.info("Worker", f"Worker {worker_id}: SUCCESS → Call {call_id} | {duration:.1f}s | {word_count} words")

    except Exception as e:
        log_streamer.error("Worker", f"Worker {worker_id}: FATAL ERROR → Call {call_id} | {e}")
        DBLogger.log_call(call_id, worker_id, "error", error_msg=str(e))
        EmailService.send_failure_alert(call_id, str(e), "Critical Processing Error")
        call_tracker.mark_completed(call_id, success=False)

    finally:
        # Always clean up temp file
        if audio_file:
            AudioService.cleanup_audio(audio_file)