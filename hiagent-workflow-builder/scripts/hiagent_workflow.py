"""Build HiAgent workflow YAML from a constrained JSON specification.

The generated wrapper follows the company-tested HiAgent ChatFlow export shape.
Only node contracts implemented in this file are allowed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import sys
import time
from typing import Any


SCHEMA_PROFILE = "hiagent-company-v2"
FILE_SUBPARAMETERS = [
    {"Desc": "文件名", "Name": "name", "Required": True, "Type": 0},
    {"Desc": "平台附件链接", "Name": "url", "Required": True, "Type": 0},
]


class WorkflowError(ValueError):
    """Raised when a specification cannot be rendered safely."""


_SENSITIVE_KEYS = {
    "api_key", "api_token", "password", "secret", "token",
    "access_token", "refresh_token",
}
_CREDENTIAL_PATTERNS = [
    re.compile(r"authorization\s*:\s*bearer\s+\S{16,}", re.IGNORECASE),
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"\b(?:api[_ -]?key|password|token)\s*[:=]\s*\S{12,}", re.IGNORECASE),
]


def _find_sensitive_key(value: Any, path: str = "") -> str | None:
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key).lower()
            child_path = f"{path}.{key}" if path else str(key)
            if key_text in _SENSITIVE_KEYS:
                return child_path
            found = _find_sensitive_key(child, child_path)
            if found:
                return found
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found = _find_sensitive_key(child, f"{path}[{index}]")
            if found:
                return found
    return None


def _find_credential_value(value: Any, path: str = "") -> str | None:
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            found = _find_credential_value(child, child_path)
            if found:
                return found
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found = _find_credential_value(child, f"{path}[{index}]")
            if found:
                return found
    elif isinstance(value, str):
        if any(pattern.search(value) for pattern in _CREDENTIAL_PATTERNS):
            return path
    return None


def _required_text(container: dict[str, Any], key: str, label: str) -> str:
    value = str(container.get(key, "")).strip()
    if not value:
        raise WorkflowError(f"{label}不能为空")
    if (value.startswith("__") and value.endswith("__")) or value.upper() in {"REPLACE_ME", "TODO"}:
        raise WorkflowError(f"{label}仍是占位符")
    return value


def validate_spec(spec: dict[str, Any], profile: dict[str, Any]) -> None:
    """Fail closed unless the input uses the verified V1 contracts."""
    sensitive = _find_sensitive_key(spec)
    if sensitive:
        raise WorkflowError(f"规格包含敏感字段：{sensitive}")
    sensitive = _find_sensitive_key(profile)
    if sensitive:
        raise WorkflowError(f"环境配置包含敏感字段：{sensitive}")
    credential = _find_credential_value(spec)
    if credential:
        raise WorkflowError(f"规格包含疑似凭证内容：{credential}")
    credential = _find_credential_value(profile)
    if credential:
        raise WorkflowError(f"环境配置包含疑似凭证内容：{credential}")

    if spec.get("spec_version") != "1.0":
        raise WorkflowError("spec_version 必须是 1.0")
    if profile.get("profile_version") != "1.0":
        raise WorkflowError("profile_version 必须是 1.0")
    if profile.get("schema_profile") != SCHEMA_PROFILE:
        raise WorkflowError(f"schema_profile 必须是 {SCHEMA_PROFILE}")

    _required_text(spec, "workflow_key", "workflow_key")
    _required_text(spec, "name", "工作流名称")
    _required_text(profile, "workspace_id", "workspace_id")
    model = profile.get("model")
    if not isinstance(model, dict):
        raise WorkflowError("环境配置缺少 model")
    _required_text(model, "id", "model.id")
    _required_text(model, "name", "model.name")

    inputs = spec.get("inputs")
    if not isinstance(inputs, list) or not inputs:
        raise WorkflowError("inputs 至少需要一个输入字段")
    known_outputs: dict[str, set[str]] = {"start": set()}
    for field in inputs:
        if not isinstance(field, dict):
            raise WorkflowError("输入字段必须是对象")
        name = _required_text(field, "name", "输入字段名称")
        if name in known_outputs["start"]:
            raise WorkflowError(f"输入字段名称重复：{name}")
        field_type = field.get("type", "string")
        if field_type not in {"string", "file_list"}:
            raise WorkflowError(f"不支持的输入类型：{field_type}")
        known_outputs["start"].add(name)

    steps = spec.get("steps")
    if not isinstance(steps, list) or not steps:
        raise WorkflowError("steps 至少需要一个处理节点")
    for step in steps:
        if not isinstance(step, dict):
            raise WorkflowError("步骤必须是对象")
        step_id = _required_text(step, "id", "步骤 id")
        if step_id == "start" or step_id in known_outputs:
            raise WorkflowError(f"步骤 id 重复：{step_id}")
        step_type = step.get("type")
        if step_type not in {"code", "llm"}:
            raise WorkflowError(f"不支持的节点类型：{step_type}")
        _required_text(step, "name", f"步骤 {step_id} 的名称")
        bindings = step.get("inputs", {})
        if not isinstance(bindings, dict):
            raise WorkflowError(f"步骤 {step_id} 的 inputs 必须是对象")
        for local_name, reference in bindings.items():
            if not isinstance(reference, str) or "." not in reference:
                raise WorkflowError(f"无效的输入引用：{reference}")
            source, path = reference.split(".", 1)
            if source not in known_outputs or path not in known_outputs[source]:
                raise WorkflowError(f"不存在的输入引用：{reference}")
            if not str(local_name).strip():
                raise WorkflowError(f"步骤 {step_id} 存在空的输入变量名")
        if step_type == "llm":
            _required_text(step, "system_prompt", f"步骤 {step_id} 的 system_prompt")
            prompt = _required_text(step, "prompt", f"步骤 {step_id} 的 prompt")
            placeholders = set(re.findall(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}", prompt))
            unbound = sorted(placeholders.difference(bindings))
            if unbound:
                raise WorkflowError("提示词变量未绑定：" + "、".join(unbound))
            max_tokens = step.get("max_tokens", 1024)
            if isinstance(max_tokens, bool):
                raise WorkflowError(f"步骤 {step_id} 的 max_tokens 必须是整数")
            try:
                max_tokens_value = int(max_tokens)
            except (TypeError, ValueError) as exc:
                raise WorkflowError(f"步骤 {step_id} 的 max_tokens 必须是整数") from exc
            if not 1 <= max_tokens_value <= 20000:
                raise WorkflowError(f"步骤 {step_id} 的 max_tokens 必须在 1 到 20000 之间")
            for parameter, default in (("temperature", 0.1), ("top_p", 0.9)):
                value = step.get(parameter, default)
                if isinstance(value, bool):
                    raise WorkflowError(f"步骤 {step_id} 的 {parameter} 必须是数值")
                try:
                    numeric = float(value)
                except (TypeError, ValueError) as exc:
                    raise WorkflowError(f"步骤 {step_id} 的 {parameter} 必须是数值") from exc
                if not 0 <= numeric <= 1:
                    raise WorkflowError(f"步骤 {step_id} 的 {parameter} 必须在 0 到 1 之间")
            known_outputs[step_id] = {"raw_output"}
        else:
            _required_text(step, "code", f"步骤 {step_id} 的 code")
            outputs = step.get("outputs")
            if not isinstance(outputs, list) or not outputs:
                raise WorkflowError(f"步骤 {step_id} 至少需要一个输出字段")
            normalized = {str(item).strip() for item in outputs}
            if "" in normalized or len(normalized) != len(outputs):
                raise WorkflowError(f"步骤 {step_id} 的输出字段为空或重复")
            known_outputs[step_id] = normalized

    outputs = spec.get("outputs")
    if not isinstance(outputs, dict) or not outputs:
        raise WorkflowError("outputs 至少需要一个 End 输出")
    for output_name, reference in outputs.items():
        if not str(output_name).strip():
            raise WorkflowError("End 输出名称不能为空")
        if not isinstance(reference, str) or "." not in reference:
            raise WorkflowError(f"无效的输出引用：{reference}")
        source, path = reference.split(".", 1)
        if source not in known_outputs or path not in known_outputs[source]:
            raise WorkflowError(f"不存在的输出引用：{reference}")


def _stable_id(workflow_key: str, role: str) -> str:
    value = f"hiagent-workflow-builder-v1:{workflow_key}:{role}"
    return hashlib.sha1(value.encode("utf-8")).hexdigest()[:20]


def _variable(name: str, node_code: str, path: str) -> dict[str, Any]:
    return {"Name": name, "NodeCode": node_code, "Path": path, "RefType": "node_field"}


def _chat_advanced() -> dict[str, Any]:
    return {
        "AdvancedReviewType": "unused",
        "FeedbackTagConfig": {
            "DislikeTags": ["没有帮助", "知识过时", "问题理解错误", "回答不准确"],
            "Enabled": True, "LikeTags": None,
        },
        "OpeningConfig": {"OpeningEnabled": False, "OpeningQuestions": [], "OpeningText": ""},
        "ReferenceEnabled": False, "ReviewEnabled": False,
        "SpeechInteractionConfig": {}, "SuggestEnabled": False,
        "ThoughtLanguageConfig": {"Language": "zh"},
        "UploadConfig": {
            "Enabled": True, "UploadAudioAllowed": True, "UploadCompressedAllowed": False,
            "UploadDocumentAllowed": True, "UploadImageAllowed": True,
            "UploadOtherAllowed": False, "UploadVideoAllowed": True,
        },
    }


def build_workflow(spec: dict[str, Any], profile: dict[str, Any], *, timestamp_ms: int) -> dict[str, Any]:
    """Return a native-shape HiAgent workflow dictionary."""
    validate_spec(spec, profile)

    workflow_key = str(spec["workflow_key"])
    workspace_id = str(profile["workspace_id"])
    model = profile["model"]
    model_id = str(model["id"])
    model_name = str(model["name"])

    app_id = _stable_id(workflow_key, "app")
    flow_id = _stable_id(workflow_key, "flow")
    publish_id = _stable_id(workflow_key, "publish")
    detail_version = _stable_id(workflow_key, "detail-version")
    outer_version = _stable_id(workflow_key, "outer-version")
    start_id = _stable_id(workflow_key, "start")

    start_fields = []
    for field in spec["inputs"]:
        field_type = field.get("type", "string")
        native_field = {
            "Desc": field.get("description", ""),
            "Name": field["name"],
            "Required": bool(field.get("required", False)),
            "Type": 11 if field_type == "file_list" else 0,
        }
        if field_type == "file_list":
            native_field["SubParameters"] = FILE_SUBPARAMETERS
        start_fields.append(native_field)
    nodes: list[dict[str, Any]] = [{
        "Code": start_id, "ID": start_id, "Name": "Start", "Type": "Start",
        "Layout": {"X": -500, "Y": 0},
        "Configs": {"Start": {"InputSchema": start_fields, "OutputSchema": start_fields}},
    }]
    logical_ids = {"start": start_id}

    for index, step in enumerate(spec["steps"]):
        if step["type"] not in {"code", "llm"}:
            raise WorkflowError(f"不支持的节点类型：{step['type']}")
        node_id = _stable_id(workflow_key, f"step:{step['id']}")
        logical_ids[step["id"]] = node_id
        inputs = []
        dependencies = []
        for local_name, reference in step.get("inputs", {}).items():
            source, path = reference.split(".", 1)
            source_id = logical_ids[source]
            inputs.append(_variable(local_name, source_id, path))
            if source_id not in dependencies:
                dependencies.append(source_id)
        common = {
            "Code": node_id, "ID": node_id, "Name": step["name"],
            "Type": "LLM" if step["type"] == "llm" else "Code",
            "Layout": {"X": -100 + index * 400, "Y": 0},
            "Depends": [{"NodeCode": item} for item in dependencies],
            "ErrorConfig": {"ErrorConfigType": "None"},
        }
        if step["type"] == "llm":
            common["Configs"] = {"LLM": {
                "CurrentTimeEnabled": False, "EnableChatHistories": False,
                "InputVariables": inputs,
                "MaxTokens": int(step.get("max_tokens", 1024)),
                "ModelFeatureList": ["streaming"],
                "ModelID": model_id, "ModelInteractiveMode": None,
                "ModelName": model_name,
                "ModelParameters": '{"context_tokens":30000,"max_tokens":{"Max":20000,"Min":1,"Default":1024},"temperature":{"default":0.1,"max":1,"min":0},"top_p":{"default":0.9,"max":1,"min":0}}',
                "OutputFormat": "text",
                "OutputSchema": [{"Name": "raw_output", "Type": 0}],
                "Prompt": step["prompt"], "PromptConfig": None,
                "ReasoningEffortType": None, "ReasoningMode": None,
                "ReasoningSwitch": None, "ReasoningSwitchType": None,
                "Retries": 0, "SystemPrompt": step["system_prompt"],
                "SystemPromptConfig": None,
                "Temperature": float(step.get("temperature", 0.1)),
                "TimeoutSeconds": 60, "TopP": float(step.get("top_p", 0.9)),
            }}
        else:
            common["Configs"] = {"Code": {
                "Code": step["code"], "InputVariables": inputs, "Language": 1,
                "OutputSchema": [{"Name": output_name, "Type": 0} for output_name in step["outputs"]],
                "Retries": 0, "TimeoutSeconds": 60,
            }}
        nodes.append(common)

    end_id = _stable_id(workflow_key, "end")
    end_inputs = []
    end_dependencies = []
    for output_name, reference in spec["outputs"].items():
        source, path = reference.split(".", 1)
        source_id = logical_ids[source]
        end_inputs.append(_variable(output_name, source_id, path))
        if source_id not in end_dependencies:
            end_dependencies.append(source_id)
    nodes.append({
        "Code": end_id, "ID": end_id, "Name": "End", "Type": "End",
        "Layout": {"X": -100 + len(spec["steps"]) * 400, "Y": 0},
        "Depends": [{"NodeCode": item} for item in end_dependencies],
        "Configs": {"End": {
            "InputVariables": end_inputs,
            "OutputSchema": [{"Name": output_name, "Type": 0} for output_name in spec["outputs"]],
            "OutputType": "Variable",
        }},
    })

    model_entry = {"Desc": "", "ID": model_id, "LogoPath": "", "Name": model_name}
    depends = {
        "AppMap": {}, "DataSourceMap": {}, "DatabaseMap": {}, "KnowledgeMap": {},
        "ModelMap": {model_id: model_entry}, "PluginMap": {}, "QADataSetMap": {},
        "TermDatasetMap": {}, "ToolMap": {}, "WorkflowMap": {},
    }
    advanced = _chat_advanced()
    display_name = str(spec["name"])
    description = str(spec.get("description", ""))
    return {
        "AppConfig": {
            "AgentMode": "", "AppID": app_id,
            "ChatFlowDetail": {
                "DLVersion": "v2", "Depends": depends, "Desc": description,
                "DisplayName": app_id, "FlowType": "Agent", "ID": flow_id,
                "LogoPath": "", "MetaType": "Workflow", "Nodes": nodes,
                "UniqueName": flow_id, "UpdatedAt": timestamp_ms,
                "VersionCode": detail_version, "VersionName": detail_version,
            },
            "MultiAgentConfig": None,
            "SingleAgentConfig": {
                "A2aAgentIDs": [], "AgentIDs": [],
                "ChatAdvancedConfig": advanced,
                "ChatFlowConfig": {
                    "ChatAdvancedConfig": advanced, "RoundsReserved": 3,
                    "Version": "v1", "WorkflowID": flow_id, "WorkflowPublishID": publish_id,
                },
                "DatabaseIDs": [], "GraphIDs": [], "KnowledgeIDs": [],
                "ModelID": "", "ModelName": "", "PrePrompt": "",
                "PromptConfig": {"PromptMode": "regex"},
                "QADatasetIDs": [], "SummaryModelID": "", "SummaryModelName": "",
                "TerminologyIDs": [], "ToolIDs": [],
                "UpdateTime": "2026-09-01 00:00:00", "VariableConfigs": [],
                "Version": "v1", "VersionDescription": "", "WorkflowIDs": [],
            },
            "WorkspaceID": workspace_id,
        },
        "AppDepends": {**depends, "ModelMap": {model_id: {**model_entry, "SourceTypes": ["Agent"]}}},
        "AppInfo": {"AgentMode": "", "AppID": app_id, "AppType": "ChatFlow", "WorkspaceID": workspace_id},
        "DLVersion": "0.0.1", "Desc": description, "DisplayName": display_name,
        "LogoPath": "", "MetaType": "Agent", "UniqueName": app_id,
        "UpdatedAt": timestamp_ms, "VersionCode": outer_version, "VersionName": "v1",
    }


def _yaml_key(value: Any) -> str:
    text = str(value)
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]*", text):
        return text
    return json.dumps(text, ensure_ascii=False)


def _yaml_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    raise TypeError(f"不支持的 YAML 值类型：{type(value).__name__}")


def dump_yaml(value: Any) -> str:
    """Serialize JSON-compatible data to dependency-free YAML 1.2."""
    lines: list[str] = []

    def emit(item: Any, indent: int) -> None:
        prefix = " " * indent
        if isinstance(item, dict):
            if not item:
                lines.append(prefix + "{}")
                return
            for key, child in item.items():
                key_text = _yaml_key(key)
                if isinstance(child, (dict, list)) and child:
                    lines.append(f"{prefix}{key_text}:")
                    emit(child, indent + 2)
                elif isinstance(child, dict):
                    lines.append(f"{prefix}{key_text}: {{}}")
                elif isinstance(child, list):
                    lines.append(f"{prefix}{key_text}: []")
                else:
                    lines.append(f"{prefix}{key_text}: {_yaml_scalar(child)}")
            return
        if isinstance(item, list):
            if not item:
                lines.append(prefix + "[]")
                return
            for child in item:
                if isinstance(child, (dict, list)) and child:
                    lines.append(prefix + "-")
                    emit(child, indent + 2)
                elif isinstance(child, dict):
                    lines.append(prefix + "- {}")
                elif isinstance(child, list):
                    lines.append(prefix + "- []")
                else:
                    lines.append(prefix + "- " + _yaml_scalar(child))
            return
        lines.append(prefix + _yaml_scalar(item))

    emit(value, 0)
    return "\n".join(lines) + "\n"


def validate_workflow_dict(workflow: dict[str, Any]) -> list[dict[str, Any]]:
    """Return observable preflight checks for the rendered workflow."""
    checks: list[dict[str, Any]] = []

    def add(name: str, passed: bool, detail: str) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    expected_top = {
        "AppConfig", "AppDepends", "AppInfo", "DLVersion", "Desc",
        "DisplayName", "LogoPath", "MetaType", "UniqueName", "UpdatedAt",
        "VersionCode", "VersionName",
    }
    add("native_wrapper",
        set(workflow) == expected_top
        and workflow.get("DLVersion") == "0.0.1"
        and workflow.get("MetaType") == "Agent",
        "顶层字段、DLVersion 和 MetaType 必须匹配已验证导出结构")

    try:
        detail = workflow["AppConfig"]["ChatFlowDetail"]
        nodes = detail["Nodes"]
    except (KeyError, TypeError):
        add("workflow_detail", False, "缺少 AppConfig.ChatFlowDetail.Nodes")
        return checks

    add("workflow_detail",
        detail.get("DLVersion") == "v2"
        and detail.get("MetaType") == "Workflow"
        and detail.get("FlowType") == "Agent",
        "工作流详情必须使用 v2 / Workflow / Agent")

    node_ids = [node.get("ID") for node in nodes]
    add("node_ids",
        len(node_ids) == len(set(node_ids))
        and all(node.get("Code") == node.get("ID") for node in nodes),
        "节点 ID 必须唯一且 Code 与 ID 一致")
    add("start_end_count",
        sum(node.get("Type") == "Start" for node in nodes) == 1
        and sum(node.get("Type") == "End" for node in nodes) == 1,
        "必须且只能有一个 Start 和一个 End")
    add("verified_node_types",
        all(node.get("Type") in {"Start", "Code", "LLM", "End"} for node in nodes),
        "仅允许 Start、Code、LLM、End")

    available: dict[str, set[str]] = {}
    for node in nodes:
        node_id = node.get("ID")
        node_type = node.get("Type")
        config = node.get("Configs", {}).get(node_type, {})
        available[node_id] = {
            item.get("Name") for item in config.get("OutputSchema", []) if item.get("Name")
        }
    references_ok = True
    for node in nodes:
        for dependency in node.get("Depends", []):
            if dependency.get("NodeCode") not in available:
                references_ok = False
        for config in node.get("Configs", {}).values():
            for variable in config.get("InputVariables", []):
                source = variable.get("NodeCode")
                path = variable.get("Path")
                if source not in available or path not in available[source]:
                    references_ok = False
    add("references_resolve", references_ok, "所有依赖和变量引用必须指向已存在节点输出")

    ends = [node for node in nodes if node.get("Type") == "End"]
    end_ok = False
    if len(ends) == 1:
        end_config = ends[0].get("Configs", {}).get("End", {})
        variables = end_config.get("InputVariables", [])
        schema_names = {item.get("Name") for item in end_config.get("OutputSchema", [])}
        end_ok = (
            end_config.get("OutputType") == "Variable"
            and bool(variables)
            and {item.get("Name") for item in variables} == schema_names
        )
    add("end_outputs_nonempty", end_ok, "End 必须使用 Variable 输出，且变量映射与输出字段一致并非空")

    llm_nodes = [node for node in nodes if node.get("Type") == "LLM"]
    model_map = detail.get("Depends", {}).get("ModelMap", {})
    model_ok = all(
        node.get("Configs", {}).get("LLM", {}).get("ModelID") in model_map
        for node in llm_nodes
    )
    add("model_bindings", model_ok, "每个 LLM 节点的 ModelID 必须存在于依赖映射")
    return checks


def _safe_filename(name: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*]', "_", name).strip().rstrip(".")
    return cleaned or "hiagent-workflow"


def generate_artifacts(spec_path: pathlib.Path, profile_path: pathlib.Path, output_dir: pathlib.Path, *, timestamp_ms: int) -> tuple[pathlib.Path, pathlib.Path]:
    spec = json.loads(spec_path.read_text(encoding="utf-8-sig"))
    profile = json.loads(profile_path.read_text(encoding="utf-8-sig"))
    workflow = build_workflow(spec, profile, timestamp_ms=timestamp_ms)
    checks = validate_workflow_dict(workflow)
    failed = [item for item in checks if not item["passed"]]
    if failed:
        raise WorkflowError("生成后校验失败：" + "；".join(item["name"] for item in failed))

    yaml_text = dump_yaml(workflow)
    output_dir.mkdir(parents=True, exist_ok=True)
    base_name = _safe_filename(str(spec["name"]))
    yaml_path = output_dir / f"{base_name}.yaml"
    report_path = output_dir / f"{base_name}.validation.json"
    yaml_path.write_text(yaml_text, encoding="utf-8", newline="\n")
    digest = hashlib.sha256(yaml_path.read_bytes()).hexdigest()
    report = {
        "generator": "hiagent-workflow-builder",
        "generator_version": "1.0.0",
        "schema_profile": SCHEMA_PROFILE,
        "status": "pass",
        "workflow_name": spec["name"],
        "workflow_key": spec["workflow_key"],
        "yaml_file": yaml_path.name,
        "yaml_sha256": digest,
        "checks": checks,
        "remaining_gate": "必须在目标公司 HiAgent 环境完成实际导入与至少一条运行验收",
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return yaml_path, report_path


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="生成公司 HiAgent 原生工作流 YAML")
    subparsers = parser.add_subparsers(dest="command", required=True)
    generate = subparsers.add_parser("generate", help="从 JSON 规格生成并校验 YAML")
    generate.add_argument("--spec", required=True, type=pathlib.Path)
    generate.add_argument("--profile", required=True, type=pathlib.Path)
    generate.add_argument("--output-dir", required=True, type=pathlib.Path)
    generate.add_argument("--timestamp-ms", type=int, default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        timestamp_ms = args.timestamp_ms or int(time.time() * 1000)
        yaml_path, report_path = generate_artifacts(args.spec, args.profile, args.output_dir, timestamp_ms=timestamp_ms)
    except (OSError, json.JSONDecodeError, KeyError, TypeError, WorkflowError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(f"YAML: {yaml_path}")
    print(f"REPORT: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
