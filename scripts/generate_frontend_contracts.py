from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any

from pydantic import BaseModel

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from app.schemas.backtest import (
    BacktestDetailResponse,
    BacktestEquityPointResponse,
    BacktestMetricsResponse,
    BacktestPortfolioRequest,
    BacktestResearchRequest,
    BacktestRunResponse,
    BacktestSignalResponse,
    BacktestStartRequest,
    BacktestStartResponse,
    BacktestTradeResponse,
    IndicatorDefinitionCreateRequest,
    PaginationResponse,
    PaperStartRequest,
    PaperStartResponse,
    PaperStopResponse,
    StrategyDefinitionResponse,
    StrategyEditorContractResponse,
    StrategyGroupLogicResponse,
    StrategyIndicatorEngineResponse,
    StrategyIndicatorRegistryResponse,
    StrategyOperatorResponse,
    StrategyTemplateCreateRequest,
    StrategyTemplateResponse,
    StrategyVersionCreateRequest,
    StrategyVersionResponse,
)
from app.schemas.backtest_result import (
    BacktestDateRangeResponse,
    BacktestIterationSummaryResponse,
    BacktestOptimizationSummaryResponse,
    BacktestOptimizationTrialResponse,
    BacktestPairBreakdownResponse,
    BacktestPaperLiveResponse,
    BacktestPaperPositionResponse,
    BacktestPortfolioPayloadResponse,
    BacktestPortfolioSummaryResponse,
    BacktestReportResponse,
    BacktestReportSnapshotResponse,
    BacktestResearchPayloadResponse,
    BacktestResearchReportResponse,
    BacktestRollingWindowResponse,
    BacktestRunMetadataResponse,
    BacktestRuntimeStateResponse,
    BacktestSampleRangesResponse,
    BacktestStrategySummaryResponse,
)
from app.schemas.factor import (
    FactorBlendComponentResponse,
    FactorBlendResponse,
    FactorCatalogItemResponse,
    FactorCatalogResponse,
    FactorDetailResponse,
    FactorDroppedComponentResponse,
    FactorExecutionRequest,
    FactorExecutionResponse,
    FactorForwardMetricResponse,
    FactorLagPointResponse,
    FactorNormalizedPointResponse,
    FactorQuantileBucketResponse,
    FactorResearchRequest,
    FactorResearchResponse,
    FactorResearchRunDetailResponse,
    FactorResearchSummaryResponse,
    FactorRollingPointResponse,
    FactorScorecardResponse,
)
from app.schemas.strategy_contract import (
    StrategyExecutionConfigResponse,
    StrategyGroupNodeResponse,
    StrategyIndicatorConfigResponse,
    StrategyIndicatorOutputResponse,
    StrategyIndicatorParamResponse,
    StrategyPartialExitResponse,
    StrategyRiskConfigResponse,
    StrategyRoiTargetResponse,
    StrategyRuleSourceResponse,
    StrategyStateBranchResponse,
    StrategyTemplateConfigResponse,
    StrategyTrailingConfigResponse,
)


FRONTEND_TYPES_DIR = REPO_ROOT / "frontend" / "src" / "types"

ALIAS_MAP = {
    "BacktestPortfolioRequest": "BacktestPortfolioConfig",
    "BacktestResearchRequest": "BacktestResearchConfig",
    "BacktestMetricsResponse": "BacktestMetrics",
    "BacktestSignalResponse": "BacktestSignal",
    "BacktestTradeResponse": "BacktestTrade",
    "BacktestEquityPointResponse": "BacktestEquityPoint",
    "PaginationResponse": "BacktestPagination",
    "BacktestRunResponse": "BacktestRun",
    "BacktestRunMetadataResponse": "BacktestRunMetadata",
    "BacktestReportResponse": "BacktestReport",
    "BacktestReportSnapshotResponse": "BacktestReportSnapshot",
    "BacktestDateRangeResponse": "BacktestDateRange",
    "BacktestPairBreakdownResponse": "BacktestPairBreakdown",
    "BacktestStrategySummaryResponse": "BacktestStrategySummary",
    "BacktestPortfolioSummaryResponse": "BacktestPortfolioSummary",
    "BacktestPortfolioPayloadResponse": "BacktestPortfolioPayload",
    "BacktestResearchPayloadResponse": "BacktestResearchPayload",
    "BacktestOptimizationTrialResponse": "BacktestOptimizationTrial",
    "BacktestOptimizationSummaryResponse": "BacktestOptimizationSummary",
    "BacktestIterationSummaryResponse": "BacktestIterationSummary",
    "BacktestRollingWindowResponse": "BacktestRollingWindow",
    "BacktestResearchReportResponse": "BacktestResearchReport",
    "BacktestSampleRangesResponse": "BacktestSampleRanges",
    "BacktestPaperPositionResponse": "BacktestPaperPosition",
    "BacktestRuntimeStateResponse": "BacktestRuntimeState",
    "BacktestPaperLiveResponse": "BacktestPaperLive",
    "BacktestRunDefaultsResponse": "BacktestRunDefaults",
    "StrategyVersionResponse": "StrategyVersion",
    "StrategyDefinitionResponse": "StrategyDefinition",
    "StrategyIndicatorRegistryResponse": "StrategyIndicatorRegistryItem",
    "StrategyOperatorResponse": "StrategyOperator",
    "StrategyGroupLogicResponse": "StrategyGroupLogic",
    "StrategyIndicatorEngineResponse": "StrategyIndicatorEngine",
    "StrategyTemplateResponse": "StrategyTemplate",
    "StrategyEditorContractResponse": "StrategyEditorContract",
    "StrategyRunProfileResponse": "StrategyRunProfile",
    "StrategyConditionNodeResponse": "StrategyConditionNode",
    "StrategyGroupNodeResponse": "StrategyGroupNode",
    "StrategyIndicatorConfigResponse": "StrategyIndicatorConfig",
    "StrategyExecutionConfigResponse": "StrategyExecutionConfig",
    "StrategyIndicatorOutputResponse": "StrategyIndicatorOutput",
    "StrategyIndicatorParamResponse": "StrategyIndicatorParam",
    "StrategyPartialExitResponse": "StrategyPartialExit",
    "StrategyRiskConfigResponse": "StrategyRiskConfig",
    "StrategyRoiTargetResponse": "StrategyRoiTarget",
    "StrategyRuleSourceResponse": "StrategyRuleSource",
    "StrategyStateBranchResponse": "StrategyStateBranch",
    "StrategyTemplateConfigResponse": "StrategyTemplateConfig",
    "StrategyTrailingConfigResponse": "StrategyTrailingConfig",
    "FactorCatalogItemResponse": "FactorCatalogItem",
    "FactorResearchSummaryResponse": "FactorResearchSummary",
    "FactorForwardMetricResponse": "FactorForwardMetric",
    "FactorScorecardResponse": "FactorScorecard",
    "FactorSampleRangeResponse": "FactorSampleRange",
    "FactorLagPointResponse": "FactorLagPoint",
    "FactorRollingPointResponse": "FactorRollingPoint",
    "FactorQuantileBucketResponse": "FactorQuantileBucket",
    "FactorNormalizedPointResponse": "FactorNormalizedPoint",
    "FactorDetailResponse": "FactorDetail",
    "FactorBlendComponentResponse": "FactorBlendComponent",
    "FactorDroppedComponentResponse": "FactorDroppedComponent",
    "FactorBlendResponse": "FactorBlend",
}

FILE_MODELS: dict[str, list[dict[str, Any]]] = {
    "backtest.ts": [
        {"name": "BacktestStartRequest", "model": BacktestStartRequest},
        {"name": "BacktestStartResponse", "model": BacktestStartResponse},
        {"name": "PaperStartRequest", "model": PaperStartRequest},
        {"name": "PaperStartResponse", "model": PaperStartResponse},
        {"name": "PaperStopResponse", "model": PaperStopResponse},
        {"name": "BacktestMetrics", "model": BacktestMetricsResponse},
        {"name": "BacktestSignal", "model": BacktestSignalResponse},
        {"name": "BacktestTrade", "model": BacktestTradeResponse},
        {"name": "BacktestEquityPoint", "model": BacktestEquityPointResponse},
        {"name": "BacktestPagination", "model": PaginationResponse},
        {"name": "BacktestRun", "model": BacktestRunResponse},
        {"name": "BacktestDetailResponse", "model": BacktestDetailResponse},
        {"name": "BacktestRunMetadata", "model": BacktestRunMetadataResponse},
        {"name": "BacktestReport", "model": BacktestReportResponse},
        {"name": "BacktestReportSnapshot", "model": BacktestReportSnapshotResponse},
        {"name": "BacktestDateRange", "model": BacktestDateRangeResponse},
        {"name": "BacktestPairBreakdown", "model": BacktestPairBreakdownResponse},
        {"name": "BacktestStrategySummary", "model": BacktestStrategySummaryResponse},
        {"name": "BacktestPortfolioSummary", "model": BacktestPortfolioSummaryResponse},
        {"name": "BacktestPortfolioPayload", "model": BacktestPortfolioPayloadResponse},
        {"name": "BacktestResearchPayload", "model": BacktestResearchPayloadResponse},
        {"name": "BacktestOptimizationTrial", "model": BacktestOptimizationTrialResponse},
        {"name": "BacktestOptimizationSummary", "model": BacktestOptimizationSummaryResponse},
        {"name": "BacktestIterationSummary", "model": BacktestIterationSummaryResponse},
        {"name": "BacktestRollingWindow", "model": BacktestRollingWindowResponse},
        {"name": "BacktestResearchReport", "model": BacktestResearchReportResponse},
        {"name": "BacktestSampleRanges", "model": BacktestSampleRangesResponse},
        {"name": "BacktestPaperPosition", "model": BacktestPaperPositionResponse},
        {"name": "BacktestRuntimeState", "model": BacktestRuntimeStateResponse},
        {"name": "BacktestPaperLive", "model": BacktestPaperLiveResponse},
        {"name": "BacktestPortfolioConfig", "model": BacktestPortfolioRequest},
        {"name": "BacktestResearchConfig", "model": BacktestResearchRequest},
        {"name": "StrategyVersion", "model": StrategyVersionResponse},
        {"name": "StrategyDefinition", "model": StrategyDefinitionResponse},
        {"name": "StrategyIndicatorRegistryItem", "model": StrategyIndicatorRegistryResponse},
        {"name": "StrategyOperator", "model": StrategyOperatorResponse},
        {"name": "StrategyGroupLogic", "model": StrategyGroupLogicResponse},
        {"name": "StrategyIndicatorEngine", "model": StrategyIndicatorEngineResponse},
        {"name": "StrategyTemplate", "model": StrategyTemplateResponse},
        {"name": "StrategyEditorContract", "model": StrategyEditorContractResponse},
        {"name": "StrategyVersionCreateRequest", "model": StrategyVersionCreateRequest},
        {"name": "IndicatorDefinitionCreateRequest", "model": IndicatorDefinitionCreateRequest},
        {"name": "StrategyTemplateCreateRequest", "model": StrategyTemplateCreateRequest},
        {"name": "StrategyRuleSource", "model": StrategyRuleSourceResponse},
        {"name": "StrategyStateBranch", "model": StrategyStateBranchResponse},
        {"name": "StrategyIndicatorConfig", "model": StrategyIndicatorConfigResponse},
        {"name": "StrategyExecutionConfig", "model": StrategyExecutionConfigResponse},
        {"name": "StrategyRoiTarget", "model": StrategyRoiTargetResponse},
        {"name": "StrategyPartialExit", "model": StrategyPartialExitResponse},
        {"name": "StrategyTrailingConfig", "model": StrategyTrailingConfigResponse},
        {"name": "StrategyRiskConfig", "model": StrategyRiskConfigResponse},
        {"name": "StrategyTemplateConfig", "model": StrategyTemplateConfigResponse},
    ],
    "factor.ts": [
        {"name": "FactorCatalogItem", "model": FactorCatalogItemResponse},
        {"name": "FactorCatalogResponse", "model": FactorCatalogResponse},
        {"name": "FactorResearchRequest", "model": FactorResearchRequest},
        {"name": "FactorForwardMetric", "model": FactorForwardMetricResponse},
        {"name": "FactorResearchSummary", "model": FactorResearchSummaryResponse},
        {"name": "FactorScorecard", "model": FactorScorecardResponse},
        {"name": "FactorLagPoint", "model": FactorLagPointResponse},
        {"name": "FactorRollingPoint", "model": FactorRollingPointResponse},
        {"name": "FactorQuantileBucket", "model": FactorQuantileBucketResponse},
        {"name": "FactorNormalizedPoint", "model": FactorNormalizedPointResponse},
        {"name": "FactorDetail", "model": FactorDetailResponse},
        {"name": "FactorBlendComponent", "model": FactorBlendComponentResponse},
        {"name": "FactorDroppedComponent", "model": FactorDroppedComponentResponse},
        {"name": "FactorBlend", "model": FactorBlendResponse},
        {"name": "FactorResearchResponse", "model": FactorResearchResponse},
        {"name": "FactorResearchRun", "model": FactorResearchRunDetailResponse, "optional_fields": {"details"}},
        {"name": "FactorExecutionRequest", "model": FactorExecutionRequest},
        {"name": "FactorExecutionResponse", "model": FactorExecutionResponse},
    ],
}

FILE_EXTRAS = {
    "backtest.ts": [
        "export interface StrategyConditionNode {",
        "  id: string",
        "  node_type?: 'condition'",
        "  label: string",
        "  left: StrategyRuleSource",
        "  operator: 'gt' | 'gte' | 'lt' | 'lte'",
        "  right: StrategyRuleSource",
        "  enabled?: boolean",
        "}",
        "",
        "export interface StrategyGroupNode {",
        "  id: string",
        "  node_type?: 'group'",
        "  label: string",
        "  logic: 'and' | 'or'",
        "  enabled?: boolean",
        "  children?: Array<StrategyRuleNode>",
        "}",
        "",
        "export type StrategyRuleNode = StrategyConditionNode | StrategyGroupNode",
    ],
    "factor.ts": [],
}

SKIP_DEFINITIONS = {"StrategyConditionNode", "StrategyGroupNode", "StrategyRuleNode", *ALIAS_MAP.keys()}


def main() -> None:
    for filename, entries in FILE_MODELS.items():
        content = render_file(entries, FILE_EXTRAS[filename])
        (FRONTEND_TYPES_DIR / filename).write_text(content, encoding="utf-8")


def render_file(entries: list[dict[str, Any]], extra_lines: list[str]) -> str:
    definitions: dict[str, dict[str, Any]] = {}
    root_names: list[str] = []
    for entry in entries:
        alias = entry["name"]
        model: type[BaseModel] = entry["model"]
        schema = copy.deepcopy(model.model_json_schema(ref_template="#/$defs/{model}"))
        schema = remap_schema(schema)
        if entry.get("optional_fields"):
            required = [item for item in schema.get("required", []) if item not in entry["optional_fields"]]
            if required:
                schema["required"] = required
            elif "required" in schema:
                del schema["required"]
        definitions[alias] = strip_defs(schema)
        root_names.append(alias)
        for def_name, def_schema in schema.get("$defs", {}).items():
            definitions.setdefault(def_name, def_schema)

    lines = [
        "// This file is generated from backend Pydantic schemas.",
        "// Do not edit manually.",
        "",
    ]

    emitted: set[str] = set()
    for name in root_names + sorted(definitions.keys()):
        if name in emitted:
            continue
        if name in SKIP_DEFINITIONS:
            emitted.add(name)
            continue
        lines.extend(emit_named_definition(name, definitions[name]))
        lines.append("")
        emitted.add(name)

    lines.extend(extra_lines)
    lines.append("")
    content = "\n".join(lines)
    for original, alias in ALIAS_MAP.items():
        content = content.replace(original, alias)
    return content


def remap_schema(value: Any) -> Any:
    if isinstance(value, dict):
        remapped: dict[str, Any] = {}
        for key, item in value.items():
            if key == "$defs":
                nested_defs: dict[str, Any] = {}
                for def_name, def_schema in item.items():
                    nested_defs[canonical_name(def_name)] = remap_schema(def_schema)
                remapped[key] = nested_defs
                continue
            if key == "$ref" and isinstance(item, str):
                remapped[key] = f"#/$defs/{canonical_name(item.split('/')[-1])}"
                continue
            remapped[key] = remap_schema(item)
        return remapped
    if isinstance(value, list):
        return [remap_schema(item) for item in value]
    return value


def canonical_name(name: str) -> str:
    return ALIAS_MAP.get(name, name)


def strip_defs(schema: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(schema)
    result.pop("$defs", None)
    result.pop("title", None)
    return result


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
