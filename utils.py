"""
utils.py
--------
Formatting helpers shared across all dashboard pages: Indian-style
currency/number grouping, lakh shorthand, and clean date display.
Kept separate from app.py so every page formats numbers identically.
"""

import pandas as pd


def format_inr(value, decimals: int = 2) -> str:
    """Formats a number using the Indian digit-grouping convention."""
    if value is None or pd.isna(value):
        return "₹0.00"

    negative = value < 0
    value = abs(value)

    int_part, _, dec_part = f"{value:,.{decimals}f}".replace(",", "").partition(".")

    # Indian grouping: last 3 digits together, then groups of 2
    if len(int_part) > 3:
        last3 = int_part[-3:]
        rest = int_part[:-3]
        groups = []
        while len(rest) > 2:
            groups.insert(0, rest[-2:])
            rest = rest[:-2]
        if rest:
            groups.insert(0, rest)
        int_part = ",".join(groups) + "," + last3

    formatted = f"₹{int_part}"
    if decimals > 0:
        formatted += f".{dec_part}"

    return f"-{formatted}" if negative else formatted


def format_lakh(value) -> str:
    """Format a value in lakhs."""
    if value is None or pd.isna(value):
        return "₹0.00 Lakh"
    return f"₹{value / 100000:.2f} Lakh"


def format_qty(value) -> str:
    """Whole-number quantity formatting, Indian grouping, no currency symbol."""
    if value is None or pd.isna(value):
        return "0"
    return format_inr(value, decimals=0).replace("₹", "")


def format_date_pretty(date_value) -> str:
    """Example: 2026-04-04 -> '04 Apr 2026'"""
    if date_value is None or pd.isna(date_value):
        return "-"
    return pd.to_datetime(date_value).strftime("%d %b %Y")


def month_label(yyyy_mm: str) -> str:
    """Example: '2026-02' -> 'Feb 2026'"""
    try:
        return pd.to_datetime(yyyy_mm + "-01").strftime("%b %Y")
    except Exception:
        return yyyy_mm
