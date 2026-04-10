import eventlet
from datetime import datetime


class CallTracker:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance
    
    def _init(self):
        self._lock = eventlet.semaphore.Semaphore()
        self.processing = set()
        self.completed = set()
        self.failed = set()
        self.start_time = datetime.now()
    
    def try_acquire(self, call_id):
        with self._lock:
            if call_id in self.processing or call_id in self.completed:
                return False
            self.processing.add(call_id)
            return True
    
    def mark_completed(self, call_id, success=True):
        with self._lock:
            self.processing.discard(call_id)
            if success:
                self.completed.add(call_id)
            else:
                self.failed.add(call_id)
    
    def is_processing(self, call_id):
        with self._lock:
            return call_id in self.processing
    
    def is_completed(self, call_id):
        with self._lock:
            return call_id in self.completed
    
    def get_stats(self):
        with self._lock:
            return {
                "processing": len(self.processing),
                "completed": len(self.completed),
                "failed": len(self.failed),
                "processing_ids": list(self.processing)
            }
    
    def get_uptime(self):
        delta = datetime.now() - self.start_time
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


call_tracker = CallTracker()