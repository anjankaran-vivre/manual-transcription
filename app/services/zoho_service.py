import os
import json
import time
import requests
from app.config import settings

class ZohoService:
    @staticmethod
    def get_authorization_url():
        """Generate Zoho OAuth authorization URL"""
        if not settings.ZOHO_CLIENT_ID:
            return None
        return (
            f"https://accounts.zoho.in/oauth/v2/auth?"
            f"scope=ZohoCRM.modules.ALL,ZohoCRM.settings.ALL&"
            f"client_id={settings.ZOHO_CLIENT_ID}&"
            f"response_type=code&"
            f"redirect_uri={settings.ZOHO_REDIRECT_URI}&"
            f"access_type=offline"
        )
    
    @staticmethod
    def save_tokens(tokens):
        with open(settings.TOKEN_FILE, "w") as f:
            json.dump(tokens, f)
    
    @staticmethod
    def load_tokens():
        if os.path.exists(settings.TOKEN_FILE):
            with open(settings.TOKEN_FILE, "r") as f:
                return json.load(f)
        return {}
    
    @staticmethod
    def generate_access_token(grant_code):
        """Generate access token from authorization code"""
        try:
            url = "https://accounts.zoho.in/oauth/v2/token"
            params = {
                "grant_type": "authorization_code",
                "client_id": settings.ZOHO_CLIENT_ID,
                "client_secret": settings.ZOHO_CLIENT_SECRET,
                "redirect_uri": settings.ZOHO_REDIRECT_URI,
                "code": grant_code
            }
            resp = requests.post(url, params=params)
            resp.raise_for_status()
            tokens = resp.json()
            tokens["created_at"] = time.time()
            ZohoService.save_tokens(tokens)
            return tokens, None
        except Exception as e:
            return None, str(e)
    
    @staticmethod
    def refresh_access_token():
        tokens = ZohoService.load_tokens()
        refresh_token = tokens.get("refresh_token")
        if not refresh_token:
            raise Exception("No refresh token found")
        
        url = "https://accounts.zoho.in/oauth/v2/token"
        params = {
            "refresh_token": refresh_token,
            "client_id": settings.ZOHO_CLIENT_ID,
            "client_secret": settings.ZOHO_CLIENT_SECRET,
            "grant_type": "refresh_token"
        }
        resp = requests.post(url, params=params)
        resp.raise_for_status()
        new_tokens = resp.json()
        new_tokens["refresh_token"] = refresh_token
        new_tokens["created_at"] = time.time()
        ZohoService.save_tokens(new_tokens)
        return new_tokens
    
    @staticmethod
    def get_access_token():
        tokens = ZohoService.load_tokens()
        if not tokens or "access_token" not in tokens:
            raise Exception("No token. Click 'Generate Token' button in sidebar.")
        
        # Auto-refresh if expired (3500 seconds = 58 minutes buffer)
        created_at = tokens.get("created_at", 0)
        if time.time() - created_at > 3500:
            tokens = ZohoService.refresh_access_token()
        
        return tokens.get("access_token")
    
    @staticmethod
    def update_call(call_id, transcription, summary):
        """Update Zoho CRM call record"""
        try:
            token = ZohoService.get_access_token()
            headers = {
                "Authorization": f"Zoho-oauthtoken {token}",
                "Content-Type": "application/json"
            }

            update_data = {
                "data": [{
                    "id": int(call_id),
                    "Transcription_c": transcription[:2000] if transcription else "No clear speech detected",
                    "Summary_c": summary
                }]
            }
            
            resp = requests.put(
                "https://www.zohoapis.in/crm/v2/Calls", 
                headers=headers, 
                json=update_data
            )
            
            if resp.status_code == 200:
                return True, None
            else:
                error_msg = f"Status {resp.status_code}: {resp.text}"
                return False, error_msg

        except Exception as e:
            return False, str(e)