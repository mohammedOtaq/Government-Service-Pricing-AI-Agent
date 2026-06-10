from __future__ import annotations


def money(value: object) -> str:
    if value is None:
        return "Not available"
    try:
        return f"{float(value):,.2f}"
    except (TypeError, ValueError):
        return str(value)


def pct(value: object) -> str:
    if value is None:
        return "Not available"
    try:
        return f"{float(value) * 100:.1f}%"
    except (TypeError, ValueError):
        return str(value)
