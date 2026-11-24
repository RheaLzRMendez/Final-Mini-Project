"""
theme_manager.py - Global Light/Dark Theme Controller.
"""

from tkinter import ttk

LIGHT_THEME = {
    "background": "#F8FAFC",
    "card": "#FFFFFF",
    "primary": "#4F46E5",
    "primary_dark": "#4338CA",
    "text": "#0F172A",
    "secondary": "#64748B",
    "input": "#F1F5F9",
    "border": "#E2E8F0",
    "light": "#EEF2FF",
    "toggle_inactive": "#E2E8F0",
    "toggle_inactive_text": "#64748B",
    "scrollbar_trough": "#F1F5F9",
    "scrollbar_thumb": "#CBD5E1",
    "scrollbar_hover": "#94A3B8",
    "danger": "#EF4444",
    "success": "#10B981",
    "calendar_bg": "#1F2228",
    "calendar_fg": "#FFFFFF",
    "calendar_accent": "#F87171"
}

DARK_THEME = {
    "background": "#0F172A",
    "card": "#1E293B",
    "primary": "#6366F1",
    "primary_dark": "#4F46E5",
    "text": "#F8FAFC",
    "secondary": "#94A3B8",
    "input": "#334155",
    "border": "#475569",
    "light": "#1E1B4B",
    "toggle_inactive": "#262D42",
    "toggle_inactive_text": "#CBD5E1",
    "scrollbar_trough": "#1E293B",
    "scrollbar_thumb": "#334155",
    "scrollbar_hover": "#4F46E5",
    "danger": "#F87171",
    "success": "#34D399",
    "calendar_bg": "#18181B",
    "calendar_fg": "#F4F4F5",
    "calendar_accent": "#F87171"
}

current_mode = "Light"
COLORS = LIGHT_THEME.copy()
FONT = "Segoe UI"


def configure_scrollbar_style(style=None):
    """Apply flat, theme-aware scrollbar styling to the clam ttk theme."""
    style = style or ttk.Style()
    style.theme_use("clam")
    for orientation in ("Vertical", "Horizontal"):
        style_name = f"{orientation}.TScrollbar"
        style.configure(
            style_name,
            background=COLORS["scrollbar_thumb"],
            troughcolor=COLORS["scrollbar_trough"],
            bordercolor=COLORS["scrollbar_trough"],
            arrowcolor=COLORS["scrollbar_trough"],
            arrowsize=0,
            width=8,
            borderwidth=0,
            relief="flat",
            gripcount=0
        )
        style.map(
            style_name,
            background=[("active", COLORS["scrollbar_hover"])],
            arrowcolor=[("active", COLORS["scrollbar_trough"])]
        )
    return style


def toggle_theme():
    global current_mode, COLORS
    if current_mode == "Light":
        current_mode = "Dark"
        COLORS.update(DARK_THEME)
    else:
        current_mode = "Light"
        COLORS.update(LIGHT_THEME)
    return current_mode