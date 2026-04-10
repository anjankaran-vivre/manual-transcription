"""
Simplified Zoho Service for Streamlit
- Token management and refresh
- Update call records in Zoho CRM
"""

import os
import json
import time
import requests
from dotenv import load_dotenv

load_dotenv()

class ZohoService:
    """Streamlit-optimized Zoho Service"""
    
    TOKEN_FILE = "zoho_tokens.json"
    
    @staticmethod
    def get_config():
        """Get Zoho configuration from environment"""
        return {
            "client_id": os.getenv("ZOHO_CLIENT_ID"),
            "client_secret": os.getenv("ZOHO_CLIENT_SECRET"),
            "redirect_uri": os.getenv("ZOHO_REDIRECT_URI"),
        }
    
    @staticmethod
    def save_tokens(tokens):
        """Save tokens to file"""
        with open(ZohoService.TOKEN_FILE, "w") as f:
            json.dump(tokens, f, indent=2)
    
    @staticmethod
    def load_tokens():
        """Load tokens from file"""
        if os.path.exists(ZohoService.TOKEN_FILE):
            try:
                with open(ZohoService.TOKEN_FILE, "r") as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    @staticmethod
    def generate_access_token(grant_code):
        """
        Generate access token using authorization code
        Call this once to get initial tokens
        """
        try:
            config = ZohoService.get_config()
            url = "https://accounts.zoho.in/oauth/v2/token"
            params = {
                "grant_type": "authorization_code",
                "client_id": config["client_id"],
                "client_secret": config["client_secret"],
                "redirect_uri": config["redirect_uri"],
                "code": grant_code
            }
            resp = requests.post(url, params=params, timeout=30)
            resp.raise_for_status()
            tokens = resp.json()
            tokens["created_at"] = time.time()
            ZohoService.save_tokens(tokens)
            return tokens, None
        except Exception as e:
            return None, str(e)
    
    @staticmethod
    def refresh_access_token():
        """
        Refresh access token using refresh token
        IMPORTANT: Call this before posting to Zoho
        """
        try:
            tokens = ZohoService.load_tokens()
            refresh_token = tokens.get("refresh_token")
            
            if not refresh_token:
                raise Exception("No refresh token found. Please authorize first.")
            
            config = ZohoService.get_config()
            url = "https://accounts.zoho.in/oauth/v2/token"
            params = {
                "refresh_token": refresh_token,
                "client_id": config["client_id"],
                "client_secret": config["client_secret"],
                "grant_type": "refresh_token"
            }
            
            resp = requests.post(url, params=params, timeout=30)
            resp.raise_for_status()
            new_tokens = resp.json()
            new_tokens["refresh_token"] = refresh_token
            new_tokens["created_at"] = time.time()
            ZohoService.save_tokens(new_tokens)
            
            return new_tokens, None
        except Exception as e:
            return None, str(e)
    
    @staticmethod
    def get_access_token():
        """
        Get valid access token
        Automatically refreshes if token is older than 3500 seconds
        """
        try:
            tokens = ZohoService.load_tokens()
            if not tokens:
                raise Exception("No tokens found. Please authorize first.")
            
            # Check if token is expired (default expiry is 3600 seconds)
            created_at = tokens.get("created_at", 0)
            if time.time() - created_at > 3500:
                # Token expired, refresh it
                tokens, error = ZohoService.refresh_access_token()
                if error:
                    raise Exception(f"Failed to refresh token: {error}")
            
            return tokens["access_token"], None
        except Exception as e:
            return None, str(e)
    
    @staticmethod
    def update_call(call_id, transcription, summary):
        """
        Update call record in Zoho CRM
        Returns: (success, error_message)
        """
        try:
            # Make sure token is fresh
            token, error = ZohoService.get_access_token()
            if error:
                return False, error
            
            headers = {
                "Authorization": f"Zoho-oauthtoken {token}",
                "Content-Type": "application/json"
            }
            
            # Ensure transcription doesn't exceed 2000 chars
            transcription_text = transcription[:2000] if transcription else "No clear speech detected"
            
            update_data = {
                "data": [{
                    "id": int(call_id),
                    "Transcription_c": transcription_text,
                    "Summary_c": summary
                }]
            }
            
            resp = requests.put(
                "https://www.zohoapis.in/crm/v2/Calls",
                headers=headers,
                json=update_data,
                timeout=30
            )
            
            if resp.status_code == 200:
                return True, None
            else:
                error_msg = f"Status {resp.status_code}: {resp.text}"
                return False, error_msg
        
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def get_authorization_url():
        """
        Get the OAuth authorization URL for initial login
        User should visit this URL and it will redirect to provided redirect_uri with code
        """
        try:
            config = ZohoService.get_config()
            scope = "CRM.modules.calls.UPDATE,CRM.modules.calls.READ"
            url = (
                f"https://accounts.zoho.in/oauth/v2/auth?"
                f"scope={scope}"
                f"&client_id={config['client_id']}"
                f"&response_type=code"
                f"&redirect_uri={config['redirect_uri']}"
                f"&state=streamlit"
            )
            return url
        except Exception as e:
            return None
