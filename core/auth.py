"""
SRK Boost - Authentication  v1.0
Supabase email/password auth — shared with website.
Session saved locally, auto-login on next launch.
"""

import os
import json
import logging
import urllib.request
import urllib.error
import hashlib
import time
from typing import Optional, Dict, Tuple

logger = logging.getLogger(__name__)

# ── Supabase config (replace with your project values) ───────────────────────
SUPABASE_URL    = "https://YOUR_PROJECT.supabase.co"
SUPABASE_ANON   = "YOUR_ANON_KEY"

SESSION_FILE = os.path.join(os.path.expanduser("~"), ".srk_boost", "session.json")


def _headers(token: str = "") -> dict:
    h = {
        "Content-Type": "application/json",
        "apikey": SUPABASE_ANON,
    }
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def _post(endpoint: str, body: dict, token: str = "") -> Tuple[int, dict]:
    url = f"{SUPABASE_URL}/auth/v1/{endpoint}"
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, headers=_headers(token), method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read())
        except Exception:
            return e.code, {"error": str(e)}
    except Exception as e:
        return 0, {"error": str(e)}


def _get(endpoint: str, token: str) -> Tuple[int, dict]:
    url = f"{SUPABASE_URL}/auth/v1/{endpoint}"
    req = urllib.request.Request(url, headers=_headers(token), method="GET")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read())
        except Exception:
            return e.code, {"error": str(e)}
    except Exception as e:
        return 0, {"error": str(e)}


# ── Session persistence ───────────────────────────────────────────────────────

def save_session(data: dict):
    os.makedirs(os.path.dirname(SESSION_FILE), exist_ok=True)
    with open(SESSION_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)


def load_session() -> Optional[dict]:
    try:
        if os.path.exists(SESSION_FILE):
            with open(SESSION_FILE, encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return None


def clear_session():
    try:
        if os.path.exists(SESSION_FILE):
            os.remove(SESSION_FILE)
    except Exception:
        pass


def is_session_valid(session: dict) -> bool:
    """Check if saved token is still valid (not expired)."""
    expires_at = session.get("expires_at", 0)
    return time.time() < expires_at - 60  # 60s buffer


# ── Auth functions ────────────────────────────────────────────────────────────

def sign_up(email: str, password: str) -> Tuple[bool, str, dict]:
    """Register new user. Returns (success, message, user_data)."""
    status, data = _post("signup", {
        "email": email,
        "password": password,
    })
    if status == 200 and "access_token" in data:
        session = {
            "access_token": data["access_token"],
            "refresh_token": data.get("refresh_token", ""),
            "expires_at": time.time() + data.get("expires_in", 3600),
            "user": data.get("user", {}),
        }
        save_session(session)
        return True, "Kayıt başarılı! Hoş geldiniz.", session
    elif status == 200:
        # Email confirmation required
        return True, "Kayıt başarılı! Email adresinizi doğrulayın.", {}
    else:
        msg = data.get("msg") or data.get("message") or data.get("error_description") or data.get("error", "Kayıt başarısız.")
        if "already registered" in str(msg).lower() or "already exists" in str(msg).lower():
            msg = "Bu email adresi zaten kayıtlı."
        elif "password" in str(msg).lower():
            msg = "Şifre en az 6 karakter olmalıdır."
        return False, msg, {}


def sign_in(email: str, password: str) -> Tuple[bool, str, dict]:
    """Login. Returns (success, message, session_data)."""
    status, data = _post("token?grant_type=password", {
        "email": email,
        "password": password,
    })
    if status == 200 and "access_token" in data:
        session = {
            "access_token": data["access_token"],
            "refresh_token": data.get("refresh_token", ""),
            "expires_at": time.time() + data.get("expires_in", 3600),
            "user": data.get("user", {}),
        }
        save_session(session)
        email_disp = session["user"].get("email", email)
        return True, f"Hoş geldiniz! {email_disp}", session
    else:
        msg = data.get("error_description") or data.get("msg") or data.get("error", "Giriş başarısız.")
        if "invalid" in str(msg).lower() or "credentials" in str(msg).lower():
            msg = "Email veya şifre hatalı."
        elif "not confirmed" in str(msg).lower():
            msg = "Email adresinizi doğrulamanız gerekiyor."
        return False, msg, {}


def sign_out(token: str):
    _post("logout", {}, token=token)
    clear_session()


def refresh_token(refresh_tok: str) -> Optional[dict]:
    """Refresh expired session."""
    status, data = _post("token?grant_type=refresh_token", {
        "refresh_token": refresh_tok,
    })
    if status == 200 and "access_token" in data:
        session = {
            "access_token": data["access_token"],
            "refresh_token": data.get("refresh_token", refresh_tok),
            "expires_at": time.time() + data.get("expires_in", 3600),
            "user": data.get("user", {}),
        }
        save_session(session)
        return session
    return None


def get_current_user() -> Optional[dict]:
    """Try to get valid session (auto-refresh if needed)."""
    session = load_session()
    if not session:
        return None
    if is_session_valid(session):
        return session
    # Try refresh
    ref = session.get("refresh_token")
    if ref:
        new_session = refresh_token(ref)
        if new_session:
            return new_session
    clear_session()
    return None
