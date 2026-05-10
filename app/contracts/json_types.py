from __future__ import annotations

from typing import TypeAlias

JsonScalar: TypeAlias = str | int | float | bool | None
JsonFlatArray: TypeAlias = list[JsonScalar]
JsonFlatObject: TypeAlias = dict[str, JsonScalar]
JsonValue: TypeAlias = JsonScalar | JsonFlatArray | JsonFlatObject | list[JsonFlatObject] | dict[str, JsonFlatArray]
JsonObject: TypeAlias = dict[str, JsonValue]
