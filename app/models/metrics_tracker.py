import eventlet
from datetime import datetime, date
from collections import defaultdict


class MetricsTracker:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance
    
    def _init(self):
        self._lock = eventlet.semaphore.Semaphore()
        self.daily_api_calls = defaultdict(int)
        self.daily_tokens = defaultdict(int)
        self.minute_calls = []
        self.total_transcriptions = 0
        self.total_summaries = 0
        self.total_errors = 0
    
    def record_api_call(self, tokens_used=0, call_type="transcription"):
        with self._lock:
            today = str(date.today())
            now = datetime.now()
            
            self.daily_api_calls[today] += 1
            self.daily_tokens[today] += tokens_used
            self.minute_calls.append(now)
            
            cutoff = datetime.now().timestamp() - 60
            self.minute_calls = [t for t in self.minute_calls if t.timestamp() > cutoff]
            
            if call_type == "transcription":
                self.total_transcriptions += 1
            elif call_type == "summary":
                self.total_summaries += 1
    
    def record_error(self):
        with self._lock:
            self.total_errors += 1
    
    def get_today_stats(self):
        with self._lock:
            today = str(date.today())
            return {
                "api_calls_today": self.daily_api_calls.get(today, 0),
                "tokens_today": self.daily_tokens.get(today, 0),
                "calls_this_minute": len(self.minute_calls),
                "total_transcriptions": self.total_transcriptions,
                "total_summaries": self.total_summaries,
                "total_errors": self.total_errors
            }
    
    def get_rate_limit_status(self):
        from app.config import settings
        with self._lock:
            today = str(date.today())
            daily_used = self.daily_api_calls.get(today, 0)
            minute_used = len(self.minute_calls)
            
            return {
                "daily_used": daily_used,
                "daily_limit": settings.GROQ_DAILY_LIMIT,
                "daily_percentage": round((daily_used / max(settings.GROQ_DAILY_LIMIT, 1)) * 100, 2),
                "minute_used": minute_used,
                "minute_limit": settings.GROQ_MINUTE_LIMIT,
                "minute_percentage": round((minute_used / max(settings.GROQ_MINUTE_LIMIT, 1)) * 100, 2)
            }


metrics_tracker = MetricsTracker()