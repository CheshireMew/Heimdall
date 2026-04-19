from __future__ import annotations

from typing import Any


def to_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    return float(value)


def to_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    return int(float(value))


def safe_float(value: Any) -> float | None:
    try:
        return to_float(value)
    except (TypeError, ValueError):
        return None
