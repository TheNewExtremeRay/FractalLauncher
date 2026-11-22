"""
FractalLauncher UI Theme - Modern Gaming Experience

Theme Philosophy:
- Glassmorphism throughout
- Dynamic gradients
- Glow effects and depth
- Gaming-inspired aesthetics
- Smooth cubic-bezier animations
"""

# ══════════════════════════════════════════════════════════════════════════════
# NEW COLOR PALETTE - Modern Gaming Design System
# ══════════════════════════════════════════════════════════════════════════════

# Base Colors
BG_DARK            = "#050508"           # Deepest black-purple
BG_PANEL          = "#0f0f1a"           # Glassmorphism base
BG_CARD           = "#161626"           # Card background
BG_INPUT          = "#1f1f35"           # Input field
BG_HOVER          = "#2a2a45"           # Hover state
BG_GLOSS          = "rgba(255, 255, 255, 0.05)"   # Glass effect

# Accent Colors (Primary Gradient)
ACCENT            = "#8b5cf6"           # Violet
ACCENT_HOVER       = "#a78bfa"           # Light violet
ACCENT_DARK        = "#7c3aed"           # Dark violet
ACCENT_GLOW        = "rgba(139, 92, 246, 0.5)"  # Glow effect

# Gradient Accents
ACCENT_GRADIENT_1  = "linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)"   # Indigo-violet
ACCENT_GRADIENT_2  = "linear-gradient(135deg, #8b5cf6 0%, #d946ef 100%)"  # Violet-pink
ACCENT_GRADIENT_3  = "linear-gradient(135deg, #06b6d4 0%, #8b5cf6 100%)"  # Cyan-violet
ACCENT_GRADIENT_4  = "linear-gradient(135deg, #f97316 0%, #8b5cf6 100%)"  # Orange-violet

# Status Colors
SUCCESS           = "#10b981"           # Emerald green
SUCCESS_HOVER      = "#34d399"
SUCCESS_GLOW       = "rgba(16, 185, 129, 0.5)"
DANGER            = "#ef4444"           # Red
WARN              = "#f59e0b"           # Amber

# Text Colors
TEXT_PRIMARY      = "#ffffff"           # Main text
TEXT_SECONDARY     = "#94a3b8"           # Secondary text
TEXT_MUTED        = "#64748b"           # Muted text
TEXT_DIMMED        = "#475569"           # Dimmed text

# Border Colors
BORDER            = "rgba(255, 255, 255, 0.08)"   # Subtle border
BORDER_FOCUS      = "rgba(139, 92, 246, 0.5)"   # Focus border
BORDER_ACTIVE     = "rgba(139, 92, 246, 0.8)"   # Active border

# Scrollbar
SCROLLBAR         = "rgba(255, 255, 255, 0.08)"   # Scrollbar
SCROLLBAR_HANDLE   = "rgba(139, 92, 246, 0.3)"   # Scrollbar handle

# Effects
SHADOW_SM         = "0 4px 12px rgba(0, 0, 0, 0.4)"   # Small shadow
SHADOW_MD         = "0 8px 24px rgba(0, 0, 0, 0.5)"   # Medium shadow
SHADOW_LG         = "0 16px 48px rgba(0, 0, 0, 0.6)"   # Large shadow
SHADOW_GLOW       = "0 0 20px rgba(139, 92, 246, 0.4)"   # Glow shadow
SHADOW_GLOW_SM    = "0 0 12px rgba(139, 92, 246, 0.3)"   # Small glow

# Border Radius
RADIUS_SM         = "6px"
RADIUS_MD         = "12px"
RADIUS_LG         = "20px"
RADIUS_XL         = "28px"

# Transitions
TRANSITION_FAST   = "0.15s cubic-bezier(0.4, 0, 0.2, 1)"
TRANSITION_NORMAL  = "0.2s cubic-bezier(0.25, 0.46, 0.45, 0.94)"
TRANSITION_SLOW    = "0.3s cubic-bezier(0.4, 0, 0.2, 1)"

# ── Typography ────────────────────────────────────────────────────────────────
FONT_FAMILY    = "Segoe UI"   # Falls back gracefully on all platforms
FONT_TITLE     = (FONT_FAMILY, 22, "bold")
FONT_HEADING   = (FONT_FAMILY, 13, "bold")
FONT_SUBHEAD   = (FONT_FAMILY, 11, "bold")
FONT_BODY      = (FONT_FAMILY, 11)
FONT_SMALL     = (FONT_FAMILY, 10)
FONT_TINY      = (FONT_FAMILY, 9)
FONT_MONO      = ("Consolas", 10)   # Console output

# ── Geometry ──────────────────────────────────────────────────────────────────
WIN_W          = 1050
WIN_H          = 680
SIDEBAR_W      = 220
CORNER_RADIUS  = 10
BTN_RADIUS     = 8
CARD_RADIUS    = 10
PAD            = 16
PAD_SM         = 8
PAD_XS         = 4

# ── customtkinter appearance ──────────────────────────────────────────────────
CTK_THEME = {
    "CTk": {
        "fg_color": [BG_DARK, BG_DARK],
    },
    "CTkFrame": {
        "fg_color": [BG_PANEL, BG_PANEL],
        "border_color": [BORDER, BORDER],
        "corner_radius": CORNER_RADIUS,
    },
    "CTkButton": {
        "fg_color": [ACCENT, ACCENT],
        "hover_color": [ACCENT_HOVER, ACCENT_HOVER],
        "text_color": [TEXT_PRIMARY, TEXT_PRIMARY],
        "border_color": [ACCENT_DARK, ACCENT_DARK],
        "corner_radius": BTN_RADIUS,
    },
    "CTkEntry": {
        "fg_color": [BG_INPUT, BG_INPUT],
        "border_color": [BORDER, BORDER],
        "text_color": [TEXT_PRIMARY, TEXT_PRIMARY],
        "placeholder_text_color": [TEXT_MUTED, TEXT_MUTED],
        "corner_radius": BTN_RADIUS,
    },
    "CTkLabel": {
        "text_color": [TEXT_PRIMARY, TEXT_PRIMARY],
    },
    "CTkComboBox": {
        "fg_color": [BG_INPUT, BG_INPUT],
        "border_color": [BORDER, BORDER],
        "button_color": [BG_HOVER, BG_HOVER],
        "button_hover_color": [ACCENT, ACCENT],
        "dropdown_fg_color": [BG_CARD, BG_CARD],
        "text_color": [TEXT_PRIMARY, TEXT_PRIMARY],
        "dropdown_text_color": [TEXT_PRIMARY, TEXT_PRIMARY],
        "corner_radius": BTN_RADIUS,
    },
    "CTkScrollbar": {
        "fg_color": [BG_PANEL, BG_PANEL],
        "button_color": [SCROLLBAR, SCROLLBAR],
        "button_hover_color": [BORDER_ACTIVE, BORDER_ACTIVE],
        "corner_radius": 4,
    },
    "CTkTextbox": {
        "fg_color": [BG_DARK, BG_DARK],
        "border_color": [BORDER, BORDER],
        "text_color": [TEXT_PRIMARY, TEXT_PRIMARY],
        "scrollbar_button_color": [SCROLLBAR, SCROLLBAR],
        "corner_radius": CARD_RADIUS,
    },
    "CTkSlider": {
        "fg_color": [BORDER, BORDER],
        "progress_color": [ACCENT, ACCENT],
        "button_color": [ACCENT_HOVER, ACCENT_HOVER],
        "button_hover_color": [TEXT_PRIMARY, TEXT_PRIMARY],
        "corner_radius": 4,
    },
    "CTkCheckBox": {
        "fg_color": [ACCENT, ACCENT],
        "hover_color": [ACCENT_HOVER, ACCENT_HOVER],
        "border_color": [BORDER_ACTIVE, BORDER_ACTIVE],
        "checkmark_color": [TEXT_PRIMARY, TEXT_PRIMARY],
        "text_color": [TEXT_PRIMARY, TEXT_PRIMARY],
        "corner_radius": 4,
    },
    "CTkSwitch": {
        "fg_color": [BORDER, BORDER],
        "progress_color": [ACCENT, ACCENT],
        "button_color": [TEXT_PRIMARY, TEXT_PRIMARY],
        "button_hover_color": [TEXT_PRIMARY, TEXT_PRIMARY],
        "text_color": [TEXT_PRIMARY, TEXT_PRIMARY],
    },
    "CTkTabview": {
        "fg_color": [BG_PANEL, BG_PANEL],
        "segmented_button_fg_color": [BG_DARK, BG_DARK],
        "segmented_button_selected_color": [ACCENT, ACCENT],
        "segmented_button_selected_hover_color": [ACCENT_HOVER, ACCENT_HOVER],
        "segmented_button_unselected_color": [BG_DARK, BG_DARK],
        "segmented_button_unselected_hover_color": [BG_HOVER, BG_HOVER],
        "text_color": [TEXT_SECONDARY, TEXT_SECONDARY],
        "text_color_disabled": [TEXT_MUTED, TEXT_MUTED],
        "border_color": [BORDER, BORDER],
        "corner_radius": CARD_RADIUS,
    },
    "CTkProgressBar": {
        "fg_color": [BG_INPUT, BG_INPUT],
        "progress_color": [ACCENT, ACCENT],
        "border_color": [BORDER, BORDER],
        "corner_radius": 4,
    },
    "CTkOptionMenu": {
        "fg_color": [BG_INPUT, BG_INPUT],
        "button_color": [BG_HOVER, BG_HOVER],
        "button_hover_color": [ACCENT, ACCENT],
        "dropdown_fg_color": [BG_CARD, BG_CARD],
        "text_color": [TEXT_PRIMARY, TEXT_PRIMARY],
        "dropdown_text_color": [TEXT_PRIMARY, TEXT_PRIMARY],
        "corner_radius": BTN_RADIUS,
    },
}


# ══════════════════════════════════════════════════════════════════════════════
#  THEME PRESET SYSTEM
# ══════════════════════════════════════════════════════════════════════════════

THEMES = {
    "Lunar": {
        "BG_DARK": "#0d0f13", "BG_PANEL": "#13161c", "BG_CARD": "#181c24",
        "BG_INPUT": "#1e2230", "BG_HOVER": "#232840",
        "ACCENT": "#5865f2", "ACCENT_HOVER": "#6d7af5", "ACCENT_DARK": "#3d4dbf",
        "SUCCESS": "#3ba55c", "SUCCESS_HOVER": "#4cc870",
        "DANGER": "#ed4245", "WARN": "#faa61a",
        "TEXT_PRIMARY": "#e8eaf6", "TEXT_SECONDARY": "#8b92a5", "TEXT_MUTED": "#555e78",
        "BORDER": "#252a38", "BORDER_ACTIVE": "#3d4566", "SCROLLBAR": "#2a2f42",
        "bg": "#0d0f13", "panel": "#13161c", "card": "#181c24",
        "accent": "#5865f2", "tp": "#e8eaf6", "ts": "#8b92a5", "tm": "#555e78",
        "ok": "#3ba55c", "warn": "#faa61a", "err": "#ed4245",
    },
    "Cyber": {
        "BG_DARK": "#050505", "BG_PANEL": "#0a0a0f", "BG_CARD": "#0f0f1a",
        "BG_INPUT": "#1a1a2f", "BG_HOVER": "#222238",
        "ACCENT": "#ff00ff", "ACCENT_HOVER": "#ff40ff", "ACCENT_DARK": "#aa00aa",
        "SUCCESS": "#00ff00", "SUCCESS_HOVER": "#00ff40",
        "DANGER": "#ff0055", "WARN": "#ffff00",
        "TEXT_PRIMARY": "#ffffff", "TEXT_SECONDARY": "#cccccc", "TEXT_MUTED": "#666666",
        "BORDER": "#333344", "BORDER_ACTIVE": "#ff00ff", "SCROLLBAR": "#333344",
        "bg": "#050505", "panel": "#0a0a0f", "card": "#0f0f1a",
        "accent": "#ff00ff", "tp": "#ffffff", "ts": "#cccccc", "tm": "#666666",
        "ok": "#00ff00", "warn": "#ffff00", "err": "#ff0055",
    },
    "Forest": {
        "BG_DARK": "#0a0f0a", "BG_PANEL": "#0f1a10", "BG_CARD": "#15201a",
        "BG_INPUT": "#1a2b20", "BG_HOVER": "#1f331d",
        "ACCENT": "#ffd700", "ACCENT_HOVER": "#ffed4a", "ACCENT_DARK": "#ccac00",
        "SUCCESS": "#00ff00", "SUCCESS_HOVER": "#66ff66",
        "DANGER": "#ef4444", "WARN": "#f59e0b",
        "TEXT_PRIMARY": "#e8f5e9", "TEXT_SECONDARY": "#7daa8a", "TEXT_MUTED": "#3d6b4f",
        "BORDER": "#1e3326", "BORDER_ACTIVE": "#2e5c3e", "SCROLLBAR": "#234433",
        "bg": "#0a0f0a", "panel": "#0f1a10", "card": "#15201a",
        "accent": "#ffd700", "tp": "#e8f5e9", "ts": "#7daa8a", "tm": "#3d6b4f",
        "ok": "#00ff00", "warn": "#f59e0b", "err": "#ef4444",
    },
    "Eclipse": {
        "BG_DARK": "#0a0510", "BG_PANEL": "#101018", "BG_CARD": "#16161f",
        "BG_INPUT": "#1f1f2a", "BG_HOVER": "#252533",
        "ACCENT": "#c0c0c0", "ACCENT_HOVER": "#d8d8d8", "ACCENT_DARK": "#a0a0a0",
        "SUCCESS": "#ffffff", "SUCCESS_HOVER": "#e8e8e8",
        "DANGER": "#ff4444", "WARN": "#ffff00",
        "TEXT_PRIMARY": "#ffffff", "TEXT_SECONDARY": "#d0d0d0", "TEXT_MUTED": "#808080",
        "BORDER": "#303040", "BORDER_ACTIVE": "#c0c0c0", "SCROLLBAR": "#303040",
        "bg": "#0a0510", "panel": "#101018", "card": "#16161f",
        "accent": "#c0c0c0", "tp": "#ffffff", "ts": "#d0d0d0", "tm": "#808080",
        "ok": "#ffffff", "warn": "#ffff00", "err": "#ff4444",
    },
    "Sun": {
        "BG_DARK": "#100a05", "BG_PANEL": "#1a1008", "BG_CARD": "#22160a",
        "BG_INPUT": "#2c1e0e", "BG_HOVER": "#372511",
        "ACCENT": "#ff6f00", "ACCENT_HOVER": "#ff8f00", "ACCENT_DARK": "#e65100",
        "SUCCESS": "#66bb6a", "SUCCESS_HOVER": "#81c784",
        "DANGER": "#f44336", "WARN": "#ffc107",
        "TEXT_PRIMARY": "#fff3e0", "TEXT_SECONDARY": "#a07850", "TEXT_MUTED": "#6b4a28",
        "BORDER": "#3a2010", "BORDER_ACTIVE": "#ff8f00", "SCROLLBAR": "#4a2c12",
        "bg": "#100a05", "panel": "#1a1008", "card": "#22160a",
        "accent": "#ff6f00", "tp": "#fff3e0", "ts": "#a07850", "tm": "#6b4a28",
        "ok": "#66bb6a", "warn": "#ffc107", "err": "#f44336",
    },
    "Amber": {
        "BG_DARK": "#1a0a05", "BG_PANEL": "#251008", "BG_CARD": "#301a0a",
        "BG_INPUT": "#3a2513", "BG_HOVER": "#452d18",
        "ACCENT": "#ff6b35", "ACCENT_HOVER": "#ff8c44", "ACCENT_DARK": "#e65112",
        "SUCCESS": "#63c5ff", "SUCCESS_HOVER": "#73d8ff",
        "DANGER": "#ff2f55", "WARN": "#ffbe4d",
        "TEXT_PRIMARY": "#fff1e0", "TEXT_SECONDARY": "#f2d0c7", "TEXT_MUTED": "#a07a5e",
        "BORDER": "#3d251f", "BORDER_ACTIVE": "#ff6b35", "SCROLLBAR": "#3d251f",
        "bg": "#1a0a05", "panel": "#251008", "card": "#301a0a",
        "accent": "#ff6b35", "tp": "#fff1e0", "ts": "#f2d0c7", "tm": "#a07a5e",
        "ok": "#63c5ff", "warn": "#ffbe4d", "err": "#ff2f55",
    },
    "Nebula": {
        "BG_DARK": "#050510", "BG_PANEL": "#0a0a18", "BG_CARD": "#10102a",
        "BG_INPUT": "#1a1a35", "BG_HOVER": "#1f1f45",
        "ACCENT": "#d946ef", "ACCENT_HOVER": "#e879f9", "ACCENT_DARK": "#a21caf",
        "SUCCESS": "#ec4899", "SUCCESS_HOVER": "#f472b6",
        "DANGER": "#ef4444", "WARN": "#fbbf24",
        "TEXT_PRIMARY": "#f5f3ff", "TEXT_SECONDARY": "#d4b8fa", "TEXT_MUTED": "#8b6cba",
        "BORDER": "#2a1a35", "BORDER_ACTIVE": "#d946ef", "SCROLLBAR": "#2a1a35",
        "bg": "#050510", "panel": "#0a0a18", "card": "#10102a",
        "accent": "#d946ef", "tp": "#f5f3ff", "ts": "#d4b8fa", "tm": "#8b6cba",
        "ok": "#ec4899", "warn": "#fbbf24", "err": "#ef4444",
    },
    "Matrix": {
        "BG_DARK": "#000000", "BG_PANEL": "#0a0a0a", "BG_CARD": "#0f0f0f",
        "BG_INPUT": "#141414", "BG_HOVER": "#1a1a1a",
        "ACCENT": "#00ff41", "ACCENT_HOVER": "#39ff6a", "ACCENT_DARK": "#00b32d",
        "SUCCESS": "#00ff41", "SUCCESS_HOVER": "#39ff6a",
        "DANGER": "#ff0000", "WARN": "#ffff00",
        "TEXT_PRIMARY": "#00ff41", "TEXT_SECONDARY": "#009922", "TEXT_MUTED": "#005511",
        "BORDER": "#003311", "BORDER_ACTIVE": "#00ff41", "SCROLLBAR": "#003311",
        "bg": "#000000", "panel": "#0a0a0a", "card": "#0f0f0f",
        "accent": "#00ff41", "tp": "#00ff41", "ts": "#009922", "tm": "#005511",
        "ok": "#00ff41", "warn": "#ffff00", "err": "#ff0000",
    },
    "Glass": {
        "BG_DARK": "#0a0a10", "BG_PANEL": "#101020", "BG_CARD": "#151530",
        "BG_INPUT": "#1f1f40", "BG_HOVER": "#252550",
        "ACCENT": "#8b5cf6", "ACCENT_HOVER": "#a78bfa", "ACCENT_DARK": "#7c3aed",
        "SUCCESS": "#10b981", "SUCCESS_HOVER": "#34d399",
        "DANGER": "#ef4444", "WARN": "#f59e0b",
        "TEXT_PRIMARY": "#ffffff", "TEXT_SECONDARY": "#a5b4fc", "TEXT_MUTED": "#6366f1",
        "BORDER": "#1a1a35", "BORDER_ACTIVE": "#8b5cf6", "SCROLLBAR": "#1a1a35",
        "bg": "#0a0a10", "panel": "#101020", "card": "#151530",
        "accent": "#8b5cf6", "tp": "#ffffff", "ts": "#a5b4fc", "tm": "#6366f1",
        "ok": "#10b981", "warn": "#f59e0b", "err": "#ef4444",
    },
    "Dark": {
        "BG_DARK": "#0a0a0a", "BG_PANEL": "#121212", "BG_CARD": "#1a1a1a",
        "BG_INPUT": "#1e1e1e", "BG_HOVER": "#252525",
        "ACCENT": "#a0aec0", "ACCENT_HOVER": "#cbd5e0", "ACCENT_DARK": "#718096",
        "SUCCESS": "#48bb78", "SUCCESS_HOVER": "#68d391",
        "DANGER": "#f56565", "WARN": "#ed8936",
        "TEXT_PRIMARY": "#ffffff", "TEXT_SECONDARY": "#e2e8f0", "TEXT_MUTED": "#718096",
        "BORDER": "#2d3748", "BORDER_ACTIVE": "#a0aec0", "SCROLLBAR": "#2d3748",
        "bg": "#0a0a0a", "panel": "#121212", "card": "#1a1a1a",
        "accent": "#a0aec0", "tp": "#ffffff", "ts": "#e2e8f0", "tm": "#718096",
        "ok": "#48bb78", "warn": "#ed8936", "err": "#f56565",
    },
    "Ocean": {
        "BG_DARK": "#050a18", "BG_PANEL": "#0a1828", "BG_CARD": "#0f2035",
        "BG_INPUT": "#152840", "BG_HOVER": "#1a304d",
        "ACCENT": "#0ea5e9", "ACCENT_HOVER": "#38bdf8", "ACCENT_DARK": "#0284c7",
        "SUCCESS": "#22d3ee", "SUCCESS_HOVER": "#67e8f9",
        "DANGER": "#ef4444", "WARN": "#f59e0b",
        "TEXT_PRIMARY": "#ecfeff", "TEXT_SECONDARY": "#5eead4", "TEXT_MUTED": "#0c4a6e",
        "BORDER": "#102030", "BORDER_ACTIVE": "#0ea5e9", "SCROLLBAR": "#102030",
        "bg": "#050a18", "panel": "#0a1828", "card": "#0f2035",
        "accent": "#0ea5e9", "tp": "#ecfeff", "ts": "#5eead4", "tm": "#0c4a6e",
        "ok": "#22d3ee", "warn": "#f59e0b", "err": "#ef4444",
    },
    "Crimson": {
        "BG_DARK": "#0f0505", "BG_PANEL": "#1a0505", "BG_CARD": "#221010",
        "BG_INPUT": "#2b1515", "BG_HOVER": "#331a1a",
        "ACCENT": "#ef4444", "ACCENT_HOVER": "#f87171", "ACCENT_DARK": "#dc2626",
        "SUCCESS": "#22c55e", "SUCCESS_HOVER": "#4ade80",
        "DANGER": "#ff1744", "WARN": "#ff9800",
        "TEXT_PRIMARY": "#fff1f1", "TEXT_SECONDARY": "#fca5a5", "TEXT_MUTED": "#7f1d1d",
        "BORDER": "#3a1515", "BORDER_ACTIVE": "#ef4444", "SCROLLBAR": "#3a1515",
        "bg": "#0f0505", "panel": "#1a0505", "card": "#221010",
        "accent": "#ef4444", "tp": "#fff1f1", "ts": "#fca5a5", "tm": "#7f1d1d",
        "ok": "#22c55e", "warn": "#ff9800", "err": "#ff1744",
    },
    "Aurora": {
        "BG_DARK": "#0a0515", "BG_PANEL": "#101025", "BG_CARD": "#151535",
        "BG_INPUT": "#1a1a45", "BG_HOVER": "#1f1f55",
        "ACCENT": "#8b5cf6", "ACCENT_HOVER": "#a78bfa", "ACCENT_DARK": "#7c3aed",
        "SUCCESS": "#34d399", "SUCCESS_HOVER": "#6ee7b7",
        "DANGER": "#f43f5e", "WARN": "#fbbf24",
        "TEXT_PRIMARY": "#f5f3ff", "TEXT_SECONDARY": "#d4b8fa", "TEXT_MUTED": "#6366f1",
        "BORDER": "#2a1a35", "BORDER_ACTIVE": "#8b5cf6", "SCROLLBAR": "#2a1a35",
        "bg": "#0a0515", "panel": "#101025", "card": "#151535",
        "accent": "#8b5cf6", "tp": "#f5f3ff", "ts": "#d4b8fa", "tm": "#6366f1",
        "ok": "#34d399", "warn": "#fbbf24", "err": "#f43f5e",
    },
    "Grid": {
        "BG_DARK": "#0a0a0e", "BG_PANEL": "#12121a", "BG_CARD": "#1a1a25",
        "BG_INPUT": "#22222f", "BG_HOVER": "#2a2a3a",
        "ACCENT": "#0ea5e9", "ACCENT_HOVER": "#38bdf8", "ACCENT_DARK": "#0284c7",
        "SUCCESS": "#10b981", "SUCCESS_HOVER": "#34d399",
        "DANGER": "#ef4444", "WARN": "#f59e0b",
        "TEXT_PRIMARY": "#e2e8f0", "TEXT_SECONDARY": "#94a3b8", "TEXT_MUTED": "#475569",
        "BORDER": "#2d3748", "BORDER_ACTIVE": "#0ea5e9", "SCROLLBAR": "#2d3748",
        "bg": "#0a0a0e", "panel": "#12121a", "card": "#1a1a25",
        "accent": "#0ea5e9", "tp": "#e2e8f0", "ts": "#94a3b8", "tm": "#475569",
        "ok": "#10b981", "warn": "#f59e0b", "err": "#ef4444",
    },
    "Abyss": {
        "BG_DARK": "#050515", "BG_PANEL": "#0a0a1e", "BG_CARD": "#0f0f2a",
        "BG_INPUT": "#141435", "BG_HOVER": "#1a1a45",
        "ACCENT": "#06b6d4", "ACCENT_HOVER": "#5a9fd4", "ACCENT_DARK": "#0493b5",
        "SUCCESS": "#78ff55", "SUCCESS_HOVER": "#a3ff80",
        "DANGER": "#ff5858", "WARN": "#fbbf24",
        "TEXT_PRIMARY": "#e0e8f0", "TEXT_SECONDARY": "#a0c4e8", "TEXT_MUTED": "#5a7ab8",
        "BORDER": "#1a1a35", "BORDER_ACTIVE": "#06b6d4", "SCROLLBAR": "#1a1a35",
        "bg": "#050515", "panel": "#0a0a1e", "card": "#0f0f2a",
        "accent": "#06b6d4", "tp": "#e0e8f0", "ts": "#a0c4e8", "tm": "#5a7ab8",
        "ok": "#78ff55", "warn": "#fbbf24", "err": "#ff5858",
    },
    "Green": {
        "BG_DARK": "#0d1a0d", "BG_PANEL": "#152515", "BG_CARD": "#1c3520",
        "BG_INPUT": "#253d2b", "BG_HOVER": "#2d4a35",
        "ACCENT": "#3a5a4c", "ACCENT_HOVER": "#5a7a6e", "ACCENT_DARK": "#2d4a35",
        "SUCCESS": "#63c5ff", "SUCCESS_HOVER": "#73d8ff",
        "DANGER": "#ff5858", "WARN": "#fbbf24",
        "TEXT_PRIMARY": "#e0e8f0", "TEXT_SECONDARY": "#a0c4e8", "TEXT_MUTED": "#5a7ab8",
        "BORDER": "#2d4a35", "BORDER_ACTIVE": "#3a5a4c", "SCROLLBAR": "#2d4a35",
        "bg": "#0d1a0d", "panel": "#152515", "card": "#1c3520",
        "accent": "#3a5a4c", "tp": "#e0e8f0", "ts": "#a0c4e8", "tm": "#5a7ab8",
        "ok": "#63c5ff", "warn": "#fbbf24", "err": "#ff5858",
    },
    "Pink": {
        "BG_DARK": "#2a0a1b", "BG_PANEL": "#35152a", "BG_CARD": "#402035",
        "BG_INPUT": "#4b2a40", "BG_HOVER": "#55354a",
        "ACCENT": "#ec4899", "ACCENT_HOVER": "#f472b6", "ACCENT_DARK": "#c026d3",
        "SUCCESS": "#78ff55", "SUCCESS_HOVER": "#a3ff80",
        "DANGER": "#ff5858", "WARN": "#fbbf24",
        "TEXT_PRIMARY": "#fff0f5", "TEXT_SECONDARY": "#f2d0c7", "TEXT_MUTED": "#a07a5e",
        "BORDER": "#3d253d", "BORDER_ACTIVE": "#ec4899", "SCROLLBAR": "#3d253d",
        "bg": "#2a0a1b", "panel": "#35152a", "card": "#402035",
        "accent": "#ec4899", "tp": "#fff0f5", "ts": "#f2d0c7", "tm": "#a07a5e",
        "ok": "#78ff55", "warn": "#fbbf24", "err": "#ff5858",
    },
    "Onyx": {
        "BG_DARK": "#000005", "BG_PANEL": "#0a0a15", "BG_CARD": "#101020",
        "BG_INPUT": "#15152a", "BG_HOVER": "#1a1a35",
        "ACCENT": "#8b5cf6", "ACCENT_HOVER": "#a78bfa", "ACCENT_DARK": "#7c3aed",
        "SUCCESS": "#10b981", "SUCCESS_HOVER": "#34d399",
        "DANGER": "#ef4444", "WARN": "#f59e0b",
        "TEXT_PRIMARY": "#ffffff", "TEXT_SECONDARY": "#a5b4fc", "TEXT_MUTED": "#6366f1",
        "BORDER": "#1a1a35", "BORDER_ACTIVE": "#8b5cf6", "SCROLLBAR": "#1a1a35",
        "bg": "#000005", "panel": "#0a0a15", "card": "#101020",
        "accent": "#8b5cf6", "tp": "#ffffff", "ts": "#a5b4fc", "tm": "#6366f1",
        "ok": "#10b981", "warn": "#f59e0b", "err": "#ef4444",
    },
    "Ice": {
        "BG_DARK": "#0e1f2f", "BG_PANEL": "#1a2d40", "BG_CARD": "#263a50",
        "BG_INPUT": "#32475c", "BG_HOVER": "#3e556a",
        "ACCENT": "#0ea5e9", "ACCENT_HOVER": "#38bdf8", "ACCENT_DARK": "#0284c7",
        "SUCCESS": "#22d3ee", "SUCCESS_HOVER": "#67e8f9",
        "DANGER": "#ef4444", "WARN": "#f59e0b",
        "TEXT_PRIMARY": "#ecfeff", "TEXT_SECONDARY": "#5eead4", "TEXT_MUTED": "#0c4a6e",
        "BORDER": "#102030", "BORDER_ACTIVE": "#0ea5e9", "SCROLLBAR": "#102030",
        "bg": "#0e1f2f", "panel": "#1a2d40", "card": "#263a50",
        "accent": "#0ea5e9", "tp": "#ecfeff", "ts": "#5eead4", "tm": "#0c4a6e",
        "ok": "#22d3ee", "warn": "#f59e0b", "err": "#ef4444",
    },
    "Gold": {
        "BG_DARK": "#2a1808", "BG_PANEL": "#352510", "BG_CARD": "#40301a",
        "BG_INPUT": "#4a3d25", "BG_HOVER": "#554a2d",
        "ACCENT": "#f59e0b", "ACCENT_HOVER": "#fbbf24", "ACCENT_DARK": "#d97706",
        "SUCCESS": "#63c5ff", "SUCCESS_HOVER": "#73d8ff",
        "DANGER": "#ff5858", "WARN": "#fbbf24",
        "TEXT_PRIMARY": "#fff7e4", "TEXT_SECONDARY": "#f3e8c4", "TEXT_MUTED": "#a07a5e",
        "BORDER": "#3d3025", "BORDER_ACTIVE": "#f59e0b", "SCROLLBAR": "#3d3025",
        "bg": "#2a1808", "panel": "#352510", "card": "#40301a",
        "accent": "#f59e0b", "tp": "#fff7e4", "ts": "#f3e8c4", "tm": "#a07a5e",
        "ok": "#63c5ff", "warn": "#fbbf24", "err": "#ff5858",
    },
}

THEME_NAMES  = list(THEMES.keys())
DEFAULT_THEME = "Lunar"


def get_theme(name: str) -> dict:
    return THEMES.get(name, THEMES[DEFAULT_THEME])


def _set_globals(t: dict):
    """Inject a theme dict into this module's global namespace."""
    g = globals()
    for k, v in t.items():
        g[k] = v


def _build_ctk_theme(t: dict) -> dict:
    return {
        "CTk":            {"fg_color": [t["BG_DARK"], t["BG_DARK"]]},
        "CTkFrame":       {"fg_color": [t["BG_PANEL"], t["BG_PANEL"]], "border_color": [t["BORDER"], t["BORDER"]], "corner_radius": 10},
        "CTkButton":      {"fg_color": [t["ACCENT"], t["ACCENT"]], "hover_color": [t["ACCENT_HOVER"], t["ACCENT_HOVER"]], "text_color": [t["TEXT_PRIMARY"], t["TEXT_PRIMARY"]], "border_color": [t["ACCENT_DARK"], t["ACCENT_DARK"]], "corner_radius": 8},
        "CTkEntry":       {"fg_color": [t["BG_INPUT"], t["BG_INPUT"]], "border_color": [t["BORDER"], t["BORDER"]], "text_color": [t["TEXT_PRIMARY"], t["TEXT_PRIMARY"]], "placeholder_text_color": [t["TEXT_MUTED"], t["TEXT_MUTED"]], "corner_radius": 8},
        "CTkLabel":       {"text_color": [t["TEXT_PRIMARY"], t["TEXT_PRIMARY"]]},
        "CTkComboBox":    {"fg_color": [t["BG_INPUT"], t["BG_INPUT"]], "border_color": [t["BORDER"], t["BORDER"]], "button_color": [t["BG_HOVER"], t["BG_HOVER"]], "button_hover_color": [t["ACCENT"], t["ACCENT"]], "dropdown_fg_color": [t["BG_CARD"], t["BG_CARD"]], "text_color": [t["TEXT_PRIMARY"], t["TEXT_PRIMARY"]], "dropdown_text_color": [t["TEXT_PRIMARY"], t["TEXT_PRIMARY"]], "corner_radius": 8},
        "CTkScrollbar":   {"fg_color": [t["BG_PANEL"], t["BG_PANEL"]], "button_color": [t["SCROLLBAR"], t["SCROLLBAR"]], "button_hover_color": [t["BORDER_ACTIVE"], t["BORDER_ACTIVE"]], "corner_radius": 4},
        "CTkTextbox":     {"fg_color": [t["BG_DARK"], t["BG_DARK"]], "border_color": [t["BORDER"], t["BORDER"]], "text_color": [t["TEXT_PRIMARY"], t["TEXT_PRIMARY"]], "scrollbar_button_color": [t["SCROLLBAR"], t["SCROLLBAR"]], "corner_radius": 10},
        "CTkSlider":      {"fg_color": [t["BORDER"], t["BORDER"]], "progress_color": [t["ACCENT"], t["ACCENT"]], "button_color": [t["ACCENT_HOVER"], t["ACCENT_HOVER"]], "button_hover_color": [t["TEXT_PRIMARY"], t["TEXT_PRIMARY"]], "corner_radius": 4},
        "CTkCheckBox":    {"fg_color": [t["ACCENT"], t["ACCENT"]], "hover_color": [t["ACCENT_HOVER"], t["ACCENT_HOVER"]], "border_color": [t["BORDER_ACTIVE"], t["BORDER_ACTIVE"]], "checkmark_color": [t["TEXT_PRIMARY"], t["TEXT_PRIMARY"]], "text_color": [t["TEXT_PRIMARY"], t["TEXT_PRIMARY"]], "corner_radius": 4},
        "CTkSwitch":      {"fg_color": [t["BORDER"], t["BORDER"]], "progress_color": [t["ACCENT"], t["ACCENT"]], "button_color": [t["TEXT_PRIMARY"], t["TEXT_PRIMARY"]], "button_hover_color": [t["TEXT_PRIMARY"], t["TEXT_PRIMARY"]], "text_color": [t["TEXT_PRIMARY"], t["TEXT_PRIMARY"]]},
        "CTkProgressBar": {"fg_color": [t["BG_INPUT"], t["BG_INPUT"]], "progress_color": [t["ACCENT"], t["ACCENT"]], "border_color": [t["BORDER"], t["BORDER"]], "corner_radius": 4},
        "CTkOptionMenu":  {"fg_color": [t["BG_INPUT"], t["BG_INPUT"]], "button_color": [t["BG_HOVER"], t["BG_HOVER"]], "button_hover_color": [t["ACCENT"], t["ACCENT"]], "dropdown_fg_color": [t["BG_CARD"], t["BG_CARD"]], "text_color": [t["TEXT_PRIMARY"], t["TEXT_PRIMARY"]], "dropdown_text_color": [t["TEXT_PRIMARY"], t["TEXT_PRIMARY"]], "corner_radius": 8},
    }
