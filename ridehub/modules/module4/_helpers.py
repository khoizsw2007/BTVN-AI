"""
Module 4 helpers: shared constants, styling, and utility functions.
"""
import customtkinter as ctk
from ui.theme import UI_FONT, COLORS

FONT_FAMILY = UI_FONT

STATUS_CANCEL_CUSTOMER = ("Cancelled by Customer", "Cancelled")
STATUS_CANCEL_DRIVER = ("Cancelled by Driver",)
STATUS_INCOMPLETE = ("Incomplete", "No Completed", "No Complete")
STATUS_COMPLETED = ("Completed",)


def font(size, weight="normal"):
    return ctk.CTkFont(family=FONT_FAMILY, size=size, weight=weight)


def sql_in(values):
    return "(" + ",".join(["%s"] * len(values)) + ")"


def sql_literals(values):
    return "(" + ",".join("'" + str(v).replace("'", "''") + "'" for v in values) + ")"


def safe_float(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def pct_delta(current, previous):
    current = safe_float(current)
    previous = safe_float(previous)
    if previous == 0:
        return 0.0 if current == 0 else 100.0
    return (current - previous) / previous * 100


def make_card(parent, **kwargs):
    options = {
        "fg_color": COLORS["surface"],
        "corner_radius": 14,
        "border_width": 1,
        "border_color": COLORS["border"],
    }
    options.update(kwargs)
    return ctk.CTkFrame(parent, **options)
