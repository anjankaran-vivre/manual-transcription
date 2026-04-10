import eventlet
import os
import tempfile
import requests
from requests.auth import HTTPBasicAuth
from app.config import settings
from app.logging.log_streamer import log_streamer


class AudioService:
    @staticmethod
    def download_audio(rec_url, call_id, worker_id):
        audio_file = None
        
        for attempt in range(1, settings.MAX_DOWNLOAD_RETRIES + 2):
            try:
                log_streamer.info("AudioService", 
                    f"Worker {worker_id}: Downloading call {call_id} (Attempt {attempt})")
                
                auth = HTTPBasicAuth(settings.AUDIO_USERNAME, settings.AUDIO_PASSWORD)
                
                with eventlet.Timeout(120):
                    resp = requests.get(rec_url, stream=True, auth=auth, timeout=60)
                    resp.raise_for_status()
                    
                    with tempfile.NamedTemporaryFile(suffix=".m4a", delete=False) as f:
                        for chunk in resp.iter_content(8192):
                            f.write(chunk)
                        audio_file = f.name
                
                file_size = os.path.getsize(audio_file)
                log_streamer.info("AudioService", 
                    f"Worker {worker_id}: Download successful ({file_size} bytes)")
                
                return audio_file, True, None
                
            except eventlet.Timeout:
                error_msg = "Download timeout"
                log_streamer.error("AudioService", f"Worker {worker_id}: Timeout")
                
            except Exception as e:
                error_msg = str(e)
                log_streamer.error("AudioService", 
                    f"Worker {worker_id}: Attempt {attempt} failed: {error_msg}")
            
            if audio_file and os.path.exists(audio_file):
                try: os.remove(audio_file)
                except: pass
                audio_file = None
            
            if attempt <= settings.MAX_DOWNLOAD_RETRIES:
                eventlet.sleep(settings.RETRY_INTERVAL)
            else:
                return None, False, error_msg
        
        return None, False, "Max retries exceeded"
    
    @staticmethod
    def cleanup_audio(audio_file):
        if audio_file and os.path.exists(audio_file):
            try:
                os.remove(audio_file)
                return True
            except Exception as e:
                log_streamer.warning("AudioService", f"Cleanup failed: {e}")
                return False
        return True