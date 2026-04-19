from __future__ import annotations

import copy
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, get_args

from fastapi.routing import APIRoute
from pydantic import BaseModel

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from app.main import app

FRONTEND_TYPES_DIR = REPO_ROOT / "frontend" / "src" / "types"
TARGET_FILES = ("backtest.ts", "factor.ts", "market.ts", "tools.ts", "config.ts")


def main() -> None:
    grouped_models: dict[str, list[type[BaseModel]]] = defaultdict(list)
    for model in collect_route_contract_models():
        grouped_models[resolve_target_file(model)].append(model)

    for filename in TARGET_FILES:
        content = render_file(grouped_models.get(filename, []))
        (FRONTEND_TYPES_DIR / filename).write_text(content, encoding="utf-8")


def collect_route_contract_models() -> tuple[type[BaseModel], ...]:
    models: dict[str, type[BaseModel]] = {}
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        for model in extract_pydantic_models(route.response_model):
            models.setdefault(model.__name__, model)
        body_field = getattr(route, "body_field", None)
        if body_field is not None:
            for model in extract_pydantic_models(body_field.type_):
                models.setdefault(model.__name__, model)
    if not models:
        raise RuntimeError("No FastAPI contract models were discovered")
    return tuple(models.values())


def extract_pydantic_models(annotation: Any) -> tuple[type[BaseModel], ...]:
    if annotation is None:
        return ()
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return (annotation,)
    models: list[type[BaseModel]] = []
    for arg in get_args(annotation):
        models.extend(extract_pydantic_models(arg))
    return tuple(models)


def resolve_target_file(model: type[BaseModel]) -> str:
    module_name = model.__module__
    if module_name.endswith(".factor"):
        return "factor.ts"
    if module_name.endswith(".market") or module_name.endswith(".binance_market"):
        return "market.ts"
    if module_name.endswith(".tools"):
        return "tools.ts"
    if module_name.endswith(".config"):
        return "config.ts"
    return "backtest.ts"


def render_file(models: list[type[BaseModel]]) -> str:
    definitions: dict[str, dict[str, Any]] = {}
    root_names: list[str] = []
    for model in models:
        name = model.__name__
        schema = copy.deepcopy(model.model_json_schema(ref_template="#/$defs/{model}"))
        schema = remap_schema(schema)
        definitions[name] = strip_defs(schema)
        root_names.append(name)
        for def_name, def_schema in schema.get("$defs", {}).items():
            normalized_def_schema = strip_defs(def_schema)
            if def_name not in definitions or is_self_reference_schema(definitions[def_name], def_name):
                definitions[def_name] = normalized_def_schema

    lines = [
        "// This file is generated from backend FastAPI route contracts.",
        "// Do not edit manually.",
        "",
    ]

    emitted: set[str] = set()
    for name in root_names + sorted(definitions.keys()):
        if name in emitted:
            continue
        lines.extend(emit_named_definition(name, definitions[name]))
        lines.append("")
        emitted.add(name)

    return "\n".join(lines)


def remap_schema(value: Any) -> Any:
    if isinstance(value, dict):
        remapped: dict[str, Any] = {}
        for key, item in value.items():
            if key == "$defs":
                remapped[key] = {def_name: remap_schema(def_schema) for def_name, def_schema in item.items()}
                continue
            if key == "$ref" and isinstance(item, str):
                remapped[key] = f"#/$defs/{item.split('/')[-1]}"
                continue
            remapped[key] = remap_schema(item)
        return remapped
    if isinstance(value, list):
        return [remap_schema(item) for item in value]
    return value


def strip_defs(schema: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(schema)
    result.pop("$defs", None)
    result.pop("title", None)
    return result


def is_self_reference_schema(schema: dict[str, Any], name: str) -> bool:
    return isinstance(schema, dict) and schema.get("$ref") == f"#/$defs/{name}"


def emit_named_definition(name: str, schema: dict[str, Any]) -> list[str]:
    if is_object_schema(schema):
        return emit_interface(name, schema)
    return [f"export type {name} = {render_type(schema)}"]


def emit_interface(name: str, schema: dict[str, Any]) -> list[str]:
    properties = schema.get("properties", {})
    required = set(schema.get("required", []))
    lines = [f"export interface {name} {{"]
    for prop_name, prop_schema in properties.items():
        optional = "?" if prop_name not in required else ""
        lines.append(f"  {prop_name}{optional}: {render_type(prop_schema)}")
    if schema.get("additionalProperties"):
        lines.append(f"  [key: string]: {render_type(schema['additionalProperties'])}")
    lines.append("}")
    return lines


def render_type(schema: dict[str, Any]) -> str:
    if schema is True:
        return "unknown"
    if schema is False:
        return "never"
    if not isinstance(schema, dict):
        return "unknown"
    if "$ref" in schema:
        return schema["$ref"].split("/")[-1]
    if "anyOf" in schema:
        return " | ".join(dict.fromkeys(render_type(item) for item in schema["anyOf"]))
    if "oneOf" in schema:
        return " | ".join(dict.fromkeys(render_type(item) for item in schema["oneOf"]))
    if "allOf" in schema:
        return " & ".join(dict.fromkeys(render_type(item) for item in schema["allOf"]))
    if "enum" in schema:
        return " | ".join(json.dumps(item) for item in schema["enum"])
    if schema.get("type") == "array":
        return f"Array<{render_type(schema.get('items', {}))}>"
    if is_object_schema(schema):
        properties = schema.get("properties", {})
        required = set(schema.get("required", []))
        members = []
        for prop_name, prop_schema in properties.items():
            optional = "?" if prop_name not in required else ""
            members.append(f"{prop_name}{optional}: {render_type(prop_schema)}")
        if schema.get("additionalProperties"):
            members.append(f"[key: string]: {render_type(schema['additionalProperties'])}")
        return "{ " + "; ".join(members) + " }"
    if schema.get("additionalProperties") is True:
        return "Record<string, unknown>"
    if schema.get("additionalProperties") is not None:
        return f"Record<string, {render_type(schema['additionalProperties'])}>"
    schema_type = schema.get("type")
    if schema_type in {"integer", "number"}:
        return "number"
    if schema_type == "string":
        return "string"
    if schema_type == "boolean":
        return "boolean"
    if schema_type == "null":
        return "null"
    return "unknown"


def is_object_schema(schema: dict[str, Any]) -> bool:
    return schema.get("type") == "object" or "properties" in schema

if __name__ == "__main__":
    main()
