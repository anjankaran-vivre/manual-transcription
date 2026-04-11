import os
import tempfile
import requests
import time
from requests.auth import HTTPBasicAuth
from app.config import settings


class AudioService:
    @staticmethod
    def download_audio(rec_url, call_id, worker_id):
        audio_file = None
        error_msg = "Max retries exceeded"

        # Strip accidental whitespace from URL (common with manual paste in UI)
        rec_url = rec_url.strip()

        for attempt in range(1, settings.MAX_DOWNLOAD_RETRIES + 2):
            try:
                auth = HTTPBasicAuth(settings.AUDIO_USERNAME, settings.AUDIO_PASSWORD)

                resp = requests.get(rec_url, stream=True, auth=auth, timeout=120)

                # Surface the actual HTTP error clearly
                if not resp.ok:
                    error_msg = (
                        f"HTTP {resp.status_code}: {resp.reason} — "
                        f"URL: {rec_url}"
                    )
                    raise requests.HTTPError(error_msg)

                with tempfile.NamedTemporaryFile(suffix=".m4a", delete=False) as f:
                    for chunk in resp.iter_content(8192):
                        f.write(chunk)
                    audio_file = f.name

                file_size = os.path.getsize(audio_file)
                if file_size == 0:
                    error_msg = "Downloaded file is empty (0 bytes)"
                    raise ValueError(error_msg)

                return audio_file, True, None

            except requests.Timeout:
                error_msg = f"Attempt {attempt}: Download timed out after 120s"

            except requests.HTTPError as e:
                # Don't retry on auth errors — they won't recover
                if resp.status_code in (401, 403):
                    return None, False, str(e)
                error_msg = str(e)

            except Exception as e:
                error_msg = f"Attempt {attempt}: {str(e)}"

            # Cleanup partial file before retry
            if audio_file and os.path.exists(audio_file):
                try:
                    os.remove(audio_file)
                except Exception:
                    pass
                audio_file = None

            if attempt <= settings.MAX_DOWNLOAD_RETRIES:
                time.sleep(settings.RETRY_INTERVAL)

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