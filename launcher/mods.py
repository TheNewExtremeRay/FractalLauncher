"""
Mod Manager — search, install, and manage mods per profile.

Source: Modrinth (free, no key needed)

Mods are installed into <profile_game_dir>/mods/  so each profile has its own
isolated mod folder. Hot-swapping profiles = hot-swapping mod sets.
"""

import os
import json
import threading
import shutil
from typing import Optional, Callable

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


_session = None
_session_lock = threading.Lock()

def _get_session():
    """Return a module-level requests.Session so Modrinth API calls reuse
    the same connection/TLS handshake (urllib3's pools are thread-safe).
    Falls back to a plain requests module if requests isn't available."""
    global _session
    if not REQUESTS_AVAILABLE:
        return requests
    if _session is None:
        with _session_lock:
            if _session is None:
                s = requests.Session()
                s.headers.update(_mr_headers())
                _session = s
    return _session


def _retry_get(url, **kwargs):
    """requests.get() with automatic retry on IncompleteRead / connection errors."""
    import time as _time
    sess = _get_session()
    kwargs.setdefault("timeout", 5)
    max_retries = 3
    last_err = None
    for attempt in range(max_retries):
        try:
            r = sess.get(url, **kwargs)
            r.raise_for_status()
            return r
        except (requests.exceptions.ConnectionError,
                requests.exceptions.ChunkedEncodingError,
                requests.exceptions.ContentDecodingError) as e:
            last_err = e
            if attempt < max_retries - 1:
                _time.sleep(1 * (attempt + 1))
                continue
        except requests.exceptions.RequestException:
            raise
    raise last_err


def _sanitize_filename(filename: str) -> str:
    """Strip path components and null bytes from a filename to prevent traversal."""
    filename = os.path.basename(filename)
    filename = filename.replace("\x00", "")
    return filename

# ── Constants ─────────────────────────────────────────────────────────────────

MODRINTH_API = "https://api.modrinth.com/v2"

_LOADER_MAP = {
    "fabric":   "fabric",
    "forge":    "forge",
    "quilt":    "quilt",
    "neoforge": "neoforge",
    "vanilla":  "",
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def _mr_headers() -> dict:
    return {"User-Agent": "FractalLauncher/1.0 (contact@FractalLauncher.dev)"}


def _get_profile_mods_dir(profile_game_dir: str) -> str:
    return os.path.join(profile_game_dir, "mods")


# ── Mod data structure ────────────────────────────────────────────────────────

class Mod:
    __slots__ = (
        "id", "source", "name", "slug", "description", "author",
        "downloads", "icon_url", "versions", "categories",
    )

    def __init__(self, id, source, name, slug, description,
                 author, downloads, icon_url, versions=None, categories=None):
        self.id          = id
        self.source      = source
        self.name        = name
        self.slug        = slug
        self.description = description
        self.author      = author
        self.downloads   = downloads
        self.icon_url    = icon_url
        self.versions    = versions or []
        self.categories  = categories or []


class ModVersion:
    __slots__ = ("id", "name", "mc_versions", "loaders", "filename", "download_url", "size_bytes")

    def __init__(self, id, name, mc_versions, loaders, filename, download_url, size_bytes=0):
        self.id           = id
        self.name         = name
        self.mc_versions  = mc_versions
        self.loaders      = loaders
        self.filename     = filename
        self.download_url = download_url
        self.size_bytes   = size_bytes


# ── Modrinth ──────────────────────────────────────────────────────────────────

def _modrinth_search(query: str, mc_version: str, loader: str,
                     limit: int = 20, offset: int = 0):
    if not REQUESTS_AVAILABLE:
        return None
    try:
        facets = [[f"project_type:mod"]]
        if mc_version:
            facets.append([f"versions:{mc_version}"])
        if loader and loader != "vanilla":
            facets.append([f"categories:{loader}"])

        params = {
            "query":  query,
            "facets": json.dumps(facets),
            "limit":  limit,
            "offset": offset,
            "index":  "relevance",
        }
        r = _retry_get(f"{MODRINTH_API}/search", params=params,
                       headers=_mr_headers(), timeout=5)
        hits = r.json().get("hits", [])
        mods = []
        for h in hits:
            mods.append(Mod(
                id          = h.get("project_id", h.get("slug", "")),
                source      = "modrinth",
                name        = h.get("title", ""),
                slug        = h.get("slug", ""),
                description = h.get("description", ""),
                author      = h.get("author", ""),
                downloads   = h.get("downloads", 0),
                icon_url    = h.get("icon_url", ""),
                categories  = h.get("categories", []),
            ))
        return mods
    except Exception as e:
        print(f"[Modrinth] Search error: {e}")
        return None


def _modrinth_versions(project_id: str, mc_version: str,
                       loader: str, skip_loader: bool = False) -> list[ModVersion]:
    if not REQUESTS_AVAILABLE:
        return []
    try:
        params = {}
        if mc_version:
            params["game_versions"] = json.dumps([mc_version])
        if loader and loader != "vanilla" and not skip_loader:
            params["loaders"] = json.dumps([loader])
        r = _retry_get(f"{MODRINTH_API}/project/{project_id}/version",
                       params=params, headers=_mr_headers(), timeout=5)
        versions = []
        for v in r.json():
            files = v.get("files", [])
            primary = next((f for f in files if f.get("primary")), files[0] if files else {})
            versions.append(ModVersion(
                id           = v.get("id", ""),
                name         = v.get("name", v.get("version_number", "")),
                mc_versions  = v.get("game_versions", []),
                loaders      = v.get("loaders", []),
                filename     = primary.get("filename", ""),
                download_url = primary.get("url", ""),
                size_bytes   = primary.get("size", 0),
            ))
        return versions
    except Exception as e:
        print(f"[Modrinth] Versions error: {e}")
        return []


# ── Public API ────────────────────────────────────────────────────────────────

def search_mods(query: str, mc_version: str, loader: str,
                on_results: Callable[[list[Mod]], None] = None,
                on_done: Callable[[bool, str], None] = None,
                offset: int = 0,
                limit: int = 20):
    """
    Search mods from Modrinth in a background thread.
    on_results(mods) called with results when done.
    on_done(success, error_msg) called at end.
    """
    def _run():
        try:
            mr = _modrinth_search(query, mc_version, loader, limit=limit, offset=offset)
            if mr is None:
                if on_results:
                    on_results([])
                if on_done:
                    on_done(False, "Could not reach Modrinth. Check your internet connection.")
                return
            if on_results:
                on_results(mr)
            if on_done:
                on_done(True, "")
        except Exception as e:
            if on_done:
                on_done(False, str(e))

    threading.Thread(target=_run, daemon=True).start()


def get_mod_versions(mod: Mod, mc_version: str, loader: str,
                     on_done: Callable[[list[ModVersion]], None],
                     skip_loader: bool = False):
    """Fetch available versions for a mod in a background thread."""
    def _run():
        versions = _modrinth_versions(mod.id, mc_version, loader, skip_loader=skip_loader)
        if on_done:
            on_done(versions)
    threading.Thread(target=_run, daemon=True).start()


def install_mod(version: ModVersion, mods_dir: str,
                on_progress: Callable[[int, int], None] = None,
                on_done: Callable[[bool, str], None] = None):
    """
    Download a mod file into mods_dir.
    on_progress(bytes_downloaded, total_bytes)
    on_done(success, filepath_or_error)
    """
    def _run():
        if not REQUESTS_AVAILABLE:
            if on_done:
                on_done(False, "requests library not installed")
            return
        if not version.download_url:
            if on_done:
                on_done(False, "No download URL available")
            return
        try:
            os.makedirs(mods_dir, exist_ok=True)
            safe_name = _sanitize_filename(version.filename) or "download.jar"
            dest = os.path.join(mods_dir, safe_name)
            import time as _time
            _last_dl_err = None
            r = None
            _sess = _get_session()
            for _attempt in range(3):
                try:
                    r = _sess.get(version.download_url, stream=True,
                                  timeout=30)
                    r.raise_for_status()
                    break
                except (requests.exceptions.ConnectionError,
                        requests.exceptions.ChunkedEncodingError,
                        requests.exceptions.ContentDecodingError) as _e:
                    _last_dl_err = _e
                    if r:
                        r.close()
                        r = None
                    if _attempt < 2:
                        _time.sleep(2 * (_attempt + 1))
                        continue
                    raise
            try:
                total = int(r.headers.get("Content-Length", 0)) if r.headers.get("Content-Length", "").strip().isdigit() else 0
            except (ValueError, TypeError):
                total = 0
            downloaded = 0
            try:
                with open(dest, "wb") as f:
                    for chunk in r.iter_content(chunk_size=65536):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if on_progress:
                                on_progress(downloaded, total)
            except Exception:
                try:
                    os.remove(dest)
                except OSError:
                    pass
                raise
            finally:
                if r:
                    r.close()
            if on_done:
                on_done(True, dest)
        except Exception as e:
            if on_done:
                on_done(False, str(e))

    threading.Thread(target=_run, daemon=True).start()


def remove_mod(filename: str, mods_dir: str) -> bool:
    """Delete a mod .jar from the mods directory. Returns True on success."""
    try:
        safe = _sanitize_filename(filename)
        if not safe:
            return False
        path = os.path.join(mods_dir, safe)
        real_mods = os.path.realpath(mods_dir)
        real_path = os.path.realpath(path)
        if not real_path.startswith(real_mods + os.sep) and real_path != real_mods:
            return False
        if os.path.isfile(path):
            os.remove(path)
            return True
        return False
    except Exception:
        return False


def list_installed_mods(mods_dir: str) -> list[str]:
    """Return list of .jar filenames in the mods directory."""
    if not os.path.isdir(mods_dir):
        return []
    return sorted(f for f in os.listdir(mods_dir)
                  if f.lower().endswith((".jar", ".zip")))


def format_downloads(n: int) -> str:
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}k"
    return str(n)


def format_size(n: int) -> str:
    if n >= 1_048_576:
        return f"{n/1_048_576:.1f} MB"
    if n >= 1024:
        return f"{n/1024:.1f} KB"
    return f"{n} B"


# ── Shaders & Resource Packs ──────────────────────────────────────────────────
# Modrinth project types: "shader" | "resourcepack"

_MR_TYPE_MAP = {
    "shader":       "shader",
    "resourcepack": "resourcepack",
    "mod":          "mod",
}


def _modrinth_search_typed(query: str, mc_version: str, project_type: str,
                            loader: str = "", limit: int = 20, offset: int = 0):
    if not REQUESTS_AVAILABLE:
        return None
    try:
        facets = [[f"project_type:{project_type}"]]
        if mc_version:
            facets.append([f"versions:{mc_version}"])
        if loader and loader not in ("vanilla", "") and project_type == "mod":
            facets.append([f"categories:{loader}"])
        params = {
            "query":  query,
            "facets": json.dumps(facets),
            "limit":  limit,
            "offset": offset,
            "index":  "relevance",
        }
        r = _retry_get(f"{MODRINTH_API}/search", params=params,
                       headers=_mr_headers(), timeout=5)
        mods = []
        for h in r.json().get("hits", []):
            mods.append(Mod(
                id          = h.get("project_id", h.get("slug", "")),
                source      = "modrinth",
                name        = h.get("title", ""),
                slug        = h.get("slug", ""),
                description = h.get("description", ""),
                author      = h.get("author", ""),
                downloads   = h.get("downloads", 0),
                icon_url    = h.get("icon_url", ""),
                categories  = h.get("categories", []),
            ))
        return mods
    except Exception as e:
        print(f"[Modrinth:{project_type}] {e}")
        return None


def search_content(query: str, mc_version: str, content_type: str,
                   loader: str = "",
                   on_results=None, on_done=None,
                   offset: int = 0, limit: int = 20):
    """
    Generic content search — works for shaders, resourcepacks.
    content_type: "shader" | "resourcepack"
    """
    mr_type = _MR_TYPE_MAP.get(content_type, "mod")

    def _run():
        try:
            mr = _modrinth_search_typed(query, mc_version, mr_type, loader,
                                       limit=limit, offset=offset)
            if mr is None:
                if on_results:
                    on_results([])
                if on_done:
                    on_done(False, "Could not reach Modrinth. Check your internet connection.")
                return
            if on_results:
                on_results(mr)
            if on_done:
                on_done(True, "")
        except Exception as e:
            if on_done:
                on_done(False, str(e))

    threading.Thread(target=_run, daemon=True).start()


def list_installed_content(directory: str) -> list[str]:
    """List installed files in a directory (.zip, .jar for resourcepacks/shaders)."""
    if not os.path.isdir(directory):
        return []
    return sorted(f for f in os.listdir(directory)
                  if f.lower().endswith((".zip", ".jar")))


# ══════════════════════════════════════════════════════════════════════════════
#  DEPENDENCY RESOLVER
# ══════════════════════════════════════════════════════════════════════════════

def fetch_mod_dependencies(project_id: str, mc_version: str,
                           loader: str) -> list[dict]:
    """
    Given a Modrinth project_id, return a list of required dependency dicts:
      {"project_id": str, "name": str, "slug": str, "required": bool}
    """
    if not REQUESTS_AVAILABLE:
        return []
    try:
        url = f"{MODRINTH_API}/project/{project_id}/version"
        params = {"game_versions": f'["{mc_version}"]', "loaders": f'["{loader}"]'}
        r = _retry_get(url, params=params, headers=_mr_headers(), timeout=5)
        versions = r.json()
        if not versions:
            return []
        latest = versions[0]
        deps = []
        for dep in latest.get("dependencies", []):
            if dep.get("dependency_type") not in ("required", "optional"):
                continue
            pid = dep.get("project_id")
            if not pid:
                continue
            try:
                proj = _retry_get(f"{MODRINTH_API}/project/{pid}",
                                  headers=_mr_headers(), timeout=5).json()
                deps.append({
                    "project_id": pid,
                    "name":       proj.get("title", pid),
                    "slug":       proj.get("slug", pid),
                    "required":   dep["dependency_type"] == "required",
                })
            except Exception:
                deps.append({"project_id": pid, "name": pid,
                             "slug": pid, "required": True})
        return deps
    except Exception:
        return []


def check_mod_updates(installed_filenames: list[str], mc_version: str,
                      loader: str) -> dict[str, str]:
    """
    For each installed .jar, try to match a Modrinth project and check for updates.
    Returns {filename: "update_available" | "up_to_date" | "unknown"}
    """
    if not REQUESTS_AVAILABLE:
        return {}
    results = {}
    for fname in installed_filenames:
        slug = fname.replace(".jar","").split("-")[0].lower()
        try:
            r = _retry_get(f"{MODRINTH_API}/project/{slug}",
                           headers=_mr_headers(), timeout=5)
            if r.status_code != 200:
                results[fname] = "unknown"
                continue
            proj = r.json()
            vr = _retry_get(f"{MODRINTH_API}/project/{proj['id']}/version",
                            headers=_mr_headers(), timeout=5,
                            params={"game_versions": f'["{mc_version}"]',
                                    "loaders": f'["{loader}"]'})
            vers = vr.json() if vr.status_code == 200 else []
            if not vers:
                results[fname] = "unknown"
                continue
            latest_file = vers[0].get("files", [{}])[0].get("filename", "")
            results[fname] = "up_to_date" if latest_file == fname else "update_available"
        except Exception:
            results[fname] = "unknown"
    return results
