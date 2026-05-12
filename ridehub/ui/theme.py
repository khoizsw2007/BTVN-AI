"""
Shared theme: fonts, colors, and matplotlib configuration.
Import from here instead of hardcoding font tuples or color hex values.
"""
import sys

import customtkinter as ctk
import matplotlib

# ── Cross-platform font that has the ₹ glyph ────────────────────
if sys.platform == "win32":
    UI_FONT = "Segoe UI"
elif sys.platform == "darwin":
    UI_FONT = "Arial Unicode MS"
else:
    UI_FONT = "Noto Sans"

# ── Fix rupee symbol ₹ in matplotlib on all OS ──────────────────
matplotlib.rcParams['font.family'] = 'sans-serif'
matplotlib.rcParams['font.sans-serif'] = [
    'Segoe UI',
    'Arial Unicode MS',
    'Noto Sans',
    'DejaVu Sans',
    'FreeSans',
]
matplotlib.rcParams['axes.unicode_minus'] = False


def shared_font(size, weight="normal"):
    """Return a CTkFont with the cross-platform UI font."""
    return ctk.CTkFont(family=UI_FONT, size=size, weight=weight)


# ── Dashboard color palette (module1) ───────────────────────────
STATUS_COLORS = {
    "Completed":             "#10B981",
    "Cancelled by Customer": "#EF4444",
    "Cancelled by Driver":   "#F59E0B",
    "Incomplete":            "#6B7280",
    "No Driver Found":       "#9CA3AF",
}
DEFAULT_COLOR = "#CBD5E1"
BAR_COLORS = ["#3B82F6", "#10B981", "#F59E0B", "#8B5CF6", "#EF4444", "#14B8A6"]

# ── Risk analysis color palette (module4) ────────────────────────
COLORS = {
    "page": "#f7f8fa",
    "surface": "#ffffff",
    "border": "#e8e8e8",
    "subtle": "#f5f5f5",
    "text": "#1a1a1a",
    "muted": "#888888",
    "muted_light": "#aaaaaa",
    "primary": "#6C63FF",
    "primary_dark": "#4F46E5",
    "primary_light": "#EEF2FF",
    "orange": "#F97316",
    "orange_bg": "#FFF0E6",
    "yellow": "#FCD34D",
    "yellow_bg": "#FEF3C7",
    "red": "#EF4444",
    "red_bg": "#FEE2E2",
    "green": "#10B981",
    "green_bg": "#D1FAE5",
    "blue": "#3B82F6",
    "sky_bg": "#E0F2FE",
    "purple": "#7C3AED",
    "purple_bg": "#F3E8FF",
}
