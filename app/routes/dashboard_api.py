"""Dashboard routes."""

from fastapi import APIRouter, HTTPException, Query
from app.controllers.dashboard import DashboardController
from app.controllers.schemas import StatusResponse, MetricsResponse

router = APIRouter()

@router.get("/status", response_model=StatusResponse)
async def get_status():
    """Get overall server status"""
    try:
        return await DashboardController.get_server_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """Get all metrics for dashboard"""
    try:
        return await DashboardController.get_metrics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/calls")
async def get_calls(limit: int = Query(50, ge=1, le=1000)):
    """Get recent call logs"""
    try:
        calls = await DashboardController.get_calls(limit)
        return {"calls": calls, "total": len(calls)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/logs")
async def get_logs(limit: int = Query(100, ge=1, le=1000)):
    """Get recent system logs"""
    try:
        logs = await DashboardController.get_logs(limit)
        return {"logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/processing")
async def get_processing():
    """Get currently processing calls"""
    try:
        stats = await DashboardController.get_processing_stats()
        return {
            "processing": stats["processing_ids"],
            "count": stats["processing"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))