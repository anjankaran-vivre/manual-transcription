"""
Authentication module — loads users from users.json
"""

import json
import hashlib
import os
from typing import Optional, Dict, Tuple



_APP_DIR = os.path.dirname(os.path.abspath(__file__))   # .../app/
_PROJECT_ROOT = os.path.dirname(_APP_DIR)               # .../MANUAL_TRANSCRIPTION/

USERS_FILE = os.path.join(_PROJECT_ROOT, "credential", "users.json")


def _load_users() -> list:
    """Load users from users.json."""
    try:
        with open(USERS_FILE, "r") as f:
            data = json.load(f)
        return data.get("users", [])
    except FileNotFoundError:
        print(f"[Auth] users.json not found at {USERS_FILE}")
        return []
    except json.JSONDecodeError as e:
        print(f"[Auth] Invalid JSON in users.json: {e}")
        return []


def authenticate(username: str, password: str) -> Tuple[bool, Optional[Dict]]:
    """
    Validate credentials.
    Returns: (success, user_dict_or_None)
    user_dict keys: username, role, display_name
    """
    if not username or not password:
        return False, None

    users = _load_users()
    username = username.strip().lower()

    for user in users:
        if user.get("username", "").lower() == username:
            stored_pw = user.get("password", "")
            if stored_pw == password:          # plain-text match
                return True, {
                    "username":     user["username"],
                    "role":         user.get("role", "user"),
                    "display_name": user.get("display_name", user["username"]),
                }
            return False, None                 # username matched, wrong password

    return False, None                         # username not found


def is_admin(user: Optional[Dict]) -> bool:
    """Check if a user dict has admin role."""
    return user is not None and user.get("role") == "admin"


def get_all_users() -> list:
    """Return all users (without passwords) — for admin display."""
    return [
        {
            "username":     u["username"],
            "role":         u.get("role", "user"),
            "display_name": u.get("display_name", u["username"]),
        }
        for u in _load_users()
    ]