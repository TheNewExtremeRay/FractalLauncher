"""
Microsoft OAuth authentication for Minecraft.

Uses minecraft_launcher_lib's built-in Microsoft login helpers.
Opens a browser for the user to log in, then a local HTTP server
captures the OAuth redirect and exchanges it for tokens.

Uses Prism Launcher's public client ID by default — no setup required.
To use your own Azure App Registration, replace CLIENT_ID below.
"""

import threading
import webbrowser
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Callable, Optional

try:
    import minecraft_launcher_lib as mll
    MSL_AVAILABLE = True
except ImportError:
    MSL_AVAILABLE = False

# ── Microsoft OAuth client ID ────────────────────────────────────────────────
# Uses Prism Launcher's public client ID — works out of the box, no Azure setup.
# You can replace this with your own Azure App Registration client ID if desired.
CLIENT_ID = "c36a9fb6-4f2a-41ff-90bd-ae7cc92031eb"
REDIRECT_PORT = 9876
REDIRECT_URI = f"http://localhost:{REDIRECT_PORT}"
# ──────────────────────────────────────────────────────────────────────────────


class _OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Tiny HTTP handler that captures the OAuth code from Microsoft's redirect."""

    code: Optional[str] = None
    error: Optional[str] = None
    expected_state: Optional[str] = None
    server_done = threading.Event()

    def do_GET(self):
        params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        # Ignore stray requests that don't carry the expected OAuth state
        req_state = params.get("state", [None])[0]
        if self.expected_state and req_state != self.expected_state:
            self.send_response(404)
            self.send_header("Content-Type", "text/html")
            body = b"<h2>Not found</h2>"
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if "code" in params:
            _OAuthCallbackHandler.code = params["code"][0]
            body = b"<h2>Login successful! You can close this tab.</h2>"
        elif "error" in params:
            _OAuthCallbackHandler.error = params.get("error_description", ["Unknown error"])[0]
            body = b"<h2>Login failed. Please close this tab and try again.</h2>"
        else:
            body = b"<h2>Waiting...</h2>"

        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        _OAuthCallbackHandler.server_done.set()

    def log_message(self, *args):
        pass  # Suppress server logs


def start_microsoft_login(
    on_success: Callable[[str, str, str, str, str], None],
    on_error: Callable[[str], None],
    client_id: str = CLIENT_ID,
):
    """
    Starts the Microsoft OAuth flow in a background thread.

    on_success(username, mc_uuid, access_token, refresh_token, skin_url)
    on_error(error_message)
    """
    if not MSL_AVAILABLE:
        on_error("minecraft-launcher-lib is not installed.\nRun: pip install minecraft-launcher-lib")
        return

    def _flow():
        try:
            # Reset state
            _OAuthCallbackHandler.code = None
            _OAuthCallbackHandler.error = None
            _OAuthCallbackHandler.server_done.clear()

            # Build login URL
            login_url, state, code_verifier = mll.microsoft_account.get_secure_login_data(
                client_id, REDIRECT_URI
            )

            # Set expected state to filter stray requests
            _OAuthCallbackHandler.expected_state = state

            # Start local HTTP server to capture redirect
            server = HTTPServer(("localhost", REDIRECT_PORT), _OAuthCallbackHandler)
            server_thread = threading.Thread(target=server.handle_request, daemon=True)
            server_thread.start()

            # Open browser
            webbrowser.open(login_url)

            # Wait for redirect (timeout 5 min)
            _OAuthCallbackHandler.server_done.wait(timeout=300)
            server.server_close()

            if _OAuthCallbackHandler.error:
                on_error(f"Microsoft login failed:\n{_OAuthCallbackHandler.error}")
                return

            if not _OAuthCallbackHandler.code:
                on_error("Login timed out or was cancelled.")
                return

            # Exchange code for tokens
            login_data = mll.microsoft_account.parse_auth_code_url(
                f"{REDIRECT_URI}?code={_OAuthCallbackHandler.code}&state={state}",
                state
            )

            mc_login = mll.microsoft_account.complete_login(
                client_id, None, REDIRECT_URI, login_data, code_verifier
            )

            username = mc_login["name"]
            mc_uuid = mc_login["id"]
            access_token = mc_login["access_token"]
            refresh_token = mc_login.get("refresh_token", "")

            # Try to fetch skin URL
            skin_url = _fetch_skin_url(mc_uuid, access_token)

            on_success(username, mc_uuid, access_token, refresh_token, skin_url)

        except Exception as e:
            on_error(f"Authentication error:\n{str(e)}")

    threading.Thread(target=_flow, daemon=True).start()


def refresh_microsoft_token(
    refresh_token: str,
    client_id: str = CLIENT_ID,
) -> Optional[dict]:
    """
    Returns new {access_token, refresh_token} or None on failure.
    """
    if not MSL_AVAILABLE:
        return None
    try:
        result = mll.microsoft_account.refresh_token(client_id, None, REDIRECT_URI, refresh_token)
        return {
            "access_token": result["access_token"],
            "refresh_token": result.get("refresh_token", refresh_token),
        }
    except Exception as e:
        print(f"[Auth] Token refresh failed: {e}")
        return None


def _fetch_skin_url(mc_uuid: str, access_token: str) -> str:
    """Fetches the player's skin URL from Mojang's API."""
    try:
        import requests
        import base64, json as _json
        resp = requests.get(
            f"https://sessionserver.mojang.com/session/minecraft/profile/{mc_uuid}",
            timeout=5
        )
        if resp.ok:
            props = resp.json().get("properties", [])
            for prop in props:
                if prop.get("name") == "textures":
                    data = _json.loads(base64.b64decode(prop["value"]))
                    return data.get("textures", {}).get("SKIN", {}).get("url", "")
    except Exception:
        pass
    return ""


def fetch_skin_url_by_username(username: str) -> str:
    """Fetch skin URL for any username (used for offline accounts preview)."""
    try:
        import requests
        resp = requests.get(
            f"https://api.mojang.com/users/profiles/minecraft/{username}",
            timeout=5
        )
        if resp.ok:
            mc_uuid = resp.json().get("id", "")
            if mc_uuid:
                return _fetch_skin_url(mc_uuid, "")
    except Exception:
        pass
    return ""
