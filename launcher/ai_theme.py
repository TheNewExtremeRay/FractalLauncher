"""
FractalLauncher — AI Custom Theme Generator

Lets the user type a plain-English description of a theme ("cyberpunk city
at night", "cozy autumn cabin", etc.) and turns it into a full FractalLauncher
color palette using Cerebras' chat-completions API.

The API key is kept in its own small text file (NOT inside config.json) so it
is easy to find and edit by hand if the user prefers:

    ~/.FractalLauncher/cerebras_api_key.txt

Generated themes are cached to disk so they persist across restarts:

    ~/.FractalLauncher/custom_themes.json
"""

import os
import re
import json
import requests

from .theme import THEMES, DEFAULT_THEME

# ── Paths ─────────────────────────────────────────────────────────────────────
CONFIG_DIR        = os.path.join(os.path.expanduser("~"), ".FractalLauncher")
API_KEY_FILE       = os.path.join(CONFIG_DIR, "cerebras_api_key.txt")
CUSTOM_THEMES_FILE = os.path.join(CONFIG_DIR, "custom_themes.json")
WEB_CUSTOM_THEMES_FILE = os.path.join(CONFIG_DIR, "custom_themes_web.json")

# ── Cerebras API ────────────────────────────────────────────────────────────────
CEREBRAS_API_URL    = "https://api.cerebras.ai/v1/chat/completions"
CEREBRAS_MODELS_URL = "https://api.cerebras.ai/v1/models"

# Cerebras' free-tier model catalog changes fairly often, so instead of hardcoding
# one model name (which can 404 out from under us), we ask the API what's actually
# available and pick the first one we recognize from this priority list, favoring
# small/fast free-tier-friendly models. If none of these match, we just use
# whatever the API says is available.
PREFERRED_MODELS = [
    "llama3.1-8b",
    "llama-3.3-70b",
    "qwen-3-32b",
    "gpt-oss-120b",
    "llama3.1-70b",
    "zai-glm-4.6",
    "zai-glm-4.7",
]

_model_cache = {"id": None}   # cached per-process so we don't hit /v1/models every call

# Every key an FractalLauncher theme needs (see launcher/theme.py THEMES dict)
REQUIRED_KEYS = [
    "BG_DARK", "BG_PANEL", "BG_CARD", "BG_INPUT", "BG_HOVER",
    "ACCENT", "ACCENT_HOVER", "ACCENT_DARK",
    "SUCCESS", "SUCCESS_HOVER", "DANGER", "WARN",
    "TEXT_PRIMARY", "TEXT_SECONDARY", "TEXT_MUTED",
    "BORDER", "BORDER_ACTIVE", "SCROLLBAR",
]

SYSTEM_PROMPT = """You are a UI color-theme generator for a dark-mode Minecraft \
launcher app called FractalLauncher (built with CustomTkinter).

Given a short description from the user, invent a complete color palette that \
matches the vibe they described. Reply with ONLY raw JSON — no markdown code \
fences, no explanation, no extra text before or after.

The JSON object must have exactly these keys, each mapped to a 6-digit hex \
color string starting with '#':

  BG_DARK, BG_PANEL, BG_CARD, BG_INPUT, BG_HOVER,
  ACCENT, ACCENT_HOVER, ACCENT_DARK,
  SUCCESS, SUCCESS_HOVER, DANGER, WARN,
  TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
  BORDER, BORDER_ACTIVE, SCROLLBAR

Guidelines:
- BG_DARK/BG_PANEL/BG_CARD/BG_INPUT/BG_HOVER should get progressively lighter \
and form a cohesive dark (or otherwise readable) background stack fitting the theme.
- ACCENT is the main highlight/button color; ACCENT_HOVER a lighter version; \
ACCENT_DARK a darker version.
- SUCCESS/SUCCESS_HOVER should read as "green/positive" even if tinted to match \
the theme; DANGER should read as "red/negative"; WARN should read as "amber/caution".
- TEXT_PRIMARY must have strong contrast against BG_DARK/BG_PANEL/BG_CARD \
(comfortably readable). TEXT_SECONDARY and TEXT_MUTED are progressively dimmer.
- BORDER/BORDER_ACTIVE/SCROLLBAR should be subtle, close in tone to the backgrounds.

Return ONLY the JSON object."""

HEX_RE = re.compile(r"^#(?:[0-9a-fA-F]{6})$")


# ── API key storage ───────────────────────────────────────────────────────────
def get_api_key() -> str:
    """Reads the Cerebras API key from its own dedicated text file."""
    try:
        with open(API_KEY_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""
    except Exception:
        return ""


def save_api_key(key: str) -> None:
    """Writes the Cerebras API key to its own dedicated text file."""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(API_KEY_FILE, "w", encoding="utf-8") as f:
        f.write(key.strip() + "\n")


def has_api_key() -> bool:
    return bool(get_api_key())


# ── Custom theme persistence ────────────────────────────────────────────────────
def load_custom_themes() -> dict:
    """Returns {theme_name: palette_dict} for all saved AI-generated themes."""
    try:
        with open(CUSTOM_THEMES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    except Exception:
        return {}


def _save_custom_themes(themes: dict) -> None:
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CUSTOM_THEMES_FILE, "w", encoding="utf-8") as f:
        json.dump(themes, f, indent=2)


def register_custom_themes() -> list:
    """
    Loads every saved custom theme from disk into the in-memory THEMES dict
    (from launcher/theme.py) so they show up alongside the built-in presets.
    Returns the list of custom theme names that were registered.
    """
    from . import theme as _theme_mod
    saved = load_custom_themes()
    names = []
    for name, palette in saved.items():
        if _valid_palette(palette):
            _theme_mod.THEMES[name] = palette
            if name not in _theme_mod.THEME_NAMES:
                _theme_mod.THEME_NAMES.append(name)
            names.append(name)
    return names


def _valid_palette(palette: dict) -> bool:
    if not isinstance(palette, dict):
        return False
    return all(k in palette and isinstance(palette[k], str) and HEX_RE.match(palette[k])
               for k in REQUIRED_KEYS)


# ── Generation ───────────────────────────────────────────────────────────────
class ThemeGenerationError(Exception):
    pass


def _extract_json(text: str) -> dict:
    """Pulls a JSON object out of a model response, tolerating stray markdown fences."""
    text = text.strip()
    # Strip ```json ... ``` or ``` ... ``` fences if present
    fence = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()
    # Fall back to grabbing the outermost { ... } block
    if not text.startswith("{"):
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            text = text[start:end + 1]
    return json.loads(text)


def _resolve_model(key: str, exclude: set = None, timeout: int = 15) -> str:
    """
    Asks the Cerebras API which models this key can actually use, and picks the
    best match from PREFERRED_MODELS (skipping anything in `exclude`). Falls back
    to the first available model the API returns if none of our preferences match.
    Result is cached for the life of the process (unless excluded).
    """
    exclude = exclude or set()

    if _model_cache["id"] and _model_cache["id"] not in exclude:
        return _model_cache["id"]

    headers = {
        "Authorization": f"Bearer {key}",
        "Accept": "application/json",
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"),
    }
    try:
        resp = requests.get(CEREBRAS_MODELS_URL, headers=headers, timeout=timeout)
        resp.raise_for_status()
        available = [m.get("id") for m in resp.json().get("data", []) if m.get("id")]
    except Exception:
        available = []

    available = [m for m in available if m not in exclude]

    if not available:
        # Couldn't list models (network hiccup, catalog empty, etc.) — best guess
        # from our priority list and let the actual chat-completion call surface
        # any real error.
        for preferred in PREFERRED_MODELS:
            if preferred not in exclude:
                return preferred
        return PREFERRED_MODELS[0]

    for preferred in PREFERRED_MODELS:
        if preferred in available:
            _model_cache["id"] = preferred
            return preferred

    # None of our preferences matched — just use whatever's first on the list.
    _model_cache["id"] = available[0]
    return available[0]


def _call_cerebras(system_prompt: str, user_prompt: str, api_key: str = None, timeout: int = 30) -> str:
    """Makes the raw Cerebras chat-completions call and returns the message content string."""
    key = (api_key or get_api_key()).strip()
    if not key:
        raise ThemeGenerationError(
            "No Cerebras API key set. Click 'Set API Key' or add it to:\n" + API_KEY_FILE
        )

    tried = set()
    model = _resolve_model(key, exclude=tried)

    payload_base = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.8,
        "max_tokens": 700,
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {key}",
        # Cloudflare (which fronts api.cerebras.ai) blocks requests that look like
        # bare scripts (e.g. Python's default urllib User-Agent) with a 403 /
        # "error code: 1010" browser-signature block. A normal browser-style
        # User-Agent avoids that false positive.
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"),
    }

    attempts_left = 2   # one retry if the chosen model turns out to be unavailable
    while True:
        payload = {"model": model, **payload_base}
        try:
            resp = requests.post(CEREBRAS_API_URL, headers=headers, json=payload, timeout=timeout)
        except requests.exceptions.Timeout:
            raise ThemeGenerationError("Cerebras API request timed out. Try again.")
        except requests.exceptions.RequestException as e:
            raise ThemeGenerationError(f"Couldn't reach Cerebras API: {e}")

        if resp.status_code == 401:
            raise ThemeGenerationError("Cerebras rejected the API key (401 Unauthorized). "
                                        "Double-check the key you saved.")
        if resp.status_code == 403:
            raise ThemeGenerationError(
                "Cerebras API blocked the request (403). This is usually Cloudflare's bot "
                "protection (error code 1010) rather than a bad API key. Wait a moment and "
                "try again; if it keeps happening, double-check your key at cloud.cerebras.ai."
            )
        if resp.status_code == 404:
            tried.add(model)
            _model_cache["id"] = None
            attempts_left -= 1
            if attempts_left > 0:
                model = _resolve_model(key, exclude=tried)   # try the next-best available model
                continue
            raise ThemeGenerationError(
                f"Cerebras doesn't have a usable free-tier model available right now "
                f"(last tried: '{model}'). Try again in a moment."
            )
        if not resp.ok:
            raise ThemeGenerationError(f"Cerebras API error {resp.status_code}: {resp.text[:200]}")

        break

    try:
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except Exception:
        raise ThemeGenerationError("Unexpected response from Cerebras API.")


# ══════════════════════════════════════════════════════════════════════════════
#  WEBVIEW (ui.html) THEME SCHEMA
# ══════════════════════════════════════════════════════════════════════════════
# ui.html's THEMES{} / previewTheme() only use this reduced key set — these map
# straight onto the app's CSS custom properties (--bg, --panel, --accent, etc).

WEB_REQUIRED_KEYS = ["bg", "panel", "card", "accent", "tp", "ts", "tm", "border", "ok", "warn", "err"]

WEB_DEFAULT_THEME = {
    "bg": "#0d0f13", "panel": "#13161c", "card": "#181c24", "accent": "#5865f2",
    "tp": "#e8eaf6", "ts": "#8b92a5", "tm": "#555e78", "border": "#252a38",
    "ok": "#3ba55d", "warn": "#faa61a", "err": "#ed4245",
}

WEB_SYSTEM_PROMPT = """You are a UI color-theme generator for a dark-mode Minecraft \
launcher app called FractalLauncher (an HTML/CSS/JS interface running in pywebview).

Given a short description from the user, invent a complete color palette that \
matches the vibe they described. Reply with ONLY raw JSON — no markdown code \
fences, no explanation, no extra text before or after.

The JSON object must have exactly these keys, each mapped to a 6-digit hex \
color string starting with '#':

  bg      - main app background
  panel   - sidebar / panel background, slightly lighter or darker than bg
  card    - card/box background, sits on top of panel
  accent  - the main highlight/button/link color
  tp      - primary text color, must contrast strongly against bg/panel/card
  ts      - secondary text color, dimmer than tp
  tm      - muted text color, dimmer than ts
  border  - subtle border color, close in tone to the backgrounds
  ok      - a "success/positive" color, reads as green even if tinted to match the theme
  warn    - a "warning/caution" color, reads as amber/yellow even if tinted to match the theme
  err     - an "error/danger" color, reads as red even if tinted to match the theme

Keep bg/panel/card visually cohesive (a believable dark, or otherwise readable, \
background stack) and make sure tp stays easily readable on top of them.

Return ONLY the JSON object."""


def load_web_themes() -> dict:
    """Returns {theme_name: palette_dict} for saved AI-generated webview themes."""
    try:
        with open(WEB_CUSTOM_THEMES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    except Exception:
        return {}


def _save_web_themes(themes: dict) -> None:
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(WEB_CUSTOM_THEMES_FILE, "w", encoding="utf-8") as f:
        json.dump(themes, f, indent=2)


def generate_web_theme(prompt: str, api_key: str = None, timeout: int = 30) -> dict:
    """
    Calls the Cerebras API to turn a text prompt into a webview (ui.html) color
    palette. Returns the palette dict on success, raises ThemeGenerationError
    with a human-readable message on failure.
    """
    prompt = (prompt or "").strip()
    if not prompt:
        raise ThemeGenerationError("Please describe the theme you want first.")

    content = _call_cerebras(WEB_SYSTEM_PROMPT, f"Theme description: {prompt}", api_key, timeout)

    try:
        palette = _extract_json(content)
    except Exception:
        raise ThemeGenerationError("The AI didn't return valid JSON. Try rephrasing your prompt.")

    cleaned = {}
    for k in WEB_REQUIRED_KEYS:
        v = palette.get(k)
        cleaned[k] = v if isinstance(v, str) and HEX_RE.match(v) else WEB_DEFAULT_THEME[k]

    return cleaned


def save_web_theme(prompt: str, palette: dict) -> str:
    """Saves a generated webview palette to disk under a name derived from the prompt."""
    short = " ".join(prompt.strip().split())[:40]
    base_name = f"AI: {short}" if short else "AI: Custom Theme"

    saved = load_web_themes()
    name = base_name
    i = 2
    while name in saved and saved.get(name) != palette:
        name = f"{base_name} ({i})"
        i += 1

    saved[name] = palette
    _save_web_themes(saved)
    return name


def save_web_theme_named(name: str, palette: dict) -> str:
    """Saves a palette under an exact user-provided name (overwrites same name)."""
    name = " ".join(str(name or "").strip().split())[:40] or "Custom Theme"
    saved = load_web_themes()
    saved[name] = palette
    _save_web_themes(saved)
    return name



def generate_theme(prompt: str, api_key: str = None, timeout: int = 30) -> dict:
    """
    Calls the Cerebras API to turn a text prompt into a full FractalLauncher
    color palette (CustomTkinter schema). Returns the palette dict on success.
    Raises ThemeGenerationError with a human-readable message on any failure.
    """
    prompt = (prompt or "").strip()
    if not prompt:
        raise ThemeGenerationError("Please describe the theme you want first.")

    content = _call_cerebras(SYSTEM_PROMPT, f"Theme description: {prompt}", api_key, timeout)

    try:
        palette = _extract_json(content)
    except Exception:
        raise ThemeGenerationError("The AI didn't return valid JSON. Try rephrasing your prompt.")

    # Fill in any missing/invalid keys from the default theme so we always
    # end up with a usable, complete palette.
    fallback = THEMES[DEFAULT_THEME]
    cleaned = {}
    for k in REQUIRED_KEYS:
        v = palette.get(k)
        cleaned[k] = v if isinstance(v, str) and HEX_RE.match(v) else fallback[k]

    return cleaned


def save_generated_theme(prompt: str, palette: dict) -> str:
    """
    Saves a generated palette under a name derived from the prompt and
    registers it into the live THEMES dict. Returns the final theme name.
    """
    from . import theme as _theme_mod

    short = " ".join(prompt.strip().split())[:40]
    base_name = f"AI: {short}" if short else "AI: Custom Theme"
    name = base_name
    saved = load_custom_themes()
    i = 2
    while name in THEMES and THEMES.get(name) != palette:
        name = f"{base_name} ({i})"
        i += 1

    saved[name] = palette
    _save_custom_themes(saved)

    _theme_mod.THEMES[name] = palette
    if name not in _theme_mod.THEME_NAMES:
        _theme_mod.THEME_NAMES.append(name)

    return name
