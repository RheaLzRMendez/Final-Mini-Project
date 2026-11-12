"""
theme_manager.py - Global Light/Dark Theme Controller.
"""

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
    "danger": "#F87171",
    "success": "#34D399",
    "calendar_bg": "#18181B",
    "calendar_fg": "#F4F4F5",
    "calendar_accent": "#F87171"
}

current_mode = "Light"
COLORS = LIGHT_THEME.copy()
FONT = "Segoe UI"


def toggle_theme():
    global current_mode, COLORS
    if current_mode == "Light":
        current_mode = "Dark"
        COLORS.update(DARK_THEME)
    else:
        current_mode = "Light"
        COLORS.update(LIGHT_THEME)
    return current_mode