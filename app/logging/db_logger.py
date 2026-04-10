import eventlet
from datetime import datetime
from sqlalchemy.orm import Session
from app.database.connection import db_manager
from app.models.db_models import CallLog, SystemLog


class DBLogger:
    _call_lock = eventlet.semaphore.Semaphore()
    _system_lock = eventlet.semaphore.Semaphore()
    
    @classmethod
    def init_db(cls):
        # Create tables if not exist
        db_manager.init_db()
    
    @classmethod
    def log_call(cls, call_id, worker_id, status, duration=0, word_count=0,
                 audio_quality="good", summary_generated=False, api_calls=0,
                 transcription="", summary="", error_msg=""):
        with cls._call_lock:
            db: Session = db_manager.get_session()
            try:
                # Check if call_id already exists
                existing_call = db.query(CallLog).filter(CallLog.call_id == call_id).first()
                
                if existing_call:
                    # UPDATE existing record
                    existing_call.timestamp = datetime.now()
                    existing_call.worker_id = worker_id
                    existing_call.status = status
                    existing_call.duration_sec = duration
                    existing_call.word_count = word_count
                    existing_call.audio_quality = audio_quality
                    existing_call.summary_generated = summary_generated
                    existing_call.api_calls = api_calls
                    existing_call.transcription = transcription
                    existing_call.summary = summary
                    existing_call.error_message = error_msg
                    db.commit()
                    print(f"✓ Updated call log for {call_id}")
                else:
                    # INSERT new record
                    log_entry = CallLog(
                        timestamp=datetime.now(),
                        call_id=call_id,
                        worker_id=worker_id,
                        status=status,
                        duration_sec=duration,
                        word_count=word_count,
                        audio_quality=audio_quality,
                        summary_generated=summary_generated,
                        api_calls=api_calls,
                        transcription=transcription,
                        summary=summary,
                        error_message=error_msg
                    )
                    db.add(log_entry)
                    db.commit()
                    print(f"✓ Created new call log for {call_id}")
            except Exception as e:
                db.rollback()
                print(f"Error logging call: {e}")
                import traceback
                traceback.print_exc()
            finally:
                db.close()
    
    @classmethod
    def log_system(cls, level, component, message, thread_id=None):
        with cls._system_lock:
            db: Session = db_manager.get_session()
            try:
                log_entry = SystemLog(
                    timestamp=datetime.now(),
                    level=level,
                    thread_id=thread_id or "greenlet",
                    component=component,
                    message=message.replace('\n', ' ').replace('\r', '')
                )
                db.add(log_entry)
                db.commit()
            except Exception as e:
                db.rollback()
                print(f"Error logging system: {e}")
            finally:
                db.close()
    
    @classmethod
    def get_stats_from_logs(cls):
        """Get historical stats from database logs"""
        from sqlalchemy import func, cast, Date
        from app.database.connection import db_manager
        from app.models.db_models import CallLog
        from datetime import datetime, timedelta
        
        db = db_manager.get_session()
        try:
            # Total calls
            total_calls = db.query(func.count(CallLog.id)).scalar() or 0
            
            # Successful calls
            successful_calls = db.query(func.count(CallLog.id)).filter(CallLog.status == "success").scalar() or 0
            
            # Failed calls
            failed_calls = db.query(func.count(CallLog.id)).filter(CallLog.status.in_(["error", "download_failed"])).scalar() or 0
            
            # Today's calls - use CAST for SQL Server compatibility
            today = datetime.now().date()
            today_calls = db.query(func.count(CallLog.id)).filter(cast(CallLog.timestamp, Date) == today).scalar() or 0
            
            # Average duration
            avg_duration = db.query(func.avg(CallLog.duration_sec)).filter(CallLog.duration_sec > 0).scalar() or 0
            
            # Total words
            total_words = db.query(func.sum(CallLog.word_count)).scalar() or 0
            
            # Recent calls (last 24 hours)
            yesterday = datetime.now() - timedelta(days=1)
            recent_calls = db.query(func.count(CallLog.id)).filter(CallLog.timestamp >= yesterday).scalar() or 0
            
            return {
                "total_calls": total_calls,
                "successful_calls": successful_calls,
                "failed_calls": failed_calls,
                "today_calls": today_calls,
                "avg_duration_sec": round(avg_duration, 2),
                "total_words": total_words,
                "recent_calls_24h": recent_calls
            }
        except Exception as e:
            print(f"Error getting stats: {e}")
            return {
                "total_calls": 0,
                "successful_calls": 0,
                "failed_calls": 0,
                "today_calls": 0,
                "avg_duration_sec": 0,
                "total_words": 0,
                "recent_calls_24h": 0
            }
        finally:
            db.close()
    
    @classmethod
    def get_recent_calls(cls, limit=50):
        """Get recent call logs from MSSQL database"""
        db = db_manager.get_session()
        try:
            # Query recent calls, sorted by timestamp descending
            calls = db.query(CallLog).order_by(CallLog.timestamp.desc()).limit(limit).all()
            
            # Convert to dict for JSON serialization
            result = []
            for call in calls:
                result.append({
                    "timestamp": call.timestamp.isoformat() if call.timestamp else "",
                    "call_id": call.call_id,
                    "worker_id": call.worker_id,
                    "status": call.status,
                    "duration_sec": call.duration_sec,
                    "word_count": call.word_count,
                    "audio_quality": call.audio_quality,
                    "summary_generated": call.summary_generated,
                    "api_calls": call.api_calls,
                    "transcription": call.transcription[:200] if call.transcription else "",  # First 200 chars
                    "summary": call.summary[:200] if call.summary else "",  # First 200 chars
                    "error_message": call.error_message
                })
            return result
        except Exception as e:
            print(f"Error fetching recent calls: {e}")
            import traceback
            traceback.print_exc()
            return []
        finally:
            db.close()
    
    @classmethod
    def get_recent_logs(cls, limit=100):
        """Get recent system logs from MSSQL database"""
        db = db_manager.get_session()
        try:
            # Query recent logs, sorted by timestamp descending
            logs = db.query(SystemLog).order_by(SystemLog.timestamp.desc()).limit(limit).all()
            
            # Convert to dict for JSON serialization
            result = []
            for log in logs:
                result.append({
                    "timestamp": log.timestamp.isoformat() if log.timestamp else "",
                    "level": log.level,
                    "component": log.component,
                    "message": log.message,
                    "thread_id": log.thread_id
                })
            return result
        except Exception as e:
            print(f"Error fetching recent logs: {e}")
            import traceback
            traceback.print_exc()
            return []
        finally:
            db.close()
    
    # ============================================================
    # (Duplicate CSV-based get_stats_from_logs removed - using DB version above)