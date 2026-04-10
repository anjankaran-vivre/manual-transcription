"""
Socket.IO handler for real-time log streaming and live terminal
"""

from socketio import AsyncServer
from socketio.asgi import ASGIApp
from app.logging.log_streamer import log_streamer
from app.logging.db_logger import DBLogger

# Create Socket.IO server
sio = AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
    ping_timeout=60,
    ping_interval=25,
)


@sio.event
async def connect(sid, environ):
    """Handle client connection"""
    print(f"[SocketIO] Client connected: {sid}")
    log_streamer.info("SocketIO", f"Client {sid} connected")


@sio.event
async def disconnect(sid):
    """Handle client disconnection"""
    print(f"[SocketIO] Client disconnected: {sid}")
    log_streamer.info("SocketIO", f"Client {sid} disconnected")


@sio.event
async def request_logs(sid):
    """Send recent logs to connected client"""
    try:
        print(f"[SocketIO] Client {sid} requested logs")
        logs = DBLogger.get_recent_logs(50)
        
        # Format logs for frontend
        formatted_logs = []
        for log in logs:
            formatted_logs.append({
                "timestamp": log.get("timestamp", ""),
                "level": log.get("level", ""),
                "component": log.get("component", ""),
                "message": log.get("message", ""),
            })
        
        # Send to client
        await sio.emit('log_history', formatted_logs, to=sid)
        print(f"[SocketIO] Sent {len(formatted_logs)} logs to {sid}")
    except Exception as e:
        print(f"[SocketIO] Error sending logs: {e}")
        import traceback
        traceback.print_exc()


async def broadcast_log(level, component, message):
    """Broadcast a new log message to all connected clients"""
    try:
        log_data = {
            "timestamp": str(__import__('datetime').datetime.now().isoformat()),
            "level": level,
            "component": component,
            "message": message,
        }
        await sio.emit('log_message', log_data)
    except Exception as e:
        print(f"[SocketIO] Error broadcasting log: {e}")
