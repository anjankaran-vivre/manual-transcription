
import os
import sys
import threading
import subprocess
import uvicorn
from dotenv import load_dotenv

load_dotenv()


def start_auth_server():
    """Start FastAPI OAuth callback server on port 5000 (background thread)."""
    from auth_server import app  # local import so path is already set up
    port = int(os.getenv("AUTH_SERVER_PORT", 5000))
    print(f"[auth-server] Listening on http://localhost:{port}/auth")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="error")


if __name__ == "__main__":
    # 1. Auth server in background daemon thread
    t = threading.Thread(target=start_auth_server, daemon=True)
    t.start()

    # 2. Streamlit in foreground — blocks until user hits Ctrl+C
    print("[streamlit]   Starting on http://localhost:8501")
    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", "app.py",
         "--server.port", "8501"],
        cwd=os.path.dirname(os.path.abspath(__file__)),
    )