from __future__ import annotations

from collections.abc import Callable
from functools import cmp_to_key
from typing import Any, TypeVar

from .binance_numbers import safe_float

TRow = TypeVar("TRow")


def board_key(field: str, direction: str) -> str:
    return f"{field}_{direction}"


def compare_nullable_number(left: Any, right: Any, direction: str) -> int:
    left_value = safe_float(left)
    right_value = safe_float(right)
    if left_value is None and right_value is None:
        return 0
    if left_value is None:
        return 1
    if right_value is None:
        return -1
    if left_value == right_value:
        return 0
    if direction == "desc":
        return -1 if left_value > right_value else 1
    return -1 if left_value < right_value else 1


def compare_text(left: Any, right: Any) -> int:
    left_value = str(left or "")
    right_value = str(right or "")
    return (left_value > right_value) - (left_value < right_value)


def sort_rows_by_number(
    rows: list[TRow],
    field: str,
    direction: str,
    *,
    value_getter: Callable[[TRow, str], Any],
    tie_breaker: Callable[[TRow, TRow], int],
) -> list[TRow]:
    def compare(left: TRow, right: TRow) -> int:
        primary = compare_nullable_number(value_getter(left, field), value_getter(right, field), direction)
        if primary != 0:
            return primary
        return tie_breaker(left, right)

    return sorted(rows, key=cmp_to_key(compare))
