"""Dashboard controller with validation."""

import psutil
import os
from app import task_queue
from app.models.call_tracker import call_tracker
from app.models.metrics_tracker import metrics_tracker
from app.logging.db_logger import DBLogger
from app.logging.log_streamer import log_streamer
from app.config import settings
from app.controllers.schemas import StatusResponse, MetricsResponse


class DashboardController:
    """Controller for dashboard operations."""

    @staticmethod
    async def get_server_status() -> StatusResponse:
        """
        Get current server status.
        
        Returns:
            StatusResponse: Server status information
            
        Raises:
            Exception: If unable to get process info
        """
        try:
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            
            return StatusResponse(
                status="running",
                uptime=call_tracker.get_uptime(),
                workers=settings.NUM_WORKERS,
                queue_size=task_queue.qsize(),
                memory_mb=round(memory_info.rss / 1024 / 1024, 2),
                cpu_percent=process.cpu_percent(),
                pid=os.getpid()
            )
        except Exception as e:
            log_streamer.error("Dashboard", f"Error getting status: {e}")
            raise

    @staticmethod
    async def get_metrics() -> MetricsResponse:
        """
        Get all metrics for dashboard.
        
        Returns:
            MetricsResponse: All metrics (real-time, historical, today, rate-limit)
            
        Raises:
            Exception: If unable to fetch metrics
        """
        try:
            call_stats = call_tracker.get_stats()
            db_stats = DBLogger.get_stats_from_logs()
            today_stats = metrics_tracker.get_today_stats()
            rate_limit = metrics_tracker.get_rate_limit_status()
            
            return MetricsResponse(
                realtime=call_stats,
                historical=db_stats,
                today=today_stats,
                rate_limit=rate_limit
            )
        except Exception as e:
            log_streamer.error("Dashboard", f"Metrics error: {e}")
            raise

    @staticmethod
    async def get_calls(limit: int = 50) -> list:
        """
        Get recent call logs from database.
        
        Args:
            limit: Maximum number of calls to return
            
        Returns:
            list: Call log records
        """
        try:
            calls = DBLogger.get_recent_calls(limit)
            return calls if calls else []
        except Exception as e:
            log_streamer.error("Dashboard", f"Error fetching calls: {e}")
            return []

    @staticmethod
    async def get_logs(limit: int = 100) -> list:
        """
        Get recent system logs from database.
        
        Args:
            limit: Maximum number of logs to return
            
        Returns:
            list: System log records
        """
        try:
            logs = DBLogger.get_recent_logs(limit)
            return logs if logs else []
        except Exception as e:
            log_streamer.error("Dashboard", f"Error fetching logs: {e}")
            return []

    @staticmethod
    async def get_processing_stats() -> dict:
        """
        Get current processing statistics.
        
        Returns:
            dict: Processing stats including processing_ids and count
        """
        try:
            stats = call_tracker.get_stats()
            return {
                "processing_ids": stats.get("processing_ids", []),
                "processing": stats.get("processing", 0)
            }
        except Exception as e:
            log_streamer.error("Dashboard", f"Error fetching processing stats: {e}")
            return {"processing_ids": [], "processing": 0}
