"""
Minimal FastAPI server to handle Zoho OAuth redirect and save token.
Not meant to be run directly — imported and started as a thread by main.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from app.services.zoho_service import ZohoService

app = FastAPI()

SUCCESS_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Token Saved</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center;
               padding: 50px; background: #f0f2f5; }
        .box { background: white; padding: 40px; border-radius: 8px;
               max-width: 480px; margin: auto; box-shadow: 0 2px 8px rgba(0,0,0,.1); }
        h2  { color: #28a745; }
        p   { color: #555; line-height: 1.6; }
        a   { color: #007bff; font-weight: bold; text-decoration: none; }
    </style>
</head>
<body>
    <div class="box">
        <h2>✅ Token Saved!</h2>
        <p>
            Your Zoho account is now connected.<br><br>
            Go back to
            <a href="http://localhost:8501" target="_blank">Streamlit</a>,
            refresh the page, and you should see
            <strong>✅ Token Saved</strong> in the sidebar.
        </p>
    </div>
</body>
</html>
"""

ERROR_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Auth Failed</title>
    <style>
        body {{ font-family: Arial, sans-serif; text-align: center;
                padding: 50px; background: #f0f2f5; }}
        .box {{ background: white; padding: 40px; border-radius: 8px;
                max-width: 480px; margin: auto; box-shadow: 0 2px 8px rgba(0,0,0,.1); }}
        h2  {{ color: #dc3545; }}
        pre {{ background: #ffe7e7; padding: 12px; border-radius: 4px;
               text-align: left; font-size: 12px; color: #721c24; white-space: pre-wrap; }}
        a   {{ color: #007bff; font-weight: bold; text-decoration: none; }}
    </style>
</head>
<body>
    <div class="box">
        <h2>❌ Authorization Failed</h2>
        <pre>{detail}</pre>
        <p><a href="http://localhost:8501">← Back to Streamlit</a></p>
    </div>
</body>
</html>
"""


@app.get("/auth", response_class=HTMLResponse)
async def zoho_callback(code: str = None, error: str = None, error_uri: str = None):
    if error:
        return ERROR_HTML.format(detail=f"Zoho error: {error}\n{error_uri or ''}")
    if not code:
        return ERROR_HTML.format(detail="No authorization code received from Zoho.")
    _, err = ZohoService.generate_access_token(code)
    if err:
        return ERROR_HTML.format(detail=f"Token exchange failed:\n{err}")
    return SUCCESS_HTML


@app.get("/health")
async def health():
    return {"status": "ok"}