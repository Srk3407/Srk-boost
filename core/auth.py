"""
SRK Boost - Authentication  v2.0
Supabase email/password + Google OAuth — shared with website.
Session saved locally, auto-login on next launch.
"""

import os
import json
import logging
import urllib.request
import urllib.error
import urllib.parse
import time
import threading
import webbrowser
import http.server
import socket
import secrets
from typing import Optional, Dict, Tuple

logger = logging.getLogger(__name__)

# ── Supabase config (replace with your project values) ───────────────────────
SUPABASE_URL    = "https://nullnnaptshhujxjnnot.supabase.co"
SUPABASE_ANON   = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im51bGxubmFwdHNoaHVqeGpubm90Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzU1Nzc4MDksImV4cCI6MjA5MTE1MzgwOX0.-N576-Xes2I1S6FnlahG0WpOmB0QUA3Oau7EAiQAdNg"

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
    ref = session.get("refresh_token")
    if ref:
        new_session = refresh_token(ref)
        if new_session:
            return new_session
    clear_session()
    return None


# ── Google OAuth (Desktop flow) ────────────────────────────────────────────────

GOOGLE_CALLBACK_PORT = 7123
GOOGLE_REDIRECT_URI  = f"http://localhost:{GOOGLE_CALLBACK_PORT}/callback"


def _find_free_port() -> int:
    with socket.socket() as s:
        s.bind(('', 0))
        return s.getsockname()[1]


def sign_in_google(on_success, on_error):
    """
    Opens browser for Google OAuth.
    on_success(session: dict) and on_error(msg: str) are called from a background thread.
    """
    port = GOOGLE_CALLBACK_PORT
    state = secrets.token_urlsafe(16)

    # Build Supabase Google OAuth URL
    params = urllib.parse.urlencode({
        "provider": "google",
        "redirect_to": f"http://localhost:{port}/callback",
    })
    auth_url = f"{SUPABASE_URL}/auth/v1/authorize?{params}"

    result_holder = {}
    server_done   = threading.Event()

    class _Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            qs     = urllib.parse.parse_qs(parsed.query)

            # Supabase redirects with #access_token in fragment (JS handles it)
            # For desktop we handle the code exchange differently:
            # Supabase sends ?code= in PKCE flow
            code = qs.get("code", [None])[0]
            err  = qs.get("error", [None])[0]

            html_ok = b"""<html><body style='background:#080716;color:#c0b8ff;
                font-family:Segoe UI;text-align:center;padding-top:120px'>
                <h2>\u2705 Giri\u015f ba\u015far\u0131l\u0131!</h2>
                <p>Bu pencereyi kapatabilirsiniz.</p></body></html>"""
            html_err = b"""<html><body style='background:#080716;color:#ff6060;
                font-family:Segoe UI;text-align:center;padding-top:120px'>
                <h2>\u274c Giri\u015f ba\u015far\u0131s\u0131z</h2>
                <p>Tekrar deneyin.</p></body></html>"""

            if code:
                result_holder["code"] = code
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(html_ok)
            else:
                result_holder["error"] = err or "cancelled"
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(html_err)
            server_done.set()

        def log_message(self, *args):
            pass  # silence server logs

    def _run():
        try:
            httpd = http.server.HTTPServer(('localhost', port), _Handler)
            httpd.timeout = 120  # 2 min timeout
            webbrowser.open(auth_url)
            server_done.wait(timeout=120)
            httpd.server_close()

            if "error" in result_holder:
                on_error("Google girişi iptal edildi.")
                return
            if "code" not in result_holder:
                on_error("Zaman aşımı — tekrar deneyin.")
                return

            # Exchange code for session via Supabase
            code = result_holder["code"]
            status, data = _post(
                "token?grant_type=pkce",
                {"auth_code": code, "code_verifier": ""}
            )
            # Supabase PKCE code exchange
            if status != 200:
                # Try alternate exchange
                url = f"{SUPABASE_URL}/auth/v1/token?grant_type=authorization_code"
                body = json.dumps({"code": code}).encode()
                req  = urllib.request.Request(
                    url, data=body, headers=_headers(), method="POST"
                )
                try:
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        status, data = resp.status, json.loads(resp.read())
                except urllib.error.HTTPError as e:
                    status, data = e.code, {}

            if status == 200 and "access_token" in data:
                session = {
                    "access_token":  data["access_token"],
                    "refresh_token": data.get("refresh_token", ""),
                    "expires_at":    time.time() + data.get("expires_in", 3600),
                    "user":          data.get("user", {}),
                }
                save_session(session)
                on_success(session)
            else:
                on_error("Google girişi tamamlanamadı. Tekrar deneyin.")
        except Exception as e:
            on_error(f"Google hatası: {e}")

    threading.Thread(target=_run, daemon=True).start()
