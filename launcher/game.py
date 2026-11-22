"""
Game launch logic — install, mod loaders, skin server, launch.
"""

import os
import subprocess
import threading
import shutil
import json
import base64
import time
from typing import Callable, Optional


# ── Retry handler for transient download errors (IncompleteRead etc.) ─────────

def _install_requests_retry():
    """Configure requests with urllib3-level retries for streaming downloads.

    minecraft-launcher-lib uses `requests` with stream=True for ALL downloads.
    Errors like IncompleteRead happen during r.iter_content(), NOT during
    Session.request(), so patching Session.request does nothing. We need
    urllib3.util.retry.Retry + HTTPAdapter which retries at the socket level.
    """
    try:
        import requests as _req
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry

        _retry = Retry(
            total=5,
            backoff_factor=2,              # 0s, 2s, 4s, 8s, 16s
            status_forcelist=[500, 502, 503, 504, 520, 521, 522, 524],
            allowed_methods=["GET", "HEAD"],
            raise_on_status=False,
        )
        _adapter = HTTPAdapter(max_retries=_retry)

        # Patch Session.__init__ so every new session (including temporary ones
        # created by requests.get()) automatically gets our retry adapter.
        _orig_init = _req.Session.__init__

        def _patched_init(self, *args, **kwargs):
            _orig_init(self, *args, **kwargs)
            self.mount("https://", _adapter)
            self.mount("http://", _adapter)

        _req.Session.__init__ = _patched_init

        # Also patch the module-level get/post/etc helpers which create
        # temporary sessions via Session(). They inherit the patched __init__.
    except ImportError:
        pass  # requests not installed — nothing to patch


_install_requests_retry()


# RSA key generation for authlib-injector metadata endpoint
try:
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    from cryptography.hazmat.primitives import serialization, hashes
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

try:
    import minecraft_launcher_lib as mll
    MLL_AVAILABLE = True
except ImportError:
    MLL_AVAILABLE = False

from .profiles import Profile, Account



DEFAULT_MINECRAFT_DIR = (mll.utils.get_minecraft_directory() if MLL_AVAILABLE
                         else os.path.join(os.path.expanduser("~"), ".minecraft"))

# ── Version manifest cache ───────────────────────────────────────────────
_VERSION_CACHE = []
_VERSION_CACHE_TIME = 0
_VERSION_CACHE_TTL = 300  # 5 minutes
_VERSION_CACHE_LOCK = threading.Lock()


def _get_cached_version_list(version_type: str = "release") -> list[dict]:
    """
    Returns a cached version manifest, re-fetching at most once every TTL seconds.
    This prevents the ~3-8 second network fetch on every call.
    """
    import time
    global _VERSION_CACHE, _VERSION_CACHE_TIME
    now = time.time()
    with _VERSION_CACHE_LOCK:
        if not _VERSION_CACHE or (now - _VERSION_CACHE_TIME) > _VERSION_CACHE_TTL:
            try:
                fetched = mll.utils.get_version_list()
                _VERSION_CACHE = fetched
                _VERSION_CACHE_TIME = now
            except Exception:
                if not _VERSION_CACHE:
                    _VERSION_CACHE = []
    if version_type == "all":
        return _VERSION_CACHE
    return [v for v in _VERSION_CACHE if v.get("type") == version_type]

_CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".FractalLauncher", "config.json")


def _get_config() -> dict:
    if os.path.exists(_CONFIG_PATH):
        try:
            with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def get_minecraft_dir(profile: Profile) -> str:
    """
    Returns the ROOT .minecraft directory (where versions/assets/libraries live).
    Priority: profile.game_dir → config default_mc_dir → system default
    """
    if profile.game_dir and os.path.isabs(profile.game_dir):
        return profile.game_dir
    cfg = _get_config()
    saved = cfg.get("defaultMcDir", cfg.get("default_mc_dir", "")).strip()
    if saved and os.path.isabs(saved):
        return saved
    return DEFAULT_MINECRAFT_DIR


def get_profile_game_dir(profile: Profile) -> str:
    """
    Returns the PER-PROFILE gameDirectory that is passed to Minecraft via --gameDir.
    Fabric (and Forge) read mods from <gameDirectory>/mods/, so each profile
    gets its own isolated folder here.

    Layout:
      <root>/.minecraft/                      ← install dir (versions/assets/libs)
      <root>/.minecraft/FractalLauncher_profiles/<profileId>/          ← gameDir
      <root>/.minecraft/FractalLauncher_profiles/<profileId>/mods/     ← MODS HERE
      <root>/.minecraft/FractalLauncher_profiles/<profileId>/saves/    ← worlds
      <root>/.minecraft/FractalLauncher_profiles/<profileId>/options.txt etc.
    """
    root = get_minecraft_dir(profile)
    game_dir = os.path.join(root, "FractalLauncher_profiles", profile.id)
    for sub in ("mods", "shaderpacks", "resourcepacks", "saves"):
        os.makedirs(os.path.join(game_dir, sub), exist_ok=True)
    return game_dir


def list_versions(version_type: str = "all") -> list[dict]:
    if not MLL_AVAILABLE:
        return []
    return _get_cached_version_list(version_type)


def get_installed_versions(minecraft_dir: str = DEFAULT_MINECRAFT_DIR) -> list[str]:
    """Installed version ids. Resilient per-folder scan: a single corrupt /
    stub version json is skipped instead of nuking the whole list (mll's
    get_installed_versions raises KeyError on missing id/type/releaseTime
    and the old blanket try/except turned that into [])."""
    vdir = os.path.join(minecraft_dir, "versions")
    try:
        names = os.listdir(vdir)
    except OSError:
        return []
    out = []
    for name in names:
        try:
            with open(os.path.join(vdir, name, name + ".json"),
                      encoding="utf-8") as f:
                vid = json.load(f).get("id")
            if vid:
                out.append(vid)
        except Exception:
            continue
    return out


def is_version_installed(version_id: str, minecraft_dir: str = DEFAULT_MINECRAFT_DIR) -> bool:
    return version_id in get_installed_versions(minecraft_dir)


def check_assets_cache(version_id: str,
                       minecraft_dir: str = DEFAULT_MINECRAFT_DIR) -> dict:
    """
    Compare what a version needs (libraries + assets) against what's already on
    disk.  Returns a dict with counts and bytes so the UI can show
    "X of Y libraries already cached, Z MB will be downloaded".
    Handles inheritsFrom (Forge/Fabric) by merging parent version data.
    """
    result = {
        "libraries": {"total": 0, "cached": 0, "bytes_needed": 0, "bytes_cached": 0},
        "assets":    {"total": 0, "cached": 0, "bytes_needed": 0, "bytes_cached": 0},
        "jar":       {"needed": False, "cached": False, "size": 0},
        "runtime":   {"needed": False, "cached": False},
    }

    ver_path = os.path.join(minecraft_dir, "versions", version_id, f"{version_id}.json")
    if not os.path.isfile(ver_path):
        return result

    try:
        data = _load_json_cached(ver_path)
    except Exception:
        return result

    # Merge inherited version data (Forge/Fabric use inheritsFrom)
    libs_dir = os.path.join(minecraft_dir, "libraries")

    def _count_libs(lib_list):
        for lib in lib_list:
            if "rules" in lib:
                try:
                    from minecraft_launcher_lib.install import parse_rule_list
                    if not parse_rule_list(lib["rules"], {}):
                        continue
                except Exception:
                    pass

            result["libraries"]["total"] += 1
            name = lib.get("name", "")
            parts = name.split(":")
            if len(parts) < 3:
                continue

            lib_path, lib_name, lib_ver_file = parts[0], parts[1], parts[2]
            lib_fileend = "jar"
            if "@" in lib_ver_file:
                lib_ver_file, lib_fileend = lib_ver_file.rsplit("@", 1)

            # Prefer artifact path from downloads
            jar = None
            size = 0
            if "downloads" in lib and "artifact" in lib["downloads"]:
                art = lib["downloads"]["artifact"]
                if "path" in art:
                    jar = os.path.join(libs_dir, art["path"])
                size = art.get("size", 0)
            else:
                base = os.path.join(libs_dir, *lib_path.split("."), lib_name, lib_ver_file)
                jar = os.path.join(base, f"{lib_name}-{lib_ver_file}.{lib_fileend}")

            if jar and os.path.isfile(jar):
                result["libraries"]["cached"] += 1
                result["libraries"]["bytes_cached"] += size
            else:
                result["libraries"]["bytes_needed"] += size

    # ── Handle inheritsFrom (merge parent libs + assets) ────────────────────
    seen_hashes = set()

    def _count_assets(asset_data):
        objects = asset_data.get("objects", {})
        for obj in objects.values():
            h = obj["hash"]
            if h in seen_hashes:
                continue
            seen_hashes.add(h)
            result["assets"]["total"] += 1
            sz = obj.get("size", 0)
            obj_path = os.path.join(minecraft_dir, "assets", "objects", h[:2], h)
            if os.path.isfile(obj_path):
                result["assets"]["cached"] += 1
                result["assets"]["bytes_cached"] += sz
            else:
                result["assets"]["bytes_needed"] += sz

    if "inheritsFrom" in data:
        parent_id = data["inheritsFrom"]
        parent_path = os.path.join(minecraft_dir, "versions", parent_id, f"{parent_id}.json")
        if os.path.isfile(parent_path):
            try:
                parent = _load_json_cached(parent_path)
                _count_libs(parent.get("libraries", []))
                # Parent's assets
                if "assets" in parent:
                    idx_path = os.path.join(minecraft_dir, "assets", "indexes",
                                            parent["assets"] + ".json")
                    if os.path.isfile(idx_path):
                        _count_assets(_load_json_cached(idx_path))
                # Parent's jar
                parent_jar = os.path.join(minecraft_dir, "versions", parent_id,
                                          f"{parent_id}.jar")
                if os.path.isfile(parent_jar):
                    result["jar"]["cached"] = True
            except Exception:
                pass

    # ── Current version's own libs ──────────────────────────────────────────
    _count_libs(data.get("libraries", []))

    # ── Current version's assets ────────────────────────────────────────────
    if "assets" in data:
        idx_path = os.path.join(minecraft_dir, "assets", "indexes",
                                data["assets"] + ".json")
        if os.path.isfile(idx_path):
            try:
                _count_assets(_load_json_cached(idx_path))
            except Exception:
                pass

    # ── Client jar ─────────────────────────────────────────────────────────
    jar_path = os.path.join(minecraft_dir, "versions", version_id,
                            f"{version_id}.jar")
    if os.path.isfile(jar_path):
        result["jar"]["cached"] = True
    if not result["jar"]["cached"] and "downloads" in data and "client" in data["downloads"]:
        result["jar"]["needed"] = True
        result["jar"]["size"] = data["downloads"]["client"].get("size", 0)

    # ── Java runtime ───────────────────────────────────────────────────────
    java_ver = data.get("javaVersion", {}).get("component", "")
    if java_ver:
        result["runtime"]["needed"] = True
        rt_dir = os.path.join(minecraft_dir, "runtime", java_ver)
        result["runtime"]["cached"] = os.path.isdir(rt_dir)

    return result


def install_version(
    version_id: str,
    minecraft_dir: str = DEFAULT_MINECRAFT_DIR,
    on_progress: Optional[Callable[[int, int, str], None]] = None,
    on_done: Optional[Callable[[bool, str], None]] = None,
):
    def _install():
        max_retries = 3
        last_err = None
        for attempt in range(max_retries):
            try:
                callbacks = {}
                if on_progress:
                    callbacks["setStatus"]   = lambda t: on_progress(0, 0, t)
                    callbacks["setProgress"] = lambda v: on_progress(v, 0, "")
                    callbacks["setMax"]      = lambda v: on_progress(0, v, "")
                mll.install.install_minecraft_version(version_id, minecraft_dir, callback=callbacks)
                if on_done:
                    on_done(True, f"Version {version_id} installed successfully.")
                return
            except Exception as e:
                last_err = e
                if attempt < max_retries - 1:
                    if on_progress:
                        on_progress(0, 0, f"Retrying ({attempt + 2}/{max_retries}) after error...")
                    time.sleep(2 * (attempt + 1))
                    continue
        if on_done:
            on_done(False, str(last_err))
    threading.Thread(target=_install, daemon=True).start()


def install_mod_loader(
    version_id: str,
    mod_loader: str,
    loader_version: str = "latest",
    minecraft_dir: str = DEFAULT_MINECRAFT_DIR,
    on_progress: Optional[Callable[[int, int, str], None]] = None,
    on_done: Optional[Callable[[bool, str], None]] = None,
):
    def _install():
        max_retries = 3
        last_err = None
        for attempt in range(max_retries):
            try:
                callbacks = {}
                if on_progress:
                    callbacks["setStatus"]   = lambda t: on_progress(0, 0, t)
                    callbacks["setProgress"] = lambda v: on_progress(v, 0, "")
                    callbacks["setMax"]      = lambda v: on_progress(0, v, "")

                cfg = _get_config()

                if mod_loader == "fabric":
                    java_path = cfg.get("javaPath", cfg.get("java_path", "")).strip() or None
                    if loader_version and loader_version != "latest":
                        mll.fabric.install_fabric(version_id, minecraft_dir,
                                                  loader_version=loader_version, callback=callbacks,
                                                  java=java_path)
                    else:
                        mll.fabric.install_fabric(version_id, minecraft_dir, callback=callbacks,
                                                  java=java_path)
                    installed = get_installed_versions(minecraft_dir)
                    fabric_id = next((v for v in installed if version_id in v and "fabric" in v), None)
                    if on_done:
                        on_done(True, fabric_id or f"fabric-loader-{version_id}")
                    return

                elif mod_loader == "quilt":
                    java_path = cfg.get("javaPath", cfg.get("java_path", "")).strip() or None
                    if loader_version and loader_version != "latest":
                        mll.quilt.install_quilt(version_id, minecraft_dir,
                                                loader_version=loader_version, callback=callbacks,
                                                java=java_path)
                    else:
                        mll.quilt.install_quilt(version_id, minecraft_dir, callback=callbacks,
                                                java=java_path)
                    installed = get_installed_versions(minecraft_dir)
                    quilt_id = next((v for v in installed if version_id in v and "quilt" in v), None)
                    if on_done:
                        on_done(True, quilt_id or f"quilt-loader-{version_id}")
                    return

                elif mod_loader == "forge":
                    forge_loader = mll.mod_loader.get_mod_loader("forge")
                    if not forge_loader.is_minecraft_version_supported(version_id):
                        if on_done:
                            on_done(False, f"Forge doesn't support Minecraft {version_id}")
                        return
                    java_path = cfg.get("javaPath", cfg.get("java_path", "")).strip() or None
                    try:
                        if loader_version and loader_version != "latest":
                            forge_id = forge_loader.install(version_id, minecraft_dir,
                                                            loader_version=loader_version,
                                                            callback=callbacks,
                                                            java=java_path)
                        else:
                            forge_id = forge_loader.install(version_id, minecraft_dir,
                                                            callback=callbacks,
                                                            java=java_path)
                        if on_done:
                            on_done(True, forge_id)
                    except Exception as e:
                        if on_done:
                            on_done(False, f"Forge install failed for {version_id}: {e}")
                    return

                elif mod_loader == "neoforge":
                    loader = mll.mod_loader.get_mod_loader("neoforge")
                    neoforge_versions = loader.get_minecraft_versions(False)
                    if version_id not in neoforge_versions:
                        if on_done:
                            on_done(False, f"NeoForge doesn't support Minecraft {version_id} yet")
                        return
                    java_path = cfg.get("javaPath", cfg.get("java_path", "")).strip() or None
                    neo_id = loader.install(version_id, minecraft_dir, callback=callbacks,
                                            java=java_path)
                    if on_done:
                        on_done(True, neo_id or f"neoforge-{version_id}")
                    return
                else:
                    if on_done:
                        on_done(False, f"Unknown mod loader: {mod_loader}")
                    return

            except Exception as e:
                last_err = e
                if attempt < max_retries - 1:
                    if on_progress:
                        on_progress(0, 0, f"Retrying ({attempt + 2}/{max_retries}) after connection error...")
                    time.sleep(2 * (attempt + 1))
                    continue
        if on_done:
            on_done(False, str(last_err))

    threading.Thread(target=_install, daemon=True).start()


def get_fabric_loader_versions() -> list[str]:
    try:
        return [v["version"] for v in mll.fabric.get_all_loader_versions()]
    except Exception:
        return []


def get_forge_versions_for_mc(mc_version: str) -> list[str]:
    try:
        result = mll.forge.find_forge_version(mc_version)
        return [result] if result else []
    except Exception:
        return []


# ── Localhost skin server ─────────────────────────────────────────────────────

def _generate_rsa_keypair():
    """
    Generate a 4096-bit RSA keypair.
    Returns (private_key, public_key_pem_str) or (None, None) if cryptography not installed.

    authlib-injector parses the signaturePublickey field by:
      1. Stripping -----BEGIN/END PUBLIC KEY----- headers
      2. Stripping all whitespace
      3. Base64-decoding the result as DER X509EncodedKeySpec
    So we must send the full PEM string (with headers and newlines).
    It then verifies property signatures using SHA1withRSA.
    """
    if not CRYPTO_AVAILABLE:
        return None, None
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=4096)
    pub_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode()
    return private_key, pub_pem


def _sign_data(private_key, data: bytes) -> str:
    """Sign bytes with RSA-SHA1 (SHA1withRSA) — this is what authlib-injector expects,
    matching Mojang's original Yggdrasil property signature format."""
    sig = private_key.sign(data, padding.PKCS1v15(), hashes.SHA1())
    return base64.b64encode(sig).decode()


class _SkinServer:
    """
    Localhost HTTP server implementing the full authlib-injector / Yggdrasil API.

    authlib-injector proxies MC's auth calls through its own httpd, which in turn
    calls OUR server. The contract it enforces:

      GET /                                     → metadata JSON with skinDomains
      GET /sessionserver/session/minecraft/profile/<uuid>  → profile + textures
      GET /sessionserver/session/minecraft/hasJoined       → profile + textures
      POST /sessionserver/session/minecraft/join           → 204
      GET /api/profiles/minecraft/<name>        → profile lookup
      GET /api/user/profile/<uuid>/<type>       → skin/cape PNG
      POST /authserver/authenticate             → fake token response
      POST /authserver/refresh                  → fake token response
      POST /authserver/validate                 → 204
      GET  /skin                                → raw PNG (served to MC directly)

    The metadata endpoint is critical — without it authlib-injector refuses to
    forward any calls.
    """
    def __init__(self, skin_path: str, skin_model: str, mc_uuid: str, username: str, cape_path: str = ""):
        self.skin_path  = skin_path
        self.skin_model = skin_model
        self.cape_path  = cape_path
        self.mc_uuid    = mc_uuid.replace("-", "")
        self.username   = username
        self.port       = None
        self._server    = None
        # Resolve LAN IP immediately so it's available before start() is called
        import socket as _sock
        _s = None
        try:
            _s = _sock.socket(_sock.AF_INET, _sock.SOCK_DGRAM)
            _s.connect(("8.8.8.8", 80))
            self._lan_ip = _s.getsockname()[0]
        except Exception:
            self._lan_ip = "127.0.0.1"
        finally:
            if _s:
                try:
                    _s.close()
                except Exception:
                    pass
        # Generate RSA keypair once — authlib-injector needs a real public key
        self._private_key, self._public_key_pem = _generate_rsa_keypair()

    def start(self) -> int:
        from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
        import json as _json

        skin_path      = self.skin_path
        skin_model     = self.skin_model
        cape_path      = self.cape_path
        mc_uuid        = self.mc_uuid
        username       = self.username
        private_key    = self._private_key
        public_key_pem = self._public_key_pem

        # Safely print to stdout even when compiled --windowed (no console).
        # PyInstaller GUI apps have sys.stdout = None, and crashing on a print
        # inside an HTTP handler causes the response to never be sent.
        def _slog(msg: str):
            import sys as _sys
            try:
                if _sys.stdout is not None:
                    print(f"[SkinServer] {msg}", file=_sys.stdout, flush=True)
            except Exception:
                pass

        class _Handler(BaseHTTPRequestHandler):
            # HTTP/1.1 makes Content-Length the primary response delimiter.
            # In HTTP/1.0, connection-close is the default — Java reads until
            # the socket closes, which races against the close and can cause
            # "Unexpected end of file". In HTTP/1.1, Java reads exactly N bytes
            # then the subsequent close is expected, not an error.
            # We also send Connection: close so the handler doesn't loop back
            # to readline() waiting for a next request — preventing deadlock.
            protocol_version = "HTTP/1.1"

            def log_message(self, fmt, *args):
                _slog(f"{self.path} → {fmt % args}")

            # ── helpers ──────────────────────────────────────────────────────

            def _send(self, body: bytes, status: int = 200,
                      ctype: str = "application/json"):
                try:
                    self.send_response(status)
                    self.send_header("Content-Type", ctype)
                    self.send_header("Content-Length", str(len(body)))
                    self.send_header("Cache-Control", "no-cache")
                    # Send Connection: close so both sides agree the connection
                    # ends after this response. This prevents deadlock where
                    # Python's handler tries to readline() for the next request
                    # while Java's HTTP client is waiting for more data.
                    self.send_header("Connection", "close")
                    self.end_headers()
                    if body:
                        self.wfile.write(body)
                    self.wfile.flush()
                    # Ensure the handler closes the socket after this request
                    # (without this, HTTP/1.1 handlers try to read more requests)
                    self.close_connection = True
                except Exception as ex:
                    _slog(f"ERROR sending response: {ex}")
                    self.close_connection = True

            def _json(self, data, status: int = 200):
                self._send(_json.dumps(data).encode(), status)

            def _read_body(self):
                try:
                    n = int(self.headers.get("Content-Length", 0))
                except (ValueError, TypeError):
                    n = 0
                return self.rfile.read(n) if n else b""

            def _lan_ip(self):
                return getattr(self.server, "_lan_ip", "127.0.0.1")

            def _skin_url(self):
                # Always 127.0.0.1 — MC fetches textures through authlib-injector's
                # local proxy which then forwards to us. LAN IP is only for hasJoined.
                port = self.server.server_address[1]
                return f"http://127.0.0.1:{port}/skin"

            def _cape_url(self):
                port = self.server.server_address[1]
                return f"http://127.0.0.1:{port}/cape"

            def _textures_b64(self):
                textures_obj = {}
                # Only advertise SKIN if we actually have a file to serve
                if skin_path and os.path.isfile(skin_path):
                    textures_obj["SKIN"] = {
                        "url": self._skin_url(),
                        **({"metadata": {"model": "slim"}}
                           if skin_model == "slim" else {})
                    }
                if cape_path and os.path.isfile(cape_path):
                    textures_obj["CAPE"] = {"url": self._cape_url()}
                tex = {
                    "timestamp": int(time.time() * 1000),
                    "profileId": mc_uuid,
                    "profileName": username,
                    "isPublic": True,
                    "textures": textures_obj  # empty dict = default Steve/Alex
                }
                return base64.b64encode(
                    _json.dumps(tex, separators=(",", ":")).encode()
                ).decode()

            def _profile(self):
                tex_b64 = self._textures_b64()
                prop = {"name": "textures", "value": tex_b64}
                # Sign the value with our RSA key so authlib-injector trusts it
                if private_key and CRYPTO_AVAILABLE:
                    sig = _sign_data(private_key, tex_b64.encode())
                    prop["signature"] = sig
                    _slog(f"Profile: uuid={mc_uuid} sig_len={len(sig)} tex_b64_len={len(tex_b64)}")
                else:
                    _slog(f"WARNING: No signature (crypto unavailable)")
                return {
                    "id":   mc_uuid,
                    "name": username,
                    "properties": [prop]
                }

            def _fake_token(self):
                return {
                    "accessToken":       "offline",
                    "clientToken":       "offline",
                    "availableProfiles": [{"id": mc_uuid, "name": username}],
                    "selectedProfile":   {"id": mc_uuid, "name": username},
                    "user": {
                        "id":         mc_uuid,
                        "username":   username,
                        "properties": []
                    }
                }

            # ── GET ──────────────────────────────────────────────────────────

            def do_GET(self):
                p = self.path.split("?")[0].rstrip("/")

                # ── Metadata root (REQUIRED by authlib-injector) ─────────────
                # authlib-injector GETs "/" first; if this returns bad JSON or
                # is missing skinDomains it aborts and won't forward anything.
                if p == "" or p == "/":
                    port = self.server.server_address[1]
                    self._json({
                        "meta": {
                            "serverName":    "FractalLauncher",
                            "implementationName": "FractalLauncher Skin Server",
                            "implementationVersion": "1.2.4",
                            "feature.non_email_login": True
                        },
                        "skinDomains": ["127.0.0.1", "localhost"],
                        "signaturePublickey": public_key_pem or ""
                    })

                # ── Raw skin PNG (served directly to MC renderer) ────────────
                elif p == "/skin":
                    if skin_path and os.path.isfile(skin_path):
                        try:
                            with open(skin_path, "rb") as f:
                                data = f.read()
                            self._send(data, ctype="image/png")
                        except Exception:
                            self._send(b"", 404)
                    else:
                        self._send(b"", 404)  # no skin → MC uses default

                # ── Raw cape PNG ─────────────────────────────────────────────
                elif p == "/cape":
                    if cape_path and os.path.isfile(cape_path):
                        try:
                            with open(cape_path, "rb") as f:
                                data = f.read()
                            self._send(data, ctype="image/png")
                        except Exception:
                            self._send(b"", 404)
                    else:
                        self._send(b"", 404)

                # ── Session / profile endpoints ──────────────────────────────
                # authlib-injector uses ConcatenateURL: it sets sessionHost to
                # http://OUR_IP:PORT/https/sessionserver.mojang.com  so MC calls
                # http://OUR_IP:PORT/https/sessionserver.mojang.com/session/minecraft/...
                # We must match both the raw path AND the concatenated Mojang URL path.
                elif ("session/minecraft/hasJoined" in p or
                      "session/minecraft/profile" in p):
                    self._json(self._profile())

                # ── Profile lookup by name ────────────────────────────────────
                elif ("profiles/minecraft" in p or
                      "users/profiles/minecraft" in p):
                    self._json({"id": mc_uuid, "name": username})

                # ── Skin/cape texture fetch ───────────────────────────────────
                elif "user/profile" in p or "user/skin" in p:
                    if skin_path and os.path.isfile(skin_path):
                        try:
                            with open(skin_path, "rb") as f:
                                data = f.read()
                            self._send(data, ctype="image/png")
                        except Exception:
                            self._send(b"", 404)
                    else:
                        self._send(b"", 404)

                # ── Services / misc ───────────────────────────────────────────
                elif "player/certificates" in p:
                    self._json({})

                elif "privacy/blocklist" in p:
                    self._json({"blockedProfiles": []})

                elif "minecraft/profile/lookup" in p:
                    self._json([{"id": mc_uuid, "name": username}])

                else:
                    self._json({})

            # ── POST ─────────────────────────────────────────────────────────

            def do_POST(self):
                body_bytes = self._read_body()
                p = self.path.split("?")[0].rstrip("/")

                if "authserver/authenticate" in p or "auth/authenticate" in p:
                    self._json(self._fake_token())

                elif "authserver/refresh" in p or "auth/refresh" in p:
                    self._json(self._fake_token())

                elif "authserver/validate" in p or "auth/validate" in p:
                    self._send(b"", 204)

                elif "authserver/invalidate" in p or "auth/invalidate" in p:
                    self._send(b"", 204)

                elif ("session/minecraft/join" in p):
                    self._send(b"", 204)

                else:
                    self._json({})

        self._server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        self._server._lan_ip = "127.0.0.1"
        self.port = self._server.server_address[1]
        _slog(f"Started on port {self.port}, crypto={CRYPTO_AVAILABLE}, has_key={private_key is not None}")
        threading.Thread(target=self._server.serve_forever, daemon=True).start()

        # ── Health check: verify the server is actually responding ──────────
        import socket as _sock
        for _attempt in range(10):
            _s = None
            try:
                _s = _sock.create_connection(("127.0.0.1", self.port), timeout=2)
                _s.sendall(b"GET / HTTP/1.0\r\nHost: 127.0.0.1\r\nConnection: close\r\n\r\n")
                _resp = _s.recv(4096)
                if b"200 OK" in _resp:
                    _slog(f"Health check OK (port {self.port})")
                    break
            except Exception:
                import time as _time
                _time.sleep(0.05)
            finally:
                if _s:
                    try:
                        _s.close()
                    except Exception:
                        pass
        else:
            _slog(f"WARNING: Health check failed (port {self.port})")

        return self.port

    def stop(self):
        if self._server:
            self._server.shutdown()
            self._server = None


# ── Launch ────────────────────────────────────────────────────────────────────

_JSON_PARSE_CACHE = {}   # (path, mtime_ns, size) -> parsed JSON object
_JSON_PARSE_CACHE_LOCK = threading.Lock()

def _load_json_cached(path: str):
    """Load and parse a JSON file, memoizing by (path, mtime_ns, size).
    Identical to json.load(open(path)) for callers; avoids re-parsing
    version/asset-index JSONs repeatedly during launch checks."""
    try:
        st = os.stat(path)
        key = (path, st.st_mtime_ns, st.st_size)
    except OSError:
        return json.load(open(path, "r", encoding="utf-8"))
    with _JSON_PARSE_CACHE_LOCK:
        hit = _JSON_PARSE_CACHE.get(key)
    if hit is not None:
        return hit
    with open(path, "r", encoding="utf-8") as f:
        obj = json.load(f)
    with _JSON_PARSE_CACHE_LOCK:
        if len(_JSON_PARSE_CACHE) > 64:
            _JSON_PARSE_CACHE.clear()
        _JSON_PARSE_CACHE[key] = obj
    return obj

def build_launch_options(profile: Profile, account: Account,
                          skin_server_port: int = 0,
                          authlib_base_url: str = "") -> dict:
    opts = {
        "username": account.username,
        "uuid":     account.uuid,
        "token":    account.access_token,
    }

    # Per-profile gameDirectory — Fabric reads mods from <gameDir>/mods/
    game_dir = get_profile_game_dir(profile)
    opts["gameDirectory"] = game_dir

    # RAM — match Xms to Xmx so JVM never needs to grow the heap (no GC stutter)
    max_ram = f"{profile.ram_mb}M"
    jvm_args = [
        f"-Xmx{max_ram}",
        f"-Xms{max_ram}",           # pre-allocate all RAM upfront

        # JVM server mode
        "-server",
        "-XX:+UnlockExperimentalVMOptions",
        "-XX:+UnlockDiagnosticVMOptions",

        # Aikar GC flags (proven for Minecraft)
        "-XX:+UseG1GC",
        "-XX:+DisableExplicitGC",   # block System.gc() stutter calls
        "-XX:+AlwaysPreTouch",      # pre-touch heap pages, avoids in-game page faults
        "-XX:G1NewSizePercent=30",
        "-XX:G1MaxNewSizePercent=40",
        "-XX:G1HeapRegionSize=16M",
        "-XX:G1ReservePercent=20",
        "-XX:G1HeapWastePercent=5",
        "-XX:G1MixedGCCountTarget=4",
        "-XX:MaxGCPauseMillis=200",
        "-XX:InitiatingHeapOccupancyPercent=15",
        "-XX:G1MixedGCLiveThresholdPercent=90",
        "-XX:G1RSetUpdatingPauseTimePercent=5",
        "-XX:SurvivorRatio=32",
        "-XX:+PerfDisableSharedMem",
        "-XX:MaxTenuringThreshold=1",

        # GPU / LWJGL — allow software fallback for older versions (LWJGL 2.x
        # on Windows 11 can fail with "Pixel format not accelerated" if the GPU
        # driver doesn't expose a compatible pixel format)
        "-Dorg.lwjgl.opengl.Display.allowSoftwareOpenGL=true",
        "-Dorg.lwjgl.util.NoChecks=true",
        "-Dfml.ignorePatchDiscrepancies=true",
        "-Dfml.ignoreInvalidMinecraftCertificates=true",
        "-Dfml.skipSplashScreen=true",

        # String / threading opts
        "-XX:+UseStringDeduplication",
        "-XX:+OptimizeStringConcat",
        "-XX:+UseCompressedOops",
        "-Dfile.encoding=UTF-8",
    ]

    # ── Offline skin via authlib-injector ────────────────────────────────────
    # MC 1.19+ completely ignores -Dminecraft.api.* properties — authlib-injector
    # is the only working approach (same as TLauncher / PolyMC offline skins).
    # The -javaagent arg must come BEFORE all other JVM args.
    if skin_server_port > 0:
        # Use the provided base URL (cloudflare tunnel or localhost)
        base = authlib_base_url or f"http://127.0.0.1:{skin_server_port}"
        cfg2 = _get_config()
        authlib_path = cfg2.get("authlib_injector_path", "").strip()
        if authlib_path and os.path.isfile(authlib_path):
            jvm_args.insert(0, f"-javaagent:{authlib_path}={base}")
        # else: no jar set — skin server still runs but skin won't show
        #       (launch_game will print a warning about this)

    # Extra user JVM args
    if profile.jvm_args.strip():
        jvm_args += [a for a in profile.jvm_args.split() if a.startswith("-")]

    opts["jvmArguments"] = jvm_args

    # Resolution
    if not profile.fullscreen:
        opts["customResolution"] = True
        opts["resolutionWidth"]  = str(profile.resolution_w)
        opts["resolutionHeight"] = str(profile.resolution_h)

    # Custom Java executable
    cfg = _get_config()
    java_path = cfg.get("javaPath", cfg.get("java_path", "")).strip()
    if java_path and os.path.isfile(java_path):
        opts["executablePath"] = java_path

    return opts


def launch_game(
    profile: Profile,
    account: Account,
    on_log: Callable[[str], None],
    on_exit: Callable[[int], None],
    on_process: Callable = None,
    version_override: str = "",
):
    if not MLL_AVAILABLE:
        on_log("[ERROR] minecraft-launcher-lib is not installed!")
        on_exit(1)
        return

    def _launch():
        skin_server = None
        tunnel_proc = None
        try:
            install_dir = get_minecraft_dir(profile)   # root .minecraft (versions/assets/libs)
            game_dir    = get_profile_game_dir(profile)  # per-profile dir (mods/saves/options)
            version_id  = version_override or profile.version

            on_log(f"[FractalLauncher] Version    : {version_id}")
            on_log(f"[FractalLauncher] User       : {account.username}")
            on_log(f"[FractalLauncher] Install dir: {install_dir}")
            on_log(f"[FractalLauncher] Game dir   : {game_dir}")

            # Log mods
            _mods_path = os.path.join(game_dir, "mods")
            _mod_count = len([f for f in os.listdir(_mods_path)
                              if f.endswith(".jar")]) if os.path.isdir(_mods_path) else 0
            on_log(f"[FractalLauncher] Mods       : {_mods_path}  ({_mod_count} mod(s))")

            # Clear Minecraft's local skin cache so stale skins from old accounts
            # never bleed onto new accounts. MC rebuilds it fresh from our skin server.
            for _cache_subdir in ("assets/skins", "assets/avatars"):
                _cache_path = os.path.join(install_dir, _cache_subdir)
                if os.path.isdir(_cache_path):
                    import shutil as _shutil
                    try:
                        _shutil.rmtree(_cache_path)
                        on_log(f"[FractalLauncher] Cleared skin cache: {_cache_path}")
                    except Exception as _e:
                        on_log(f"[FractalLauncher] Could not clear skin cache: {_e}")

            # Start skin server for ALL offline accounts — even with no skin.
            # This is critical: if we don't intercept auth for offline accounts,
            # Minecraft falls back to its on-disk skin cache which may contain
            # a previous account's skin/cape, causing it to "bleed" onto new accounts.
            skin_server_port = 0
            skin_path  = getattr(account, "skin_path",  "") or ""
            skin_model = getattr(account, "skin_model", "default") or "default"
            cape_path_val = getattr(account, "cape_path", "") or ""

            tunnel_proc = None
            if account.auth_type == "offline":
                # Start local skin server for offline skins
                skin_server = _SkinServer(skin_path, skin_model, account.uuid,
                                          account.username, cape_path_val)
                skin_server_port = skin_server.start()
                on_log(f"[FractalLauncher] Skin server: 127.0.0.1:{skin_server_port}")
                if skin_path and os.path.isfile(skin_path):
                    on_log(f"[FractalLauncher] Skin file  : {skin_path} (model={skin_model})")
                    if cape_path_val and os.path.isfile(cape_path_val):
                        on_log(f"[FractalLauncher] Cape file  : {cape_path_val}")

                # Check authlib-injector
                authlib_path = _get_config().get("authlib_injector_path", "").strip()
                if authlib_path and os.path.isfile(authlib_path):
                    on_log(f"[FractalLauncher] AuthLib    : {authlib_path}")
                    if not CRYPTO_AVAILABLE:
                        on_log("[FractalLauncher] ⚠ 'cryptography' package not installed!")
                        on_log("[FractalLauncher] ⚠ Skin signing disabled — skin may not show.")
                else:
                    on_log("[FractalLauncher] ⚠ AuthLib-Injector NOT configured!")
                    on_log("[FractalLauncher] ⚠ Skin will NOT show without it.")

                # Use localhost for authlib (no tunnel needed)
                authlib_base_url = f"http://127.0.0.1:{skin_server_port}"
                on_log(f"[FractalLauncher] Auth base  : {authlib_base_url}")
            else:
                authlib_base_url = f"http://127.0.0.1:{skin_server_port}"

            options = build_launch_options(profile, account, skin_server_port, authlib_base_url)

            if "executablePath" in options:
                on_log(f"[FractalLauncher] Java       : {options['executablePath']}")

            command = mll.command.get_minecraft_command(version_id, install_dir, options)

            on_log(f"[FractalLauncher] Launching...\n")

            # Launch with HIGH priority so Minecraft isn't starved by background tasks
            import sys as _sys
            popen_kwargs = dict(
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            if _sys.platform == "win32":
                # ABOVE_NORMAL_PRIORITY_CLASS = 0x8000, HIGH_PRIORITY_CLASS = 0x80
                popen_kwargs["creationflags"] = 0x00008000  # ABOVE_NORMAL (safe, not starves OS)
            proc = subprocess.Popen(command, **popen_kwargs)
            if on_process:
                on_process(proc)

            # Boost Java process priority after launch (Windows only)
            if _sys.platform == "win32":
                try:
                    import ctypes as _ct
                    ABOVE_NORMAL = 0x8000
                    handle = _ct.windll.kernel32.OpenProcess(0x0200, False, proc.pid)
                    if handle:
                        _ct.windll.kernel32.SetPriorityClass(handle, ABOVE_NORMAL)
                        _ct.windll.kernel32.CloseHandle(handle)
                except Exception:
                    pass

            for line in proc.stdout:
                on_log(line.rstrip())

            proc.wait()
            if proc.stdout:
                proc.stdout.close()
            on_log(f"\n[FractalLauncher] Game exited with code {proc.returncode}")
            on_exit(proc.returncode)

        except Exception as e:
            on_log(f"[FractalLauncher] Launch failed: {e}")
            on_exit(1)
        finally:
            if skin_server:
                skin_server.stop()

    threading.Thread(target=_launch, daemon=False).start()
