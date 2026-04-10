"""
FastAPI App Factory with Socket.IO Integration
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from contextlib import asynccontextmanager
from socketio.asgi import ASGIApp
from app.socketio_handler import sio

# Task queue (initialized in create_app)
task_queue = None

# Placeholder for WebSocket manager (will implement later)
websocket_manager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """App lifespan - manages background tasks"""
    from app.background_tasks import process_tasks_loop
    
    print("\n" + "="*60)
    print("🟢 STARTING BACKGROUND TASK PROCESSOR")
    print("="*60)
    
    # Startup - create background task
    task_processor = asyncio.create_task(process_tasks_loop(task_queue))
    
    yield
    
    # Shutdown
    print("\n" + "="*60)
    print("🔴 STOPPING BACKGROUND TASK PROCESSOR")
    print("="*60)
    task_processor.cancel()
    try:
        await task_processor
    except asyncio.CancelledError:
        pass


def create_app():
    global task_queue
    
    # Create FastAPI app
    app = FastAPI(
        title="Transcription Server",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # Initialize asyncio queue for background tasks
    task_queue = asyncio.Queue()
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    from app.routes.transcription import router as transcription_router
    from app.routes.dashboard_api import router as dashboard_router
    from app.routes.admin import router as admin_router
    
    app.include_router(transcription_router)
    app.include_router(dashboard_router, prefix="/api")
    app.include_router(admin_router, prefix="/admin")
    
    from app.logging.db_logger import DBLogger
    DBLogger.init_db()
    
    # Wrap FastAPI with Socket.IO ASGI app
    asgi_app = ASGIApp(sio, app)
    
    return app, asgi_app