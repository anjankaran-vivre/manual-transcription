import eventlet
from datetime import datetime
from collections import deque


class LogStreamer:
    _instance = None
    MAX_BUFFER_SIZE = 500
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance
    
    def _init(self):
        self.buffer = deque(maxlen=self.MAX_BUFFER_SIZE)
        self._lock = eventlet.semaphore.Semaphore()
    
    def log(self, level, component, message):
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        log_entry = {
            "timestamp": timestamp,
            "level": level,
            "component": component,
            "message": message
        }
        
        with self._lock:
            self.buffer.append(log_entry)
        
        # Broadcast to Socket.IO clients
        try:
            from app.socketio_handler import broadcast_log
            import asyncio
            try:
                asyncio.get_running_loop()
                asyncio.create_task(broadcast_log(level, component, message))
            except RuntimeError:
                # No event loop running in this context, skip broadcasting
                pass
        except Exception as e:
            pass
        
        # Log to DB
        try:
            from app.logging.db_logger import DBLogger
            DBLogger.log_system(level, component, message)
        except:
            pass
        
        print(f"[{timestamp}] [{level}] [{component}] {message}")
    
    def info(self, component, message):
        self.log("INFO", component, message)
    
    def error(self, component, message):
        self.log("ERROR", component, message)
    
    def warning(self, component, message):
        self.log("WARNING", component, message)
    
    def debug(self, component, message):
        self.log("DEBUG", component, message)
    
    def get_recent_logs(self, count=100):
        with self._lock:
            return list(self.buffer)[-count:]


log_streamer = LogStreamer()