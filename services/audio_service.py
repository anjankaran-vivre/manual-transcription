"""
Simplified Audio Service for Streamlit
- Download audio from URL
- Basic cleanup
"""

import os
import tempfile
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

load_dotenv()

class AudioService:
    """Streamlit-optimized Audio Service"""
    
    MAX_RETRIES = 3
    RETRY_INTERVAL = 2
    
    @staticmethod
    def download_audio(rec_url, call_id, worker_id=1):
        """
        Download audio from URL
        Returns: (audio_file_path, success, error_message)
        """
        audio_file = None
        
        # Get credentials from environment if needed
        username = os.getenv("AUDIO_USERNAME")
        password = os.getenv("AUDIO_PASSWORD")
        
        for attempt in range(1, AudioService.MAX_RETRIES + 2):
            try:
                auth = None
                if username and password:
                    auth = HTTPBasicAuth(username, password)
                
                # Download with timeout
                resp = requests.get(
                    rec_url,
                    stream=True,
                    auth=auth,
                    timeout=120
                )
                resp.raise_for_status()
                
                # Save to temporary file
                with tempfile.NamedTemporaryFile(suffix=".m4a", delete=False) as f:
                    for chunk in resp.iter_content(8192):
                        if chunk:
                            f.write(chunk)
                    audio_file = f.name
                
                file_size = os.path.getsize(audio_file)
                
                if file_size < 100:
                    os.remove(audio_file)
                    raise Exception("Downloaded file too small")
                
                return audio_file, True, None
            
            except requests.Timeout:
                error_msg = "Download timeout"
            except requests.RequestException as e:
                error_msg = str(e)
            except Exception as e:
                error_msg = str(e)
            
            # Cleanup on error
            if audio_file and os.path.exists(audio_file):
                try:
                    os.remove(audio_file)
                except:
                    pass
                audio_file = None
            
            if attempt < AudioService.MAX_RETRIES:
                import time
                time.sleep(AudioService.RETRY_INTERVAL)
        
        return None, False, error_msg
    
    @staticmethod
    def cleanup_audio(audio_file):
        """Delete audio file"""
        if audio_file and os.path.exists(audio_file):
            try:
                os.remove(audio_file)
                return True
            except Exception as e:
                return False
        return True
