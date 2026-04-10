from fastapi import APIRouter, HTTPException
from app.controllers.admin import AdminController
from app.controllers.schemas import AdminResponse

router = APIRouter()

@router.post("/restart", response_model=AdminResponse)
async def restart_server():
    """Restart the server process"""
    try:
        return await AdminController.restart_server()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stop", response_model=AdminResponse)
async def stop_server():
    """Stop the server"""
    try:
        return await AdminController.stop_server()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/clear-queue", response_model=AdminResponse)
async def clear_queue():
    """Clear the task queue"""
    try:
        return await AdminController.clear_queue()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test-email", response_model=AdminResponse)
async def test_email():
    """Send test email"""
    try:
        return await AdminController.test_email()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))