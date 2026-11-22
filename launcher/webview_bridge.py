"""
webview_bridge.py — JavaScript ↔ Python bridge for FractalLauncher's webview UI.

All public methods on this class are callable from JS via:
    window.pywebview.api.methodName(args)

The bridge holds references to the ProfileManager and all game functions,
keeping ALL existing backend logic intact.
"""

import os
import json
import shutil
import threading
import traceback
import re
import time
from typing import Optional


def _safe_path(filename: str, allowed_dir: str) -> str | None:
    """Validate that filename resolves inside allowed_dir. Returns the joined
    path if safe, or None if it would escape the directory."""
    safe = os.path.basename(filename)
    if not safe:
        return None
    joined = os.path.join(allowed_dir, safe)
    real_allowed = os.path.realpath(allowed_dir)
    real_joined = os.path.realpath(joined)
    if real_joined.startswith(real_allowed + os.sep) or real_joined == real_allowed:
        return joined
    return None


def _extract_mc_version(version_str: str, mc_dir: str = None) -> str:
    """Extract Minecraft version from any version string.
    Handles: '1.8.9', 'forge-1.8.9-14.25.1.2854', 'fabric-loader-0.16.14-1.21', etc.
    Now accepts ANY version (e.g., 26.1.2, 23.2.1) not just 1.x.x formats.

    Order of trust:
      1. The installed version JSON's 'inheritsFrom' — authoritative for
         loader installs (fabric/quilt/forge ids inherit the vanilla parent,
         e.g. 'fabric-loader-0.19.5-26.3' inheritsFrom '26.3').
      2. Numeric scan of the id itself. Fabric/Quilt ids embed the LOADER
         version BEFORE the MC version, so those take the LAST match;
         everything else keeps the first match ('1.19.2-forge-43.3.0' ->
         '1.19.2', '26.1.2' -> '26.1.2'). The old first-match rule returned
         the loader version '0.19.5' for imported profiles, which sent
         Modrinth searches/install checks after a non-existent MC version."""
    version_str = str(version_str or "").strip()
    # 1) Authoritative: an installed loader json points at its vanilla parent
    if mc_dir and version_str:
        try:
            vjson = os.path.join(mc_dir, "versions", version_str,
                                 version_str + ".json")
            if os.path.isfile(vjson):
                with open(vjson, "r", encoding="utf-8") as f:
                    inherits = str(json.load(f).get("inheritsFrom") or "").strip()
                if inherits and re.match(r"\d+\.\d+", inherits):
                    return inherits
        except Exception:
            pass
    # 2) Numeric scan of the id itself
    matches = re.findall(r"\d+\.\d+(?:\.\d+)?", version_str)
    if matches:
        if re.match(r"(?i)^(fabric|quilt)[-_]loader", version_str):
            return matches[-1]   # loader version comes first in these ids
        return matches[0]
    return version_str


# ── Diagnostics helpers (module-level, cached) ────────────────────────────────

_HW_CACHE = {"ts": 0.0, "cpu": "", "gpu": "", "cores": 0, "logical": 0, "driver": ""}


def _diag_hw_probe(force: bool = False):
    """Best-effort CPU/GPU names via one PowerShell call (cached 5 min).
    Returns (cpu_name, gpu_name). Fail-soft: empty strings on any error."""
    now = time.time()
    if not force and now - _HW_CACHE["ts"] < 300 and _HW_CACHE["cpu"]:
        return _HW_CACHE["cpu"], _HW_CACHE["gpu"]
    import platform as _plat
    if _plat.system() != "Windows":
        _HW_CACHE["ts"] = now
        return "", ""
    import subprocess as _sp
    script = (
        "$o=@{};"
        "$c=Get-CimInstance Win32_Processor|Select-Object -First 1 Name,NumberOfCores,NumberOfLogicalProcessors;"
        "if($c){$o.cpu=$c.Name;$o.cores=$c.NumberOfCores;$o.logical=$c.NumberOfLogicalProcessors};"
        "$g=Get-CimInstance Win32_VideoController|Select-Object -First 1 Name,DriverVersion;"
        "if($g){$o.gpu=$g.Name;$o.driver=$g.DriverVersion};"
        "$o|ConvertTo-Json -Compress"
    )
    try:
        out = _sp.run(["powershell", "-NoProfile", "-Command", script],
                      capture_output=True, text=True, timeout=5)
        if out.returncode == 0 and out.stdout.strip():
            data = json.loads(out.stdout)
            _HW_CACHE.update(
                ts=now,
                cpu=str(data.get("cpu") or ""),
                gpu=str(data.get("gpu") or ""),
                cores=int(data.get("cores") or 0),
                logical=int(data.get("logical") or 0),
                driver=str(data.get("driver") or ""),
            )
    except Exception:
        _HW_CACHE["ts"] = now
    return _HW_CACHE["cpu"], _HW_CACHE["gpu"]


def _diag_tcp_ok(host: str, port: int = 443, timeout: float = 2.0) -> bool:
    import socket
    try:
        s = socket.create_connection((host, port), timeout=timeout)
        s.close()
        return True
    except Exception:
        return False


def _diag_dir_stats(path: str, max_files: int = 200000):
    """Return (total_bytes, file_count, truncated)."""
    total = 0
    count = 0
    for root, _dirs, files in os.walk(path):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
            count += 1
            if count >= max_files:
                return total, count, True
    return total, count, False


def _diag_java_version(java_path: str) -> str:
    """Run `java -version` and return the major version as a string ('' on fail)."""
    import subprocess as _sp
    try:
        proc = _sp.run([java_path, "-version"], capture_output=True,
                       text=True, timeout=6)
        blob = (proc.stderr or "") + (proc.stdout or "")
        m = re.search(r'version "(\d+)(?:\.(\d+))?', blob)
        if m:
            major = int(m.group(1))
            if major == 1 and m.group(2):
                major = int(m.group(2))
            return str(major)
    except Exception:
        pass
    return ""


def _diag_mem_status():
    """Return (total_bytes, available_bytes) — (0, 0) if unknown."""
    import platform as _plat
    try:
        if _plat.system() == "Windows":
            import ctypes

            class _MS(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]

            m = _MS()
            m.dwLength = ctypes.sizeof(_MS)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m)):
                return m.ullTotalPhys, m.ullAvailPhys
        elif hasattr(os, "sysconf"):
            page = os.sysconf("SC_PAGE_SIZE")
            total = page * os.sysconf("SC_PHYS_PAGES")
            try:
                avail = page * os.sysconf("SC_AVPHYS_PAGES")
            except Exception:
                avail = 0
            return total, avail
    except Exception:
        pass
    return 0, 0


def _detect_loader(version_id: str, vjson_path: str = "") -> str:
    """Best-effort mod-loader detection from a version id and/or its JSON."""
    blob = (version_id or "").lower()
    if "fabric" in blob:
        return "fabric"
    if "quilt" in blob:
        return "quilt"
    if "neoforge" in blob or "neo-forge" in blob:
        return "neoforge"
    if "forge" in blob:
        return "forge"
    if vjson_path and os.path.isfile(vjson_path):
        try:
            with open(vjson_path, encoding="utf-8") as f:
                data = json.load(f)
            libs = json.dumps(data.get("libraries", [])).lower()
            if "fabricmc" in libs:
                return "fabric"
            if "quiltmc" in libs:
                return "quilt"
            if "neoforge" in libs:
                return "neoforge"
            if "minecraftforge" in libs:
                return "forge"
            main = str(data.get("mainClass", "")).lower()
            if "fabric" in main:
                return "fabric"
            if "quilt" in main:
                return "quilt"
            if "forge" in main:
                return "forge"
        except Exception:
            pass
    return "vanilla"


def _version_base(mc_root, vid):
    """Minecraft base version of a version id — prefers the version JSON's
    inheritsFrom so loader ids like 'fabric-loader-0.19.5-26.3' map to
    '26.3' instead of the loader version ('0.19.5')."""
    vid = str(vid or "")
    vjson = os.path.join(mc_root, "versions", vid, f"{vid}.json")
    if vid and os.path.isfile(vjson):
        try:
            with open(vjson, encoding="utf-8") as f:
                inherits = str(json.load(f).get("inheritsFrom") or "").strip()
            if inherits:
                return inherits
        except Exception:
            pass
    return _extract_mc_version(vid, mc_root)


def _version_json_ok(mc_root, vid):
    """True when versions/<vid>/<vid>.json exists AND is a real version
    manifest (has 'libraries'). Guards against stub/partial json files
    that would make is_version_installed() return True but crash
    command building with KeyError('libraries')."""
    vjson = os.path.join(mc_root, "versions", vid, f"{vid}.json")
    try:
        with open(vjson, encoding="utf-8") as f:
            return "libraries" in json.load(f)
    except Exception:
        return False


def _inherited_base_ids(mc_root):
    """Version ids that exist only as an 'inheritsFrom' parent of an
    installed loader version (fabric/forge installs pull the base json+jar
    down as a dependency) — they are not standalone vanilla installs."""
    out = set()
    vdir = os.path.join(mc_root, "versions")
    try:
        for name in os.listdir(vdir):
            vjson = os.path.join(vdir, name, name + ".json")
            if not os.path.isfile(vjson):
                continue
            try:
                with open(vjson, encoding="utf-8") as f:
                    inh = str(json.load(f).get("inheritsFrom") or "").strip()
                if inh:
                    out.add(inh)
            except Exception:
                continue
    except Exception:
        pass
    return out


def _profile_coverage(mc_root, profiles):
    """(exact version ids, (base, loader) pairs) already covered by FL
    profiles. Loader-aware: a vanilla profile on '26.3' does NOT cover
    'fabric-loader-…-26.3' — matching _find_installed_version, which
    resolves loaders per profile."""
    versions = set()
    pairs = set()
    for p in (profiles or []):
        pv = str(getattr(p, "version", "") or "")
        if not pv:
            continue
        versions.add(pv)
        vjson = os.path.join(mc_root, "versions", pv, pv + ".json")
        detected = _detect_loader(pv, vjson if os.path.isfile(vjson) else "")
        loader = detected if detected != "vanilla" else (
            str(getattr(p, "mod_loader", "") or "").lower() or "vanilla")
        pairs.add((_version_base(mc_root, pv), loader))
    return versions, pairs


_UUID_DIR_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")


def _orphan_profile_dirs(mc_root, profiles):
    """Per-profile game folders under FractalLauncher_profiles/ that no
    current profile references — left behind when profiles.json is reset
    or a profile entry is lost. Folder names ARE profile ids (uuid4)."""
    base = os.path.join(mc_root, "FractalLauncher_profiles")
    used = {str(getattr(p, "id", "") or "") for p in (profiles or [])}
    out = []
    try:
        for name in sorted(os.listdir(base)):
            if (_UUID_DIR_RE.match(name) and name not in used
                    and os.path.isdir(os.path.join(base, name))):
                out.append(name)
    except OSError:
        pass
    return out


def _adopt_profile_dir_id(mc_root, profiles, loader):
    """Pick an orphaned profile folder for an imported profile so "Add"
    reattaches to the user's existing content (mods/saves/resourcepacks/
    shaders) instead of creating a fresh empty folder. A single orphan is
    adopted outright; with several, only an unambiguous loader marker
    (.fabric / .quilt) picks one — otherwise "" keeps the old new-id behavior."""
    orphans = _orphan_profile_dirs(mc_root, profiles)
    if not orphans:
        return ""
    if len(orphans) == 1:
        return orphans[0]
    marker = {"fabric": ".fabric", "quilt": ".quilt"}.get(
        (loader or "").lower(), "")
    if marker:
        base = os.path.join(mc_root, "FractalLauncher_profiles")
        matches = [n for n in orphans
                   if os.path.isdir(os.path.join(base, n, marker))]
        if len(matches) == 1:
            return matches[0]
    return ""


def _find_installed_version(mc_root, vid, base_vid, loader_want):
    """Find an installed version folder that fulfils profile version `vid`,
    honouring the profile's mod loader. Mirrors the launch flow's _find_loader:
    e.g. vid '26.3' + loader 'fabric' matches 'fabric-loader-0.19.5-26.3'.
    Returns the folder name or ''."""
    loader_want = (loader_want or "vanilla").lower()
    vroot = os.path.join(mc_root, "versions")
    installed = []
    try:
        from .game import get_installed_versions
        installed = list(get_installed_versions(mc_root))
    except Exception:
        try:
            installed = [n for n in os.listdir(vroot)
                         if os.path.isfile(os.path.join(vroot, n, n + ".json"))]
        except Exception:
            installed = []
    # Step 1: same base version + wanted loader in the id (mll style)
    if base_vid:
        for cand in installed:
            if base_vid in cand and loader_want in cand.lower():
                return cand
    # Step 2: exact id match (loader must match for loader profiles)
    for cand in installed:
        if vid == cand and (loader_want == "vanilla" or loader_want in cand.lower()):
            return cand
    # Step 3: directory scan — loader in name, or JSON inheritsFrom == base
    try:
        for name in sorted(os.listdir(vroot)) if os.path.isdir(vroot) else []:
            njson = os.path.join(vroot, name, name + ".json")
            if not os.path.isfile(njson):
                continue
            if base_vid and base_vid in name and loader_want in name.lower():
                return name
            inherits = ""
            try:
                with open(njson, encoding="utf-8") as f:
                    inherits = str(json.load(f).get("inheritsFrom") or "")
            except Exception:
                continue
            if base_vid and inherits == base_vid:
                detected = _detect_loader(name, njson)
                if detected == loader_want:
                    return name
    except Exception:
        pass
    return ""


def _diagnose_game_version(mc_root, vid, loader):
    """(status, detail) for the 'Game version' diagnostics check —
    mod-loader aware: recognises loader-prefixed installs (e.g. a profile
    on '26.3' matches 'fabric-loader-0.19.5-26.3') and reports a missing
    loader separately from a missing game."""
    loader = (loader or "vanilla")
    loader_want = loader.lower()
    vdir = os.path.join(mc_root, "versions", vid)
    jar = os.path.join(vdir, f"{vid}.jar")
    vjson = os.path.join(vdir, f"{vid}.json")
    base_vid = _extract_mc_version(vid, mc_root)
    base_jar = os.path.join(mc_root, "versions", base_vid, f"{base_vid}.jar")
    base_vjson = os.path.join(mc_root, "versions", base_vid, f"{base_vid}.json")
    equiv = _find_installed_version(mc_root, vid, base_vid, loader_want)
    equiv_jar = os.path.join(mc_root, "versions", equiv, f"{equiv}.jar") if equiv else ""
    equiv_vjson = os.path.join(mc_root, "versions", equiv, f"{equiv}.json") if equiv else ""
    if equiv and os.path.isfile(equiv_jar):
        return "ok", f"{vid} installed" + (f" (via {equiv})" if equiv != vid else "")
    if os.path.isfile(jar):
        if loader_want != "vanilla":
            return "warn", (f"{loader} loader not installed for {base_vid} — "
                            "installs on first launch")
        return "ok", f"{vid} installed" + (f" (base {base_vid})" if base_vid != vid else "")
    if os.path.isfile(vjson):
        return "warn", f"{vid} JSON present but jar missing — will repair on launch"
    if equiv and os.path.isfile(equiv_vjson):
        return "warn", f"{equiv} JSON present but jar missing — will repair on launch"
    if os.path.isfile(base_jar) or os.path.isfile(base_vjson):
        if loader_want != "vanilla":
            return "warn", (f"{loader} loader not installed for {base_vid} — "
                            "installs on first launch")
        return "ok", f"{vid} installed" + (f" (base {base_vid})" if base_vid != vid else "")
    return "warn", f"{vid} not installed yet — downloads on first launch"


class API:
    """
    Exposed to JavaScript as window.pywebview.api
    All methods must be synchronous (pywebview handles threading).
    Methods return dicts that JS receives as plain objects.
    """

    def __init__(self):
        self._window   = None   # set after webview.create_window
        self._pm       = None   # ProfileManager — set in attach()
        self._console_lines = []
        self._console_queue = []            # pending console lines not yet flushed to JS
        self._console_queue_lock = threading.Lock()
        self._console_flush_timer = None
        self._launch_running = False
        self._game_process = None
        self._hidden_for_game = False   # window hidden by "hide on game" setting

    def attach(self, pm, window):
        from .profiles import ProfileManager
        self._pm     = pm
        self._window = window
        # Warm the version manifest cache in background so "+ New Profile" is instant
        threading.Thread(target=self._prefetch_versions, daemon=True).start()

    # ── helpers ──────────────────────────────────────────────────────────────

    def _ok(self, **data):
        return {"ok": True, **data}

    def _err(self, msg):
        return {"ok": False, "error": str(msg)}

    def _push(self, event: str, data: dict):
        """Push a server-side event to the JS side."""
        if not self._window:
            return
        if event == "console_line":
            with self._console_queue_lock:
                self._console_queue.append(data)
            if len(self._console_queue) >= 100:
                self._flush_console_queue()
            else:
                with self._console_queue_lock:
                    if self._console_flush_timer is None:
                        t = threading.Timer(0.05, self._flush_console_queue)
                        t.daemon = True
                        self._console_flush_timer = t
                        t.start()
            return
        self._flush_console_queue()   # preserve ordering: flush queued lines first
        payload = json.dumps(data).replace("'", "\\'")
        self._window.evaluate_js(
            f"window.dispatchEvent(new CustomEvent('{event}', {{detail: {payload}}}))"
        )

    def _flush_console_queue(self):
        """Flush all queued console_line events in one evaluate_js call."""
        with self._console_queue_lock:
            if self._console_flush_timer is not None:
                self._console_flush_timer.cancel()
                self._console_flush_timer = None
            if not self._console_queue:
                return
            batch = self._console_queue[:]
            self._console_queue.clear()
        if not self._window:
            return
        parts = []
        for d in batch:
            line = json.dumps(d.get("line", "")).replace("'", "\\'")
            parts.append(
                f"window.dispatchEvent(new CustomEvent('console_line', {{detail: {{line: {line}}}}}))")
        self._window.evaluate_js(";".join(parts))

    def _prefetch_versions(self):
        """Warm the version cache on startup so list_versions is instant later."""
        try:
            from .game import list_versions
            list_versions("release")
        except Exception:
            pass

    # ── Profile Manager ───────────────────────────────────────────────────────

    def get_profiles(self):
        try:
            pm = self._pm
            profiles = []
            for p in pm.profiles:
                profiles.append({
                    "id":        p.id,
                    "name":      p.name,
                    "version":   p.version,
                    "modLoader": p.mod_loader,
                    "modLoaderVersion": p.mod_loader_version,
                    "ramMb":     p.ram_mb,
                    "jvmArgs":   p.jvm_args,
                    "gameDir":   p.game_dir,
                    "resolutionW": p.resolution_w,
                    "resolutionH": p.resolution_h,
                    "fullscreen":  p.fullscreen,
                    "accountId": p.account_id,
                    "active":    p.id == pm.active_profile_id,
                })
            return self._ok(profiles=profiles)
        except Exception as e:
            return self._err(e)

    def get_active_profile(self):
        try:
            p = self._pm.active_profile
            if not p:
                return self._ok(profile=None)
            return self._ok(profile={
                "id":        p.id,
                "name":      p.name,
                "version":   p.version,
                "modLoader": p.mod_loader,
                "modLoaderVersion": p.mod_loader_version,
                "ramMb":     p.ram_mb,
                "jvmArgs":   p.jvm_args,
                "gameDir":   p.game_dir,
                "resolutionW": p.resolution_w,
                "resolutionH": p.resolution_h,
                "fullscreen":  p.fullscreen,
            })
        except Exception as e:
            return self._err(e)

    def set_active_profile(self, profile_id: str):
        try:
            self._pm.active_profile_id = profile_id
            self._pm.save()
            return self._ok()
        except Exception as e:
            return self._err(e)

    def create_profile(self, name: str, version: str, mod_loader: str,
                       ram_mb: int = 4096, jvm_args: str = ""):
        try:
            from .profiles import Profile
            import uuid as _uuid
            p = Profile(
                id=str(_uuid.uuid4()),
                name=name,
                version=version,
                mod_loader=mod_loader.lower(),
                mod_loader_version="latest",
                account_id=self._pm.active_account_id or "",
                ram_mb=ram_mb,
                jvm_args=jvm_args,
                game_dir="",
            )
            self._pm.profiles.append(p)
            self._pm.active_profile_id = p.id
            self._pm.save()
            return self._ok(profile_id=p.id)
        except Exception as e:
            return self._err(e)

    def delete_profile(self, profile_id: str):
        try:
            prof = next((p for p in self._pm.profiles
                         if p.id == profile_id), None)
            self._pm.profiles = [p for p in self._pm.profiles if p.id != profile_id]
            if self._pm.active_profile_id == profile_id:
                self._pm.active_profile_id = self._pm.profiles[0].id if self._pm.profiles else None
            self._pm.save()
            if prof is not None:
                self._delete_profile_folder(prof)
            return self._ok()
        except Exception as e:
            return self._err(e)

    def _delete_profile_folder(self, profile):
        """Remove the profile's FL-managed game folder
        (FractalLauncher_profiles/<profile id>) together with its
        mods/saves/resourcepacks/shaders, so deleting a profile also frees
        its storage. Never touches the .minecraft root itself or anything
        outside that per-profile directory."""
        try:
            import shutil
            from .game import get_minecraft_dir
            root = get_minecraft_dir(profile)
            base = os.path.normpath(
                os.path.join(root, "FractalLauncher_profiles"))
            path = os.path.normpath(
                os.path.join(base, str(getattr(profile, "id", "") or "")))
            if os.path.dirname(path) == base and os.path.isdir(path):
                shutil.rmtree(path, ignore_errors=True)
        except Exception:
            pass

    def update_profile(self, profile_id: str, data: dict = None):
        """Update profile fields. Accepts both camelCase and snake_case keys."""
        try:
            if not data:
                return self._ok()
            # Map camelCase JS keys to snake_case Python attrs
            key_map = {"ramMb": "ram_mb", "modLoader": "mod_loader",
                       "modLoaderVersion": "mod_loader_version",
                       "gameDir": "game_dir", "jvmArgs": "jvm_args",
                       "resolutionW": "resolution_w", "resolutionH": "resolution_h"}
            int_fields = {"ram_mb", "resolution_w", "resolution_h"}
            bool_fields = {"fullscreen"}
            for p in self._pm.profiles:
                if p.id == profile_id:
                    for k, v in data.items():
                        attr = key_map.get(k, k)
                        if hasattr(p, attr):
                            if attr in int_fields:
                                v = int(v)
                            elif attr in bool_fields:
                                v = bool(v)
                            setattr(p, attr, v)
            self._pm.save()
            return self._ok()
        except Exception as e:
            return self._err(e)

    def edit_jvm_notepad(self, text: str = ""):
        """Open JVM arguments in Notepad for editing. Blocks until Notepad closes, returns edited text."""
        import tempfile
        import subprocess
        import sys as _sys
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".txt", prefix="jvm_args_",
                delete=False, encoding="utf-8"
            ) as f:
                f.write(text)
                tmp_path = f.name
            # Open Notepad and wait for it to close
            if _sys.platform == "win32":
                subprocess.run(["notepad.exe", tmp_path], timeout=300)
            else:
                # Fallback: try nano/vim/vi
                for editor in ["nano", "vim", "vi"]:
                    try:
                        subprocess.run([editor, tmp_path], timeout=300)
                        break
                    except FileNotFoundError:
                        continue
            # Read back the edited content
            with open(tmp_path, "r", encoding="utf-8") as f:
                result = f.read()
            # Clean up temp file
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
            return self._ok(text=result)
        except Exception as e:
            return self._err(e)

    # ── Accounts ──────────────────────────────────────────────────────────────

    def get_accounts(self):
        try:
            accounts = []
            for a in self._pm.accounts:
                accounts.append({
                    "id":       a.id,
                    "username": a.username,
                    "authType": a.auth_type,
                    "active":   a.id == self._pm.active_account_id,
                })
            return self._ok(accounts=accounts)
        except Exception as e:
            return self._err(e)

    def get_active_account(self):
        try:
            a = self._pm.active_account
            if not a:
                return self._ok(account=None)
            return self._ok(account={
                "id":       a.id,
                "username": a.username,
                "authType": a.auth_type,
                "skinPath": getattr(a, "skin_path", "") or "",
                "skinUrl":  getattr(a, "skin_url", "") or "",
                "skinModel": getattr(a, "skin_model", "default") or "default",
                "capePath": getattr(a, "cape_path", "") or "",
            })
        except Exception as e:
            return self._err(e)

    def add_offline_account(self, username: str):
        try:
            a = self._pm.add_offline_account(username)
            self._pm.active_account_id = a.id
            self._pm.save()
            return self._ok(account_id=a.id)
        except Exception as e:
            return self._err(e)

    def start_microsoft_login(self):
        """Start Microsoft OAuth login flow. Pushes events to JS on success/error."""
        try:
            from . import auth

            def on_success(username, mc_uuid, access_token, refresh_token, skin_url):
                a = self._pm.add_microsoft_account(
                    username, mc_uuid, access_token, refresh_token, skin_url)
                self._pm.active_account_id = a.id
                self._pm.save()
                self._push("microsoft_login_success", {
                    "accountId": a.id,
                    "username": username,
                })

            def on_error(error_msg):
                self._push("microsoft_login_error", {"error": error_msg})

            auth.start_microsoft_login(on_success, on_error)
            return self._ok()
        except Exception as e:
            return self._err(e)

    def set_active_account(self, account_id: str):
        try:
            self._pm.active_account_id = account_id
            self._pm.save()
            return self._ok()
        except Exception as e:
            return self._err(e)

    def delete_account(self, account_id: str):
        try:
            self._pm.accounts = [a for a in self._pm.accounts if a.id != account_id]
            if self._pm.active_account_id == account_id:
                self._pm.active_account_id = self._pm.accounts[0].id if self._pm.accounts else None
            self._pm.save()
            return self._ok()
        except Exception as e:
            return self._err(e)

    def set_skin(self, skin_path: str, model: str = "default"):
        try:
            a = self._pm.active_account
            if not a:
                return self._err("No active account")
            a.skin_path  = skin_path
            a.skin_model = model
            self._pm.save()
            return self._ok()
        except Exception as e:
            return self._err(e)

    def cache_skin_from_url(self, skin_url: str):
        """Download a skin from a URL and save it locally for the active account."""
        try:
            import requests as _req
            a = self._pm.active_account
            if not a:
                return self._err("No active account")
            if not skin_url:
                return self._err("No skin URL")
            cache_dir = os.path.join(os.path.expanduser("~"),
                                     ".FractalLauncher", "skins")
            os.makedirs(cache_dir, exist_ok=True)
            fname = f"{a.id}.png"
            dest = os.path.join(cache_dir, fname)
            r = _req.get(skin_url, timeout=15)
            r.raise_for_status()
            with open(dest, "wb") as f:
                f.write(r.content)
            a.skin_path = dest
            self._pm.save()
            return self._ok(path=dest)
        except Exception as e:
            return self._err(e)

    def set_cape(self, cape_path: str):
        try:
            a = self._pm.active_account
            if not a:
                return self._err("No active account")
            a.cape_path = cape_path
            self._pm.save()
            return self._ok()
        except Exception as e:
            return self._err(e)

    def clear_cape(self):
        try:
            a = self._pm.active_account
            if not a:
                return self._err("No active account")
            a.cape_path = ""
            self._pm.save()
            return self._ok()
        except Exception as e:
            return self._err(e)

    # ── Launch ────────────────────────────────────────────────────────────────

    def launch(self):
        if self._launch_running:
            return self._err("Already running")
        try:
            from .game import (launch_game, get_minecraft_dir,
                               install_version, install_mod_loader,
                               is_version_installed, get_installed_versions)
            pm      = self._pm
            profile = pm.active_profile
            account = pm.active_account
            if not profile:
                return self._err("No profile selected")
            if not account:
                return self._err("No account selected")

            # Refresh Microsoft token if expired
            if account.auth_type == "microsoft" and account.refresh_token:
                try:
                    from . import auth
                    refreshed = auth.refresh_microsoft_token(account.refresh_token)
                    if refreshed:
                        account.access_token = refreshed["access_token"]
                        account.refresh_token = refreshed.get("refresh_token", account.refresh_token)
                        self._pm.save()
                except Exception:
                    pass  # Launch anyway with existing token

            self._launch_running = True
            self._console_lines  = []
            with self._console_queue_lock:
                if self._console_flush_timer is not None:
                    self._console_flush_timer.cancel()
                    self._console_flush_timer = None
                self._console_queue.clear()
            self._push("launch_state", {"state": "launching"})

            mc_dir = get_minecraft_dir(profile)

            def _base(v):
                return _extract_mc_version(v, mc_dir)

            def _find_loader():
                base   = _base(profile.version)
                loader = profile.mod_loader.lower()
                # Step 1: Try mll installed versions (loader in name)
                try:
                    for vid in get_installed_versions(mc_dir):
                        if base in vid and loader in vid.lower():
                            return vid
                except Exception:
                    pass
                # Step 2: Try exact match on full profile.version
                try:
                    for vid in get_installed_versions(mc_dir):
                        if profile.version == vid:
                            # For mod-loader profiles, verify the version actually has the loader
                            if loader == "vanilla" or loader in vid.lower():
                                return vid
                except Exception:
                    pass
                # Step 3: Scan versions/ directory for loader + base match
                try:
                    versions_dir = os.path.join(mc_dir, "versions")
                    if os.path.isdir(versions_dir):
                        for name in os.listdir(versions_dir):
                            if base in name and loader in name.lower():
                                vjson = os.path.join(versions_dir, name, name + ".json")
                                if os.path.isfile(vjson):
                                    return name
                        # For mod-loader profiles, try profile.version as a mod-loader ID
                        # (e.g. fabric-loader-0.19.3-26.2) but only if loader is in the name
                        if loader != "vanilla":
                            vjson = os.path.join(versions_dir, profile.version, profile.version + ".json")
                            if os.path.isfile(vjson) and loader in profile.version.lower():
                                return profile.version
                except Exception:
                    pass
                return ""

            base_ver = _base(profile.version)

            def on_log(line):
                self._console_lines.append(line)
                self._push("console_line", {"line": line})

            def on_exit(code):
                self._launch_running = False
                if self._hidden_for_game:
                    self._hidden_for_game = False
                    try:
                        if self._window:
                            self._window.show()
                    except Exception:
                        pass
                self._push("launch_state", {"state": "stopped", "code": code})
                self._push("console_line", {
                    "line": f"\n[FractalLauncher] Process exited (code {code})"})

            # CRITICAL: Always accept any version format and proceed with launch
            # The installer will automatically download missing versions
            # No version validation - accept all formats (26.1.2, 1.20.1, etc.)
            on_log(f"[FractalLauncher] Attempting launch with version: {profile.version}")

            def _do_launch(p, a, vid=""):
                def _store_proc(proc):
                    self._game_process = proc
                    if self._hide_window_for_game():
                        try:
                            self._window.hide()
                            self._hidden_for_game = True
                        except Exception:
                            self._hidden_for_game = False
                launch_game(p, a, on_log=on_log, on_exit=on_exit, on_process=_store_proc,
                            version_override=vid)

            def _run():
                try:
                    base_ver = _base(profile.version)
                    loader_id = _find_loader()

                    on_log(f"[FractalLauncher] Debug     : profile.version={profile.version!r} base_ver={base_ver!r} loader_id={loader_id!r} mod_loader={profile.mod_loader!r}")

                    # ── Shared-asset pre-check ──────────────────────────────
                    from .game import check_assets_cache
                    cache_info = check_assets_cache(base_ver, mc_dir)
                    lib_c = cache_info["libraries"]
                    ast_c = cache_info["assets"]
                    if lib_c["total"] or ast_c["total"]:
                        lib_pct = int(lib_c["cached"] / max(lib_c["total"], 1) * 100)
                        ast_pct = int(ast_c["cached"] / max(ast_c["total"], 1) * 100)
                        need_mb = (lib_c["bytes_needed"] + ast_c["bytes_needed"]) / (1024*1024)
                        on_log(f"[FractalLauncher] Cache check: {lib_c['cached']}/{lib_c['total']} libs ({lib_pct}%), {ast_c['cached']}/{ast_c['total']} assets ({ast_pct}%) — ~{need_mb:.1f} MB to download")
                        self._push("assets_cache", cache_info)

                    def _make_progress_tracker():
                        """Create a progress tracker that computes speed/ETA.
                        Emits install_progress at most ~10 Hz, with a guaranteed
                        trailing final push so the bar always reaches its last state."""
                        tracker = {"start": 0, "last": 0, "last_time": 0,
                                   "samples": [], "max": 0,
                                   "last_emit": 0.0, "pending": None,
                                   "pending_timer": None}
                        lock = threading.Lock()

                        def _emit(payload, force=False):
                            now = time.time()
                            with lock:
                                if not force and (now - tracker["last_emit"]) < 0.1:
                                    tracker["pending"] = payload
                                    if tracker["pending_timer"] is None:
                                        def _flush():
                                            with lock:
                                                tracker["pending_timer"] = None
                                                p = tracker["pending"]
                                                tracker["pending"] = None
                                            if p is not None:
                                                self._push("install_progress", p)
                                        t = threading.Timer(0.1, _flush)
                                        t.daemon = True
                                        tracker["pending_timer"] = t
                                        t.start()
                                    return
                                tracker["last_emit"] = now
                                tracker["pending"] = None
                                if tracker["pending_timer"] is not None:
                                    tracker["pending_timer"].cancel()
                                    tracker["pending_timer"] = None
                            self._push("install_progress", payload)

                        def on_prog(cur, tot, status):
                            now = time.time()
                            if tracker["start"] == 0:
                                tracker["start"] = now
                                tracker["last_time"] = now
                            if tot > 0 and tracker["max"] == 0:
                                tracker["max"] = tot
                            if tot > 0:
                                tracker["max"] = tot
                            dt = now - tracker["last_time"]
                            if dt >= 0.3 and cur > tracker["last"]:
                                speed = (cur - tracker["last"]) / dt
                                tracker["samples"].append(speed)
                                if len(tracker["samples"]) > 8:
                                    tracker["samples"].pop(0)
                                tracker["last"] = cur
                                tracker["last_time"] = now

                            max_val = tracker["max"] if tracker["max"] > 0 else tot
                            frac = cur / max(max_val, 1)
                            avg_speed = (sum(tracker["samples"]) / len(tracker["samples"])) if tracker["samples"] else 0
                            remaining_bytes = max(max_val - cur, 0)
                            eta = remaining_bytes / avg_speed if avg_speed > 0 else -1
                            downloaded_mb = cur / (1024 * 1024)
                            total_mb = max_val / (1024 * 1024)
                            speed_mbs = avg_speed / (1024 * 1024)

                            payload = {
                                "status": status or "Downloading...",
                                "frac": frac,
                                "downloaded": downloaded_mb,
                                "total": total_mb,
                                "speed": speed_mbs,
                                "eta": eta,
                                "downloadedRaw": cur,
                                "totalRaw": max_val,
                            }
                            if frac >= 1.0:
                                _emit(payload, force=True)
                            else:
                                _emit(payload)
                        return on_prog

                    if profile.mod_loader == "vanilla":
                        if not (is_version_installed(base_ver, mc_dir)
                                and _version_json_ok(mc_dir, base_ver)):
                            on_prog = _make_progress_tracker()
                            def on_done(ok, msg):
                                if ok:
                                    _do_launch(profile, account)
                                else:
                                    self._launch_running = False
                                    self._push("launch_state", {"state": "error", "error": msg})
                            install_version(base_ver, mc_dir,
                                            on_progress=on_prog, on_done=on_done)
                        else:
                            _do_launch(profile, account)
                    else:
                        if loader_id:
                            if (is_version_installed(base_ver, mc_dir)
                                    and _version_json_ok(mc_dir, base_ver)):
                                _do_launch(profile, account, loader_id)
                            else:
                                # Loader folder exists but the vanilla PARENT isn't
                                # installed (fabric/forge/quilt inherit from vanilla).
                                # Install the base version first, then launch.
                                on_prog = _make_progress_tracker()
                                def after_parent(ok, msg, _lid=loader_id):
                                    if ok:
                                        _do_launch(profile, account, _lid)
                                    else:
                                        self._launch_running = False
                                        self._push("launch_state",
                                                   {"state": "error", "error": msg})
                                install_version(base_ver, mc_dir,
                                                on_progress=on_prog,
                                                on_done=after_parent)
                        else:
                            on_prog = _make_progress_tracker()
                            def after_vanilla(ok, msg):
                                if not ok:
                                    self._launch_running = False
                                    self._push("launch_state", {"state":"error","error":msg})
                                    return
                                def after_loader(ok2, ver_or_err):
                                    if ok2:
                                        _do_launch(profile, account, ver_or_err)
                                    else:
                                        self._launch_running = False
                                        self._push("launch_state",
                                                   {"state":"error","error":ver_or_err})
                                install_mod_loader(base_ver, profile.mod_loader,
                                                   profile.mod_loader_version, mc_dir,
                                                   on_progress=on_prog,
                                                   on_done=after_loader)
                            if is_version_installed(base_ver, mc_dir):
                                after_vanilla(True, "")
                            else:
                                install_version(base_ver, mc_dir,
                                                on_progress=on_prog, on_done=after_vanilla)
                except Exception as ex:
                    self._launch_running = False
                    self._push("launch_state", {"state":"error","error":str(ex)})

            threading.Thread(target=_run, daemon=True).start()
            return self._ok()
        except Exception as e:
            self._launch_running = False
            return self._err(e)

    def get_console_log(self):
        return self._ok(lines=self._console_lines)

    def clear_console(self):
        with self._console_queue_lock:
            if self._console_flush_timer is not None:
                self._console_flush_timer.cancel()
                self._console_flush_timer = None
            self._console_queue.clear()
        self._console_lines = []
        self._push("console_clear", {})
        return self._ok()

    def check_assets(self, version_id: str = ""):
        """Check how many libraries/assets are already cached for a version."""
        try:
            from .game import check_assets_cache, get_minecraft_dir
            p = self._pm.active_profile
            mc_dir = get_minecraft_dir(p) if p else None
            if not mc_dir:
                return self._err("No profile")
            if not version_id and p:
                version_id = _extract_mc_version(p.version, mc_dir)
            if not version_id:
                return self._err("No version specified")
            result = check_assets_cache(version_id, mc_dir)
            return self._ok(**result)
        except Exception as e:
            return self._err(e)

    def kill_game(self):
        """Kill the running Minecraft process."""
        if self._game_process:
            try:
                import signal
                import sys
                if sys.platform == "win32":
                    self._game_process.terminate()
                else:
                    self._game_process.send_signal(signal.SIGTERM)
                self._push("console_line", {"line": "\n[FractalLauncher] ⚠ Game process killed by user"})
                return self._ok()
            except Exception as e:
                return self._err(str(e))
        return self._err("No game process running")

    # ── Mods ──────────────────────────────────────────────────────────────────

    def search_content(self, query: str = "",
                       content_type: str = "shader",
                       offset: int = 0, limit: int = 20):
        """Search for shaders or resource packs via Modrinth."""
        try:
            from .mods import search_content as _sc
            from .game import get_minecraft_dir
            p = self._pm.active_profile
            if not p:
                return self._err("No profile")
            mc_dir = get_minecraft_dir(p)
            base_ver = _extract_mc_version(p.version, mc_dir)
            result  = {"mods": [], "done": False, "error": ""}
            evt     = threading.Event()

            def on_results(mods):
                result["mods"] = [{
                    "id":          mod.id,
                    "name":        mod.name,
                    "author":      mod.author,
                    "description": mod.description[:120],
                    "downloads":   mod.downloads,
                    "source":      mod.source,
                    "slug":        mod.slug,
                    "icon_url":    getattr(mod, "icon_url", "") or "",
                } for mod in mods]

            def on_done(ok, err):
                result["done"] = True
                if not ok and err:
                    result["error"] = err
                evt.set()

            _sc(query, base_ver, content_type,
                loader=p.mod_loader,
                on_results=on_results, on_done=on_done,
                offset=offset, limit=limit)
            evt.wait(timeout=25)
            if result["error"]:
                return self._ok(mods=[], error=result["error"],
                                page=offset // limit + 1, hasMore=False)
            return self._ok(mods=result["mods"],
                            page=offset // limit + 1,
                            hasMore=len(result["mods"]) >= limit)
        except Exception as e:
            return self._err(e)

    def get_profile_game_dir(self):
        """Return the active profile's game directory path."""
        try:
            from .game import get_profile_game_dir
            p = self._pm.active_profile
            if not p:
                return self._err("No active profile")
            path = get_profile_game_dir(p)
            return self._ok(path=path)
        except Exception as e:
            return self._err(e)

    def get_installed_mods(self):
        try:
            from .game import get_profile_game_dir
            from .mods import list_installed_mods
            p = self._pm.active_profile
            if not p:
                return self._ok(mods=[])
            mods_dir = os.path.join(get_profile_game_dir(p), "mods")
            files    = list_installed_mods(mods_dir)
            mods = []
            for f in files:
                path    = os.path.join(mods_dir, f)
                enabled = not f.endswith(".disabled")
                mods.append({
                    "filename": f,
                    "enabled":  enabled,
                    "size":     os.path.getsize(path) if os.path.isfile(path) else 0,
                })
            return self._ok(mods=mods)
        except Exception as e:
            return self._err(e)

    def get_installed_content(self, content_type: str = "shader"):
        """List installed shaders/resource packs for the active profile."""
        try:
            from .game import get_profile_game_dir
            p = self._pm.active_profile
            if not p:
                return self._ok(items=[])
            subdir = {"shader": "shaderpacks", "resourcepack": "resourcepacks"}.get(content_type)
            if not subdir:
                return self._err("Unsupported content type")
            folder = os.path.join(get_profile_game_dir(p), subdir)
            if not os.path.isdir(folder):
                return self._ok(items=[])
            items=[]
            for fn in sorted(os.listdir(folder), key=str.lower):
                if fn.startswith('.'):
                    continue
                path = os.path.join(folder, fn)
                is_dir = os.path.isdir(path)
                low = fn.lower()
                if not is_dir and not low.endswith((".zip", ".jar", ".disabled")):
                    continue
                enabled = not low.endswith(".disabled")
                display_name = fn[:-len(".disabled")] if not enabled else fn
                try:
                    size = 0 if is_dir else os.path.getsize(path)
                except OSError:
                    size = 0
                items.append({
                    "name": display_name,
                    "filename": fn,
                    "size": size,
                    "enabled": enabled,
                    "is_dir": is_dir,
                })
            return self._ok(items=items)
        except Exception as e:
            return self._err(e)

    def delete_content(self, filename: str, content_type: str = "shader"):
        """Delete an installed shader/resource pack safely."""
        try:
            from .game import get_profile_game_dir
            p=self._pm.active_profile
            if not p:
                return self._err("No profile")
            subdir={"shader":"shaderpacks", "resourcepack":"resourcepacks"}.get(content_type)
            if not subdir:
                return self._err("Unsupported content type")
            folder=os.path.join(get_profile_game_dir(p),subdir)
            path=_safe_path(os.path.basename(str(filename)),folder)
            if not path:
                return self._err("Invalid filename")
            if os.path.isdir(path):
                shutil.rmtree(path)
            elif os.path.isfile(path):
                os.remove(path)
            return self._ok()
        except Exception as e:
            return self._err(e)

    def toggle_mod(self, filename: str):
        try:
            from .game import get_profile_game_dir
            p = self._pm.active_profile
            if not p:
                return self._err("No profile")
            mods_dir = os.path.join(get_profile_game_dir(p), "mods")
            safe = os.path.basename(filename)
            if not safe:
                return self._err("Invalid filename")
            old_path = os.path.join(mods_dir, safe)
            if filename.endswith(".disabled"):
                new_path = old_path[:-len(".disabled")]
            else:
                new_path = old_path + ".disabled"
            os.rename(old_path, new_path)
            return self._ok(newFilename=os.path.basename(new_path))
        except Exception as e:
            return self._err(e)

    def delete_mod(self, filename: str):
        try:
            from .game import get_profile_game_dir
            p = self._pm.active_profile
            if not p:
                return self._err("No profile")
            mods_dir = os.path.join(get_profile_game_dir(p), "mods")
            path = _safe_path(filename, mods_dir)
            if not path:
                return self._err("Invalid filename")
            if os.path.isfile(path):
                os.remove(path)
            return self._ok()
        except Exception as e:
            return self._err(e)

    def search_mods(self, query: str = "",
                    offset: int = 0, limit: int = 20):
        try:
            from .mods import search_mods as _search
            from .game import get_profile_game_dir, get_minecraft_dir
            p = self._pm.active_profile
            if not p:
                return self._err("No profile")
            mc_dir = get_minecraft_dir(p)
            base_ver = _extract_mc_version(p.version, mc_dir)
            result  = {"mods": [], "done": False, "error": ""}
            evt     = threading.Event()

            def on_results(mods):
                result["mods"] = [{
                    "id":          mod.id,
                    "name":        mod.name,
                    "author":      mod.author,
                    "description": mod.description[:120],
                    "downloads":   mod.downloads,
                    "source":      mod.source,
                    "slug":        mod.slug,
                    "icon_url":    getattr(mod, "icon_url", "") or "",
                } for mod in mods]

            def on_done(ok, err):
                result["done"] = True
                if not ok and err:
                    result["error"] = err
                evt.set()

            _search(query, base_ver, p.mod_loader,
                    on_results=on_results,
                    on_done=on_done,
                    offset=offset, limit=limit)
            evt.wait(timeout=25)
            if result["error"]:
                return self._ok(mods=[], error=result["error"],
                                page=offset // limit + 1, hasMore=False)
            return self._ok(mods=result["mods"],
                            page=offset // limit + 1,
                            hasMore=len(result["mods"]) >= limit)
        except Exception as e:
            return self._err(e)

    def install_mod(self, mod_id: str, mod_name: str = "",
                    content_type: str = "mod"):
        try:
            from .mods import get_mod_versions, install_mod as _install
            from .game import get_profile_game_dir, get_minecraft_dir
            p = self._pm.active_profile
            if not p:
                return self._err("No profile")
            mc_dir = get_minecraft_dir(p)
            base_ver = _extract_mc_version(p.version, mc_dir)
            _subdir = {"mod": "mods", "shader": "shaderpacks",
                       "resourcepack": "resourcepacks"}.get(content_type, "mods")
            mods_dir = os.path.join(get_profile_game_dir(p), _subdir)

            mod_obj = type("M", (), {"id": mod_id, "source": "modrinth"})()
            versions_found = {"v": []}
            evt = threading.Event()

            def got_versions(vlist):
                versions_found["v"] = vlist
                evt.set()

            skip_loader = content_type in ("shader", "resourcepack")
            get_mod_versions(mod_obj, base_ver, p.mod_loader, on_done=got_versions,
                             skip_loader=skip_loader)
            evt.wait(timeout=10)
            versions = versions_found["v"]
            if not versions:
                return self._err("No compatible versions found")

            # Return version list to JS for user to pick
            return self._ok(versions=[{
                "filename": v.filename,
                "name":     v.name,
                "url":      v.download_url,
                "size":     v.size_bytes,
            } for v in versions[:10]])
        except Exception as e:
            return self._err(e)

    def download_mod_version(self, mod_id: str,
                              version_filename: str,
                              content_type: str = "mod"):
        try:
            from .mods import (get_mod_versions, install_mod as _install,
                              fetch_mod_dependencies, list_installed_mods)
            from .game import get_profile_game_dir, get_minecraft_dir
            p = self._pm.active_profile
            if not p:
                return self._err("No profile")
            mc_dir = get_minecraft_dir(p)
            base_ver = _extract_mc_version(p.version, mc_dir)
            _subdir = {"mod": "mods", "shader": "shaderpacks",
                       "resourcepack": "resourcepacks"}.get(content_type, "mods")
            mods_dir = os.path.join(get_profile_game_dir(p), _subdir)
            mod_obj  = type("M", (), {"id": mod_id, "source": "modrinth"})()
            versions_found = {"v": []}
            evt = threading.Event()

            def got_versions(vlist):
                versions_found["v"] = vlist
                evt.set()

            skip_loader = content_type in ("shader", "resourcepack")
            get_mod_versions(mod_obj, base_ver, p.mod_loader, on_done=got_versions,
                             skip_loader=skip_loader)
            evt.wait(timeout=10)
            version = next((v for v in versions_found["v"]
                            if v.filename == version_filename), None)
            if not version:
                return self._err("Version not found")

            # ── DEPENDENCY CHECK & AUTO-DOWNLOAD ──────────────────────────────
            if content_type == "mod":
                deps = fetch_mod_dependencies(mod_id, base_ver, p.mod_loader)
                required = [d for d in deps if d["required"]]
                optional = [d for d in deps if not d["required"]]
                
                if required or optional:
                    # Check which are already installed
                    installed_files = list_installed_mods(mods_dir)
                    def _is_installed(dep):
                        slug = dep["slug"].lower()
                        name = dep["name"].lower().replace(" ", "-")
                        return any(slug in f.lower() or name in f.lower()
                                   for f in installed_files)
                    
                    needed_required = [d for d in required if not _is_installed(d)]
                    needed_optional = [d for d in optional if not _is_installed(d)]
                    
                    # Auto-install required dependencies
                    for dep in needed_required:
                        self._push("dependency_installing", {"name": dep["name"]})
                        dep_mod_obj = type("_M", (), {"id": dep["project_id"], 
                                                       "source": "modrinth"})()
                        dep_versions_evt = threading.Event()
                        dep_versions_result = {"v": []}
                        
                        def _got_dep_versions(vlist, result=dep_versions_result):
                            result["v"] = vlist
                            dep_versions_evt.set()
                        
                        get_mod_versions(dep_mod_obj, base_ver, p.mod_loader,
                                        on_done=_got_dep_versions)
                        dep_versions_evt.wait(timeout=10)
                        
                        if dep_versions_result["v"]:
                            dep_version = dep_versions_result["v"][0]
                            dep_dl_evt = threading.Event()
                            dep_result = {"ok": False}
                            
                            def _dep_done(ok, _, evt=dep_dl_evt, res=dep_result):
                                res["ok"] = ok
                                evt.set()
                            
                            _install(dep_version, mods_dir, on_done=_dep_done)
                            dep_dl_evt.wait(timeout=60)
            # ──────────────────────────────────────────────────────────────────

            result = {"ok": False, "error": ""}
            dl_evt = threading.Event()

            def on_prog(dl, total):
                if total > 0:
                    self._push("mod_download_progress", {
                        "frac": dl/total, "filename": version_filename})

            def on_done(ok, path_or_err):
                result["ok"]    = ok
                result["error"] = "" if ok else path_or_err
                dl_evt.set()

            self._push("mod_download_progress", {"frac": 0, "filename": version_filename})
            _install(version, mods_dir, on_progress=on_prog, on_done=on_done)
            dl_evt.wait(timeout=60)
            if result["ok"]:
                if content_type == "mod":
                    # Refresh installed mods list so UI shows new mod immediately
                    from .mods import list_installed_mods
                    installed = list_installed_mods(mods_dir)
                    self._push("mods_list_updated", {"mods": installed})
                else:
                    self._push("content_list_updated",
                               {"content_type": content_type})
                return self._ok()
            return self._err(result["error"])
        except Exception as e:
            return self._err(e)

    # ── Servers ───────────────────────────────────────────────────────────────

    def get_servers(self):
        try:
            from .game import _get_config
            cfg = _get_config()
            return self._ok(servers=cfg.get("servers", []))
        except Exception as e:
            return self._err(e)

    def add_server(self, name: str, ip: str):
        try:
            cfg_path = os.path.join(os.path.expanduser("~"),
                                    ".FractalLauncher", "config.json")
            cfg = {}
            if os.path.isfile(cfg_path):
                with open(cfg_path) as f:
                    cfg = json.load(f)
            servers = cfg.get("servers", [])
            servers.append({"name": name, "ip": ip, "desc": "", "tag": "Custom"})
            cfg["servers"] = servers
            with open(cfg_path, "w") as f:
                json.dump(cfg, f, indent=2)
            return self._ok()
        except Exception as e:
            return self._err(e)

    def ping_server(self, ip: str):
        """Ping a Minecraft server and return latency."""
        try:
            import socket, time, struct
            host = ip
            port = 25565
            if ":" in ip:
                host, port = ip.rsplit(":", 1)
                port = int(port)
            start = time.time()
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(3)
            try:
                s.connect((host, port))
                def pack_varint(val):
                    buf = b""
                    while True:
                        b = val & 0x7F
                        val >>= 7
                        if val:
                            b |= 0x80
                        buf += bytes([b])
                        if not val:
                            break
                    return buf
                host_bytes = host.encode("utf-8")
                data = (pack_varint(0x00) +
                        pack_varint(47) +
                        pack_varint(len(host_bytes)) + host_bytes +
                        struct.pack(">H", port) +
                        pack_varint(1))
                s.sendall(pack_varint(len(data)) + data)
                s.sendall(b"\x01\x00")
                s.recv(4096)
                ms = int((time.time() - start) * 1000)
                return self._ok(ms=ms, online=True)
            finally:
                s.close()
        except Exception:
            return self._ok(ms=-1, online=False)

    # ── Settings ──────────────────────────────────────────────────────────────

    def get_settings(self):
        try:
            cfg_path = os.path.join(os.path.expanduser("~"), ".FractalLauncher", "config.json")
            exists = os.path.isfile(cfg_path)
            cfg = {}
            if exists:
                with open(cfg_path, encoding="utf-8") as f: cfg = json.load(f)
            profile = getattr(self._pm, "active_profile", None) if self._pm else None
            return self._ok(settings={
                "javaPath": cfg.get("javaPath") or cfg.get("java_path") or "",
                "authlibPath": cfg.get("authlibPath") or cfg.get("authlib_injector_path") or "",
                "defaultMcDir": cfg.get("defaultMcDir") or cfg.get("default_mc_dir") or "",
                "hideOnGame": cfg.get("hideOnGame", cfg.get("hide_launcher_on_game", True)),
                "theme": cfg.get("theme", "Lunar"),
                "language": cfg.get("language", "en"),
                "font": cfg.get("font", "Inter"),
                "fontType": cfg.get("fontType") or cfg.get("font_type") or "preset",
                "ramMb": getattr(profile, "ram_mb", 4096) if profile else 4096,
                "jvmArgs": getattr(profile, "jvm_args", "") if profile else "",
                "configExists": exists,
                "firstLaunch": bool(cfg.get("firstLaunch", cfg.get("first_launch", False))),
            })
        except Exception as e:
            return self._err(e)

    def save_settings(self, data: dict):
        try:
            cfg_path = os.path.join(os.path.expanduser("~"), ".FractalLauncher", "config.json")
            os.makedirs(os.path.dirname(cfg_path), exist_ok=True)
            cfg = {}
            if os.path.isfile(cfg_path):
                with open(cfg_path, encoding="utf-8") as f:
                    cfg = json.load(f)
            if not isinstance(cfg, dict):
                cfg = {}
            cfg.update(data)
            with open(cfg_path, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2)
            return self._ok()
        except Exception as e:
            return self._err(e)

    def get_first_launch(self):
        try:
            cfg_path = os.path.join(os.path.expanduser("~"), ".FractalLauncher", "config.json")
            if not os.path.isfile(cfg_path): return self._ok(firstLaunch=True, configExists=False)
            with open(cfg_path, encoding="utf-8") as f: cfg=json.load(f)
            if "firstLaunch" in cfg or "first_launch" in cfg:
                fl = bool(cfg.get("firstLaunch", cfg.get("first_launch", False)))
                return self._ok(firstLaunch=fl, configExists=True)
            # Config exists but has NO first-launch flag (written by an older
            # bootstrap before this logic existed): treat as first launch only
            # when the launcher has no real data yet (fresh/reset system).
            profiles_path = os.path.join(os.path.dirname(cfg_path), "profiles.json")
            has_accounts = False
            try:
                with open(profiles_path, encoding="utf-8") as pf:
                    has_accounts = bool(json.load(pf).get("accounts"))
            except Exception:
                pass
            return self._ok(firstLaunch=not has_accounts, configExists=True)
        except Exception as e: return self._err(e)

    def complete_first_launch(self):
        try:
            cfg_path = os.path.join(os.path.expanduser("~"), ".FractalLauncher", "config.json")
            cfg={}
            if os.path.isfile(cfg_path):
                with open(cfg_path, encoding="utf-8") as f: cfg=json.load(f)
            cfg["first_launch"]=False
            cfg["firstLaunch"]=False
            os.makedirs(os.path.dirname(cfg_path), exist_ok=True)
            with open(cfg_path,"w",encoding="utf-8") as f: json.dump(cfg,f,indent=2)
            return self._ok()
        except Exception as e: return self._err(e)

    def get_version_list(self):
        try:
            from .game import list_versions
            versions = list_versions("release")
            return self._ok(versions=[v["id"] for v in versions])
        except Exception as e:
            return self._err(e)

    # ── AI Custom Themes (Cerebras) ─────────────────────────────────────────────

    def get_custom_themes(self):
        """Returns all previously-generated AI custom themes: {name: palette}."""
        try:
            from . import ai_theme
            return self._ok(themes=ai_theme.load_web_themes())
        except Exception as e:
            return self._err(e)

    def get_cerebras_key_status(self):
        try:
            from . import ai_theme
            return self._ok(hasKey=ai_theme.has_api_key())
        except Exception as e:
            return self._err(e)

    def set_cerebras_key(self, key: str):
        try:
            from . import ai_theme
            if not key or not key.strip():
                return self._err("API key can't be empty.")
            ai_theme.save_api_key(key)
            return self._ok()
        except Exception as e:
            return self._err(e)

    def generate_custom_theme(self, prompt: str):
        """Sends the description to Cerebras, saves the result, and returns it to JS."""
        try:
            from . import ai_theme
            palette = ai_theme.generate_web_theme(prompt)
            name = ai_theme.save_web_theme(prompt, palette)
            return self._ok(name=name, palette=palette)
        except Exception as e:
            return self._err(e)

    def open_theme_instructions(self):
        """Opens the plain-text setup guide for Custom Themes in the OS default app."""
        try:
            import subprocess, sys
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            path = os.path.join(base_dir, "assets", "CUSTOM_THEMES_SETUP.txt")
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
            return self._ok()
        except Exception as e:
            return self._err(e)

    def save_theme_to_file(self, name: str, json_str: str):
        root = None
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            path = filedialog.asksaveasfilename(
                title="Export Theme",
                defaultextension=".json",
                initialfile=f"theme_{name}.json",
                filetypes=[("JSON files", "*.json")]
            )
            if path:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(json_str)
                return self._ok(path=path)
            return self._err("Export cancelled")
        except Exception as e:
            return self._err(e)
        finally:
            if root:
                try:
                    root.destroy()
                except Exception:
                    pass

    def import_custom_theme(self, name: str, palette: dict):
        try:
            from . import ai_theme
            ai_theme.save_web_theme(f"Imported: {name}", palette)
            return self._ok()
        except Exception as e:
            return self._err(e)

    def save_custom_theme(self, name: str, palette: dict):
        """Persist a user-edited custom theme under its exact name."""
        try:
            from . import ai_theme
            name = str(name or "").strip()
            if not name or not isinstance(palette, dict) or not palette:
                return self._err("Invalid theme.")
            ai_theme.save_web_theme_named(name, palette)
            return self._ok(name=name)
        except Exception as e:
            return self._err(e)

    def set_language(self, language: str):
        """Persist the UI language immediately (merges into config.json)."""
        try:
            lang = str(language or "").strip()
            if not lang:
                return self._err("Language can't be empty.")
            cfg_path = os.path.join(os.path.expanduser("~"), ".FractalLauncher", "config.json")
            os.makedirs(os.path.dirname(cfg_path), exist_ok=True)
            cfg = {}
            if os.path.isfile(cfg_path):
                with open(cfg_path, encoding="utf-8") as f:
                    cfg = json.load(f)
            if not isinstance(cfg, dict):
                cfg = {}
            cfg["language"] = lang
            with open(cfg_path, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2)
            return self._ok()
        except Exception as e:
            return self._err(e)

    def _hide_window_for_game(self) -> bool:
        """True when the 'hide launcher while the game runs' setting is enabled."""
        if not self._window:
            return False
        try:
            cfg_path = os.path.join(os.path.expanduser("~"), ".FractalLauncher", "config.json")
            if os.path.isfile(cfg_path):
                with open(cfg_path, encoding="utf-8") as f:
                    cfg = json.load(f)
            else:
                cfg = {}
            if not isinstance(cfg, dict):
                cfg = {}
            val = cfg.get("hideOnGame", cfg.get("hide_launcher_on_game", True))
            return bool(val)
        except Exception:
            return True

    # ── File dialogs ──────────────────────────────────────────────────────────

    def browse_file(self, title: str = "Select file",
                    filetypes: str = "All files (*.*)|*.*"):
        """Open a native file dialog and return the selected path."""
        root = None
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            path = filedialog.askopenfilename(title=title)
            return self._ok(path=path or "")
        except Exception as e:
            return self._err(e)
        finally:
            if root:
                try:
                    root.destroy()
                except Exception:
                    pass

    def browse_folder(self, title: str = "Select folder"):
        root = None
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            path = filedialog.askdirectory(title=title)
            return self._ok(path=path or "")
        except Exception as e:
            return self._err(e)
        finally:
            if root:
                try:
                    root.destroy()
                except Exception:
                    pass

    def open_folder(self, path: str):
        try:
            import subprocess, sys
            if sys.platform == "win32":
                os.startfile(path)
            else:
                subprocess.Popen(["xdg-open", path])
            return self._ok()
        except Exception as e:
            return self._err(e)

    # ── Diagnostics ───────────────────────────────────────────────────────────

    def run_diagnostics(self):
        """Comprehensive health check across system, Java, Minecraft,
        network, account and launcher. Each result carries a `category`
        and may carry a `fix` ({action, label}) for one-click repair."""
        try:
            import platform
            import shutil
            import socket
            import subprocess
            import sys
            from concurrent.futures import ThreadPoolExecutor
            from .game import _get_config, get_minecraft_dir, get_profile_game_dir

            results = []

            def add(cat, label, status, detail, fix=None, key=None, dkey=None):
                item = {"category": cat, "label": label,
                        "status": status, "detail": detail}
                if key:
                    item["key"] = key
                if dkey:
                    item["dkey"] = dkey
                if fix:
                    item["fix"] = fix
                results.append(item)

            cfg = _get_config()
            p = self._pm.active_profile

            # ── System ──────────────────────────────────────────────────────
            add("system", "OS", "info",
                f"{platform.platform()} ({platform.machine()})", key="os")

            cpu_name, gpu_name = _diag_hw_probe()
            cores = _HW_CACHE.get("cores", 0) or (os.cpu_count() or 0)
            logical = _HW_CACHE.get("logical", 0) or cores
            cpu_label = cpu_name.strip() or f"{cores} core(s)"
            add("system", "CPU", "info",
                f"{cpu_label} — {logical} logical processor(s)", key="cpu")

            if gpu_name.strip():
                drv = _HW_CACHE.get("driver", "")
                detail = gpu_name.strip()
                if drv:
                    detail += f" (driver {drv})"
                add("system", "GPU", "info", detail, key="gpu")
            else:
                add("system", "GPU", "info", "Not detected",
                    key="gpu", dkey="det_not_detected")

            ram_total, ram_avail = _diag_mem_status()
            if ram_total:
                used_pct = (1 - ram_avail / ram_total) * 100 if ram_avail else 0
                add("system", "System RAM", "info",
                    f"{ram_total / (1024**3):.1f} GB total, "
                    f"{ram_avail / (1024**3):.1f} GB available ({used_pct:.0f}% used)",
                    key="ram")
            else:
                add("system", "System RAM", "info", "Not detected",
                    key="ram", dkey="det_not_detected")

            mc_root = get_minecraft_dir(p) if p else os.path.expanduser("~")
            try:
                du = shutil.disk_usage(mc_root)
                free_gb = du.free / (1024 ** 3)
                total_gb = du.total / (1024 ** 3)
                drive = os.path.splitdrive(mc_root)[0] or mc_root
                if free_gb < 2:
                    st, fx = "error", {"action": "open_game_dir", "label": "Open folder"}
                elif free_gb < 5:
                    st, fx = "warn", None
                else:
                    st, fx = "ok", None
                add("system", f"Disk space ({drive})", st,
                    f"{free_gb:.1f} GB free of {total_gb:.1f} GB", fx, key="disk")
            except Exception as e:
                add("system", "Disk space", "warn", f"Could not read: {e}", key="disk")

            # ── Java ────────────────────────────────────────────────────────
            java = cfg.get("java_path", "")
            java_major = ""
            if java and os.path.isfile(java):
                java_major = _diag_java_version(java)
                if java_major:
                    bits = "64-bit" if int(java_major) >= 9 or "64" in java else "version detected"
                    add("java", "Java", "ok", f"Java {java_major} ({bits}) — {java}",
                        key="java")
                else:
                    add("java", "Java", "warn",
                        f"Found but could not read version — {java}", key="java")
            else:
                add("java", "Java", "warn",
                    "Not found — set in Settings", key="java",
                    dkey="not_found_settings")

            jh = os.environ.get("JAVA_HOME", "")
            if jh:
                add("java", "JAVA_HOME", "info", jh, key="java_home")
            else:
                add("java", "JAVA_HOME", "info", "Not set",
                    key="java_home", dkey="det_not_set")

            # ── Minecraft (active profile) ─────────────────────────────────
            if p:
                loader = (p.mod_loader or "vanilla")
                add("minecraft", "Active profile", "info",
                    f"{p.name} — Minecraft {p.version}, {loader}, {p.ram_mb} MB RAM",
                    key="active_profile")

                if java_major and p.ram_mb > 0 and ram_total:
                    if p.ram_mb * (1024 ** 2) > ram_total:
                        add("minecraft", "RAM allocation", "error",
                            f"Profile requests {p.ram_mb} MB but system only has "
                            f"{ram_total / (1024**3):.1f} GB total", key="ram_alloc")
                    elif p.ram_mb * (1024 ** 2) > ram_total * 0.75:
                        add("minecraft", "RAM allocation", "warn",
                            f"{p.ram_mb} MB is over 75% of system RAM — "
                            f"other apps may struggle", key="ram_alloc")
                    else:
                        add("minecraft", "RAM allocation", "ok",
                            f"{p.ram_mb} MB allocated", key="ram_alloc")

                jvm_args = (getattr(p, "jvm_args", "") or "")
                if "-Xmx" in jvm_args:
                    add("minecraft", "JVM arguments", "warn",
                        "Custom -Xmx in JVM args overrides profile RAM setting",
                        key="jvm_args", dkey="det_jvm_args")

                game_dir = get_profile_game_dir(p)
                try:
                    size_b, n_files, trunc = _diag_dir_stats(game_dir)
                    note = " (size capped)" if trunc else ""
                    add("minecraft", "Game directory", "ok",
                        f"{size_b / (1024**3):.2f} GB, {n_files} file(s){note} — {game_dir}",
                        {"action": "open_game_dir", "label": "Open", "key": "open"},
                        key="game_dir")
                except Exception as e:
                    add("minecraft", "Game directory", "warn", str(e),
                        {"action": "open_game_dir", "label": "Open", "key": "open"},
                        key="game_dir")

                # Version installed? — mod-loader aware (see _diagnose_game_version)
                gv_status, gv_detail = _diagnose_game_version(mc_root, p.version, loader)
                add("minecraft", "Game version", gv_status, gv_detail,
                    {"action": "open_versions", "label": "Versions", "key": "versions"}
                    if gv_status == "warn" else None, key="game_version")

                # Assets cache
                assets = os.path.join(mc_root, "assets")
                if os.path.isdir(assets):
                    a_b, a_n, _ = _diag_dir_stats(assets, max_files=50000)
                    add("minecraft", "Assets cache", "info",
                        f"{a_n} files, {a_b / (1024**3):.2f} GB", key="assets")
                else:
                    add("minecraft", "Assets cache", "warn",
                        "Missing — will download on launch",
                        key="assets", dkey="det_assets_missing")

                # Mods
                mods_dir = os.path.join(game_dir, "mods")
                mod_files = [f for f in os.listdir(mods_dir)
                             if f.endswith(".jar")] if os.path.isdir(mods_dir) else []
                m_b = 0
                for f in mod_files:
                    try:
                        m_b += os.path.getsize(os.path.join(mods_dir, f))
                    except OSError:
                        pass
                if loader == "vanilla" and mod_files:
                    add("minecraft", "Mods folder", "warn",
                        f"{len(mod_files)} jar(s) present but profile is Vanilla — "
                        f"they will not load",
                        {"action": "open_game_dir", "label": "Open", "key": "open"},
                        key="mods")
                elif mod_files:
                    add("minecraft", "Mods folder", "ok",
                        f"{len(mod_files)} mod(s), {m_b / (1024**2):.0f} MB",
                        {"action": "open_game_dir", "label": "Open", "key": "open"},
                        key="mods")
                else:
                    add("minecraft", "Mods folder", "info", "No mods installed",
                        {"action": "open_game_dir", "label": "Open", "key": "open"},
                        key="mods", dkey="det_mods_none")

                # Resource packs / shaderpacks / saves (info)
                for sub, label, skey in (("resourcepacks", "Resource packs", "resource_packs"),
                                         ("shaderpacks", "Shader packs", "shader_packs")):
                    d = os.path.join(game_dir, sub)
                    n = len([f for f in os.listdir(d)
                             if not f.startswith(".")]) if os.path.isdir(d) else 0
                    add("minecraft", label, "info", f"{n} installed", key=skey)

                saves = os.path.join(game_dir, "saves")
                worlds = [f for f in os.listdir(saves)
                          if os.path.isdir(os.path.join(saves, f))] if os.path.isdir(saves) else []
                add("minecraft", "Worlds", "info", f"{len(worlds)} save folder(s)",
                    key="worlds")

                # Crash reports
                crashes = os.path.join(mc_root, "crash-reports")
                crash_files = []
                if os.path.isdir(crashes):
                    crash_files = sorted(
                        [f for f in os.listdir(crashes) if f.startswith("crash-")],
                        key=lambda f: os.path.getmtime(os.path.join(crashes, f)),
                        reverse=True)
                if crash_files:
                    latest = crash_files[0]
                    age_days = (time.time() - os.path.getmtime(
                        os.path.join(crashes, latest))) / 86400
                    st = "warn" if age_days <= 7 else "info"
                    add("minecraft", "Crash reports", st,
                        f"{len(crash_files)} report(s), latest {age_days:.1f} day(s) ago: {latest}",
                        {"action": "open_crash_reports", "label": "Open", "key": "open"},
                        key="crash")
                else:
                    add("minecraft", "Crash reports", "ok", "None found",
                        {"action": "open_crash_reports", "label": "Open", "key": "open"},
                        key="crash", dkey="det_crash_none")

                # Latest log
                log = os.path.join(game_dir, "logs", "latest.log")
                if os.path.isfile(log):
                    lb = os.path.getsize(log)
                    st = "warn" if lb > 20 * 1024 * 1024 else "ok"
                    add("minecraft", "Latest log", st,
                        f"{lb / (1024**2):.1f} MB",
                        {"action": "open_logs", "label": "Open logs", "key": "open_logs"},
                        key="log")
                else:
                    add("minecraft", "Latest log", "info", "No log yet",
                        {"action": "open_logs", "label": "Open logs", "key": "open_logs"},
                        key="log", dkey="det_log_none")

                # Mesa3D conflict
                mesa = os.path.join(mc_root, "opengl32.dll")
                if os.path.isfile(mesa):
                    add("minecraft", "Mesa3D conflict", "error",
                        "opengl32.dll found — may cause 7 FPS! Delete it.",
                        {"action": "delete_mesa", "label": "Delete", "key": "delete"},
                        key="mesa", dkey="opengl_warning")
                else:
                    add("minecraft", "Mesa3D conflict", "ok", "Clean",
                        key="mesa", dkey="det_mesa_clean")

                # Authlib
                auth = cfg.get("authlib_injector_path", "")
                if auth and os.path.isfile(auth):
                    add("minecraft", "AuthLib-Injector", "ok", auth, key="authlib")
                else:
                    add("minecraft", "AuthLib-Injector", "warn",
                        "Not configured — skins won't work",
                        key="authlib", dkey="not_configured_skins")
            else:
                add("minecraft", "Profile", "warn", "No active profile",
                    key="profile", dkey="det_no_profile")

            # ── Network (parallel, 2 s each) ───────────────────────────────
            probes = [
                ("Internet connectivity", "1.1.1.1", 443, "net_internet"),
                ("Mojang session servers", "sessionserver.mojang.com", 443, "net_session"),
                ("Modrinth API", "api.modrinth.com", 443, "net_modrinth"),
                ("Mojang libraries CDN", "libraries.minecraft.net", 443, "net_libs"),
            ]
            with ThreadPoolExecutor(max_workers=4) as pool:
                futs = {pool.submit(_diag_tcp_ok, h, pt): (lbl, h, pk)
                        for lbl, h, pt, pk in probes}
                for fut, (lbl, host, pkey) in futs.items():
                    ok_net = fut.result()
                    if ok_net:
                        add("network", lbl, "ok", f"{host} reachable", key=pkey)
                    else:
                        add("network", lbl, "error",
                            f"{host} unreachable — check internet / firewall / DNS",
                            key=pkey)

            # ── Account ────────────────────────────────────────────────────
            try:
                a = self._pm.active_account
                if a:
                    at = getattr(a, "auth_type", "offline")
                    add("account", "Active account", "ok",
                        f"{a.username} ({at})", key="account")
                else:
                    add("account", "Active account", "warn",
                        "No account selected — launch will fail",
                        key="account", dkey="det_no_account")
            except Exception as e:
                add("account", "Active account", "warn", str(e), key="account")

            # ── Launcher ───────────────────────────────────────────────────
            cfg_path = os.path.join(os.path.expanduser("~"),
                                    ".FractalLauncher", "config.json")
            if os.path.isfile(cfg_path):
                try:
                    with open(cfg_path, encoding="utf-8") as f:
                        json.load(f)
                    add("launcher", "Config file", "ok", cfg_path, key="config")
                except Exception as e:
                    add("launcher", "Config file", "error",
                        f"Corrupt JSON — {e}", None, key="config")
            else:
                add("launcher", "Config file", "info",
                    "No config yet (defaults in use)", None,
                    key="config", dkey="det_config_none")

            data_dir = os.path.dirname(cfg_path)
            writable = os.access(data_dir, os.W_OK) if os.path.isdir(data_dir) else True
            add("launcher", "Data directory",
                "ok" if writable else "error",
                data_dir + ("" if writable else " — not writable!"), key="data_dir")

            backups_dir = os.path.join(data_dir, "backups")
            if os.path.isdir(backups_dir):
                bks = [f for f in os.listdir(backups_dir) if f.endswith(".zip")]
                if bks:
                    newest = max(bks, key=lambda f: os.path.getmtime(
                        os.path.join(backups_dir, f)))
                    age = (time.time() - os.path.getmtime(
                        os.path.join(backups_dir, newest))) / 86400
                    add("launcher", "Backups", "info",
                        f"{len(bks)} backup(s), newest {age:.1f} day(s) ago",
                        key="backups")
                else:
                    add("launcher", "Backups", "info", "No backups yet",
                        key="backups", dkey="det_backups_none")
            else:
                add("launcher", "Backups", "info", "No backups yet",
                    key="backups", dkey="det_backups_none")

            kind = "packaged build" if getattr(sys, "frozen", False) else "dev (source)"
            add("launcher", "Launcher build", "info", f"FractalLauncher — {kind}",
                key="build")

            # ── Summary ────────────────────────────────────────────────────
            summary = {"ok": 0, "warn": 0, "error": 0, "info": 0,
                       "total": len(results)}
            for it in results:
                summary[it["status"]] = summary.get(it["status"], 0) + 1
            return self._ok(results=results, summary=summary)
        except Exception as e:
            return self._err(e)

    def diag_fix(self, action: str):
        """One-click repair actions surfaced by diagnostics checks."""
        try:
            import sys
            import subprocess
            from .game import get_minecraft_dir, get_profile_game_dir

            p = self._pm.active_profile
            trusted = ("delete_mesa", "clear_natives", "open_crash_reports",
                       "open_game_dir", "open_logs", "open_versions")
            if action not in trusted:
                return self._err("Unknown fix action")

            if action == "delete_mesa":
                if not p:
                    return self._err("No active profile")
                mesa = os.path.join(get_minecraft_dir(p), "opengl32.dll")
                if not os.path.isfile(mesa):
                    return self._err("opengl32.dll not found")
                os.remove(mesa)
                return self._ok(msg="Deleted opengl32.dll")

            if action == "clear_natives":
                if not p:
                    return self._err("No active profile")
                removed = 0
                vid = p.version
                bases = [os.path.join(get_minecraft_dir(p), "versions", vid),
                         get_profile_game_dir(p)]
                for base in bases:
                    if not os.path.isdir(base):
                        continue
                    for entry in os.listdir(base):
                        if entry.startswith("natives"):
                            full = os.path.join(base, entry)
                            if os.path.isdir(full):
                                import shutil
                                shutil.rmtree(full, ignore_errors=True)
                                removed += 1
                return self._ok(msg=f"Removed {removed} natives folder(s)")

            # open_* actions
            if not p:
                return self._err("No active profile")
            mc = get_minecraft_dir(p)
            gd = get_profile_game_dir(p)
            dirs = {
                "open_crash_reports": os.path.join(mc, "crash-reports"),
                "open_game_dir": gd,
                "open_logs": os.path.join(gd, "logs"),
                "open_versions": os.path.join(mc, "versions"),
            }
            d = dirs[action]
            os.makedirs(d, exist_ok=True)
            if sys.platform == "win32":
                os.startfile(d)
            else:
                subprocess.Popen(["xdg-open", d])
            return self._ok()
        except Exception as e:
            return self._err(e)

    # ── External profile detection ───────────────────────────────────────────

    def _ext_cfg_path(self):
        return os.path.join(os.path.expanduser("~"),
                            ".FractalLauncher", "config.json")

    def _ext_load_cfg(self):
        path = self._ext_cfg_path()
        if os.path.isfile(path):
            try:
                with open(path, encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _ext_save_cfg(self, cfg):
        path = self._ext_cfg_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)

    def detect_external_profiles(self):
        """Scan the Minecraft directory for version installs (from ANY
        launcher) that are not yet tracked as a FractalLauncher profile.
        Also reads the official launcher's launcher_profiles.json for
        friendlier names and custom game directories."""
        try:
            from .game import DEFAULT_MINECRAFT_DIR
            cfg = self._ext_load_cfg()
            saved = str(cfg.get("defaultMcDir") or cfg.get("default_mc_dir") or "").strip()
            mc_root = saved if saved and os.path.isabs(saved) else DEFAULT_MINECRAFT_DIR
            dismissed = set(cfg.get("dismissed_ext") or [])
            # A candidate is "already have it" if any FL profile tracks the
            # same version id OR the same (base version, loader) pair — a
            # vanilla profile must not cover a loader install or vice versa
            existing_versions, existing_pairs = _profile_coverage(
                mc_root, self._pm.profiles if self._pm else [])
            inherited = _inherited_base_ids(mc_root)

            vdir = os.path.join(mc_root, "versions")
            found = {}

            if os.path.isdir(vdir):
                for vid in sorted(os.listdir(vdir)):
                    vpath = os.path.join(vdir, vid)
                    vjson = os.path.join(vpath, vid + ".json")
                    if not os.path.isdir(vpath) or not os.path.isfile(vjson):
                        continue
                    if vid in existing_versions:
                        continue
                    loader = _detect_loader(vid, vjson)
                    if loader == "vanilla" and vid in inherited:
                        # internal base pulled down as a dependency by a
                        # loader install (e.g. fabric's '26.3' parent) —
                        # not a standalone vanilla install
                        continue
                    if (_version_base(mc_root, vid), loader) in existing_pairs:
                        continue
                    key = f"{vid}|{loader}"
                    if key in dismissed:
                        continue
                    display = (vid if loader == "vanilla"
                               else f"{loader.title()} {_version_base(mc_root, vid)}")
                    found[key] = {
                        "key": key, "name": display, "version": vid,
                        "loader": loader, "gameDir": "", "source": "version",
                    }

            # Official Minecraft launcher profiles — richer names + gameDir
            lp = os.path.join(mc_root, "launcher_profiles.json")
            if os.path.isfile(lp):
                try:
                    with open(lp, encoding="utf-8") as f:
                        data = json.load(f)
                    for prof in (data.get("profiles") or {}).values():
                        if not isinstance(prof, dict):
                            continue
                        name = str(prof.get("name") or "").strip()
                        ver = str(prof.get("lastVersionId") or "").strip()
                        if not name or not ver:
                            continue
                        if not os.path.isdir(os.path.join(vdir, ver)):
                            continue
                        vjson = os.path.join(vdir, ver, ver + ".json")
                        loader = _detect_loader(ver, vjson if os.path.isfile(vjson) else "")
                        if ver in existing_versions:
                            continue
                        # (inherited bases stay offerable here: an official
                        # profile pointing at one is a genuine user profile)
                        if (_version_base(mc_root, ver), loader) in existing_pairs:
                            continue
                        key = f"{ver}|{loader}"
                        if key in dismissed:
                            continue
                        gdir = str(prof.get("gameDir") or "")
                        if gdir and not os.path.isabs(gdir):
                            gdir = ""
                        if key in found:
                            found[key]["name"] = name
                            if gdir:
                                found[key]["gameDir"] = gdir
                            found[key]["source"] = "official"
                        else:
                            found[key] = {
                                "key": key, "name": name, "version": ver,
                                "loader": loader, "gameDir": gdir,
                                "source": "official",
                            }
                except Exception:
                    pass

            return self._ok(profiles=list(found.values()), mcRoot=mc_root)
        except Exception as e:
            return self._err(e)

    def import_profiles(self, items):
        """Add previously detected external profiles as FractalLauncher profiles."""
        try:
            from .game import DEFAULT_MINECRAFT_DIR
            if not isinstance(items, list):
                return self._err("Invalid payload")
            cfg = self._ext_load_cfg()
            saved = str(cfg.get("defaultMcDir") or cfg.get("default_mc_dir") or "").strip()
            mc_root = saved if saved and os.path.isabs(saved) else DEFAULT_MINECRAFT_DIR
            vdir = os.path.join(mc_root, "versions")
            allowed = {"vanilla", "fabric", "forge", "quilt", "neoforge"}
            existing, existing_pairs = _profile_coverage(
                mc_root, self._pm.profiles if self._pm else [])
            inherited = _inherited_base_ids(mc_root)
            added = 0
            for it in items:
                if not isinstance(it, dict):
                    continue
                name = str(it.get("name") or "").strip()
                version = str(it.get("version") or "").strip()
                loader = str(it.get("loader") or "vanilla").strip().lower()
                gdir = str(it.get("gameDir") or "")
                if not name or not version or version in existing:
                    continue
                if loader not in allowed:
                    loader = "vanilla"
                base = _version_base(mc_root, version)
                if (base, loader) in existing_pairs:
                    continue
                if (loader == "vanilla" and version in inherited
                        and str(it.get("source") or "") == "version"):
                    # dependency parent of a loader install, not a real
                    # vanilla install (detect already filters these)
                    continue
                if not os.path.isdir(os.path.join(vdir, version)):
                    continue
                if gdir and not (os.path.isabs(gdir) and os.path.isdir(gdir)):
                    gdir = ""
                kwargs = dict(name=name, version=version,
                              mod_loader=loader, game_dir=gdir)
                if not gdir:
                    # Reattach to an orphaned FL profile folder (left behind
                    # when profiles.json was reset) instead of inventing a
                    # fresh empty one — the user's mods/saves/RP/shaders
                    # live in FractalLauncher_profiles/<old profile id>.
                    pid = _adopt_profile_dir_id(mc_root,
                                                self._pm.profiles, loader)
                    if pid:
                        kwargs["profile_id"] = pid
                self._pm.add_profile(**kwargs)
                existing.add(version)
                existing_pairs.add((base, loader))
                added += 1
            return self._ok(added=added)
        except Exception as e:
            return self._err(e)

    def dismiss_external_profiles(self, keys):
        """Remember dismissed candidates so they are not re-offered each launch."""
        try:
            if not isinstance(keys, list):
                return self._err("Invalid payload")
            cfg = self._ext_load_cfg()
            seen = list(cfg.get("dismissed_ext") or [])
            for k in keys:
                k = str(k)
                if k and k not in seen:
                    seen.append(k)
            cfg["dismissed_ext"] = seen[-500:]
            self._ext_save_cfg(cfg)
            return self._ok()
        except Exception as e:
            return self._err(e)

    # ── Screenshots & Backups ─────────────────────────────────────────────────

    def get_screenshots(self):
        try:
            from .game import get_profile_game_dir
            p = self._pm.active_profile
            if not p:
                return self._ok(screenshots=[])
            ss_dir = os.path.join(get_profile_game_dir(p), "screenshots")
            if not os.path.isdir(ss_dir):
                return self._ok(screenshots=[])
            files = sorted([f for f in os.listdir(ss_dir)
                            if f.lower().endswith((".png", ".jpg", ".jpeg"))],
                           reverse=True)
            shots = []
            for f in files[:50]:
                path = os.path.join(ss_dir, f)
                try:
                    st = os.stat(path)
                    shots.append({
                        "filename": f,
                        "path": path,
                        "size": st.st_size,
                        "mtime": st.st_mtime,
                        "mtime_ns": st.st_mtime_ns,
                    })
                except OSError:
                    continue
            return self._ok(screenshots=shots)
        except Exception as e:
            return self._err(e)

    def save_edited_screenshot(self, path: str, base64_data: str):
        try:
            import base64
            from .game import get_profile_game_dir
            p = self._pm.active_profile
            if not p:
                return self._err("No profile")
            ss_dir = os.path.join(get_profile_game_dir(p), "screenshots")
            safe = _safe_path(path, ss_dir)
            if not safe:
                safe = _safe_path(path, ss_dir)
            if not safe:
                return self._err("Invalid path")
            data = base64.b64decode(base64_data, validate=True)
            if not data:
                return self._err("Empty image data")
            with open(safe, "wb") as f:
                f.write(data)
            return self._ok()
        except Exception as e:
            return self._err(e)

    def backup_now(self):
        try:
            import zipfile, datetime
            from .game import get_profile_game_dir
            p = self._pm.active_profile
            if not p:
                return self._err("No active profile")
            saves_dir  = os.path.join(get_profile_game_dir(p), "saves")
            backup_dir = os.path.join(os.path.expanduser("~"),
                                      ".FractalLauncher", "backups")
            os.makedirs(backup_dir, exist_ok=True)
            if not os.path.isdir(saves_dir):
                return self._err("No saves folder found")
            # Collect all files first
            all_files = []
            for root, dirs, files in os.walk(saves_dir):
                for f in files:
                    fp = os.path.join(root, f)
                    all_files.append((fp, os.path.relpath(fp, saves_dir)))
            if not all_files:
                return self._err("No world saves found to backup")
            ts   = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            name = f"{p.name}_{ts}.zip".replace(" ", "_")
            out  = os.path.join(backup_dir, name)
            with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
                for fp, arcname in all_files:
                    zf.write(fp, arcname)
            return self._ok(path=out, filename=name)
        except Exception as e:
            return self._err(e)

    def get_backups(self):
        try:
            backup_dir = os.path.join(os.path.expanduser("~"),
                                      ".FractalLauncher", "backups")
            if not os.path.isdir(backup_dir):
                return self._ok(backups=[])
            files = sorted([f for f in os.listdir(backup_dir)
                            if f.endswith(".zip")], reverse=True)
            return self._ok(backups=[{
                "filename": f,
                "path":     os.path.join(backup_dir, f),
                "size":     os.path.getsize(os.path.join(backup_dir, f)),
            } for f in files])
        except Exception as e:
            return self._err(e)

    def delete_backup(self, filename: str):
        try:
            backup_dir = os.path.join(os.path.expanduser("~"),
                                      ".FractalLauncher", "backups")
            path = _safe_path(filename, backup_dir)
            if not path:
                return self._err("Invalid filename")
            if os.path.isfile(path):
                os.remove(path)
            return self._ok()
        except Exception as e:
            return self._err(e)

    # ── Capes ─────────────────────────────────────────────────────────────────

    def get_cape_presets(self):
        try:
            import sys as _sys
            if getattr(_sys, "frozen", False):
                base = os.path.dirname(_sys.executable)
            else:
                base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            capes_dir = os.path.join(base, "assets", "capes")
            if not os.path.isdir(capes_dir):
                return self._ok(capes=[])
            capes = []
            for f in os.listdir(capes_dir):
                if f.lower().endswith(".png"):
                    capes.append({
                        "filename": f,
                        "name":     os.path.splitext(f)[0].replace("_", " ").title(),
                        "path":     os.path.join(capes_dir, f),
                    })
            return self._ok(capes=capes)
        except Exception as e:
            return self._err(e)

    # ── Fonts ─────────────────────────────────────────────────────────────────

    def get_font_presets(self):
        return self._ok(fonts=[
            "Inter", "Roboto", "Open Sans", "Lato", "Montserrat", 
            "Poppins", "Ubuntu", "Segoe UI", "Arial", "Verdana"
        ])

    def get_uploaded_fonts(self):
        try:
            font_dir = os.path.join(os.path.expanduser("~"), ".FractalLauncher", "fonts")
            if not os.path.isdir(font_dir):
                return self._ok(fonts=[])
            fonts = []
            for f in os.listdir(font_dir):
                if f.lower().endswith((".ttf", ".otf", ".woff", ".woff2")):
                    fonts.append({
                        "name": os.path.splitext(f)[0],
                        "filename": f,
                        "path": os.path.join(font_dir, f)
                    })
            return self._ok(fonts=fonts)
        except Exception as e:
            return self._err(e)

    def upload_font(self):
        try:
            import shutil
            res = self.browse_file("Select Font File", "Font files (*.ttf;*.otf;*.woff;*.woff2)|*.ttf;*.otf;*.woff;*.woff2")
            if not res["ok"] or not res["path"]:
                return res
            
            src = res["path"]
            font_dir = os.path.join(os.path.expanduser("~"), ".FractalLauncher", "fonts")
            os.makedirs(font_dir, exist_ok=True)
            
            filename = os.path.basename(src)
            dest = os.path.join(font_dir, filename)
            shutil.copy2(src, dest)
            
            return self._ok(name=os.path.splitext(filename)[0], filename=filename, path=dest)
        except Exception as e:
            return self._err(e)

    def delete_font(self, filename: str):
        try:
            font_dir = os.path.join(os.path.expanduser("~"), ".FractalLauncher", "fonts")
            path = _safe_path(filename, font_dir)
            if not path:
                return self._err("Invalid filename")
            if os.path.isfile(path):
                os.remove(path)
            return self._ok()
        except Exception as e:
            return self._err(e)
