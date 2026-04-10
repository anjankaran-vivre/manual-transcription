"""Admin controller with validation."""

import os
import sys
import signal
import threading
from app.config import settings
from app.logging.log_streamer import log_streamer
from app.controllers.schemas import AdminResponse
from app.services.email_service import EmailService


class AdminController:
    """Controller for admin operations."""

    @staticmethod
    async def restart_server() -> AdminResponse:
        """
        Restart the server process.
        
        Returns:
            AdminResponse: Restart status
            
        Raises:
            Exception: If restart fails
        """
        try:
            log_streamer.info("Admin", "Server restart requested")
            
            # Schedule restart (gives time for response)
            def delayed_restart():
                import time
                time.sleep(2)
                os.kill(os.getpid(), signal.SIGTERM)
            
            threading.Thread(target=delayed_restart, daemon=True).start()
            
            return AdminResponse(
                status="restarting",
                message="Server will restart in 2 seconds"
            )
            
        except Exception as e:
            log_streamer.error("Admin", f"Restart failed: {e}")
            raise

    @staticmethod
    async def stop_server() -> AdminResponse:
        """
        Stop the server.
        
        Returns:
            AdminResponse: Stop status
            
        Raises:
            Exception: If stop fails
        """
        try:
            log_streamer.info("Admin", "Server stop requested")
            
            def delayed_stop():
                import time
                time.sleep(1)
                os.kill(os.getpid(), signal.SIGTERM)
            
            threading.Thread(target=delayed_stop, daemon=True).start()
            
            return AdminResponse(
                status="stopping",
                message="Server will stop in 1 second"
            )
            
        except Exception as e:
            log_streamer.error("Admin", f"Stop failed: {e}")
            raise

    @staticmethod
    async def clear_queue() -> AdminResponse:
        """
        Clear the task queue.
        
        Returns:
            AdminResponse: Queue clear status with count
            
        Raises:
            Exception: If clear fails
        """
        try:
            from app import task_queue
            cleared = 0
            while not task_queue.empty():
                try:
                    task_queue.get_nowait()
                    cleared += 1
                except:
                    break
            
            log_streamer.info("Admin", f"Queue cleared: {cleared} items removed")
            return AdminResponse(
                status="success",
                message=f"Cleared {cleared} items from queue",
                cleared=cleared
            )
            
        except Exception as e:
            log_streamer.error("Admin", f"Clear queue failed: {e}")
            raise

    @staticmethod
    async def test_email() -> AdminResponse:
        """
        Send test email.
        
        Returns:
            AdminResponse: Test status
            
        Raises:
            Exception: If email send fails
        """
        try:
            EmailService.send_alert(
                "Test Alert",
                "This is a test email from the Transcription Server dashboard."
            )
            return AdminResponse(
                status="success",
                message="Test email sent"
            )
        except Exception as e:
            log_streamer.error("Admin", f"Test email failed: {e}")
            raise
