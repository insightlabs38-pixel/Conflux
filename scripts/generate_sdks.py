"""Generate the checked TypeScript and Python SDK surface from OpenAPI."""

import argparse
import json
import pprint
import re
import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "docs/api/openapi.yaml"
TS_OUTPUT = ROOT / "sdks/typescript/generated.ts"
PY_OUTPUT = ROOT / "sdks/python/conflux_sdk/generated.py"
METHODS = {"get", "post", "put", "patch", "delete"}


def ref_name(schema):
    ref = schema["$ref"]
    prefix = "#/components/schemas/"
    if not ref.startswith(prefix):
        raise ValueError(f"Unsupported reference: {ref}")
    return ref[len(prefix) :]


def normalize(schema):
    if "allOf" in schema:
        parts = schema["allOf"]
        if len(parts) != 1:
            raise ValueError(f"Unsupported allOf: {parts}")
        return {**parts[0], "nullable": schema.get("nullable", False)}
    if any(key in schema for key in ("oneOf", "anyOf")):
        raise ValueError(f"Unsupported union schema: {schema}")
    return schema


def ts_type(raw, *, input_mode=False):
    schema = normalize(raw)
    if not schema or set(schema) <= {"nullable", "readOnly", "writeOnly", "description", "default"}:
        return "unknown"
    if "$ref" in schema:
        value = ("InputOf" if input_mode else "") + ref_name(schema)
    elif "enum" in schema:
        value = " | ".join(json.dumps(item) for item in schema["enum"])
    elif schema.get("type") == "array":
        value = f"({ts_type(schema['items'], input_mode=input_mode)})[]"
    elif schema.get("type") == "object" or "properties" in schema:
        props = schema.get("properties", {})
        if props:
            required = set(schema.get("required", []))
            fields = []
            for key, part in props.items():
                if input_mode and part.get("readOnly"):
                    continue
                optional = "" if key in required else "?"
                fields.append(
                    f"{json.dumps(key)}{optional}: {ts_type(part, input_mode=input_mode)};"
                )
            value = "{ " + " ".join(fields) + " }"
        elif "additionalProperties" in schema:
            part = schema["additionalProperties"]
            value = (
                f"Record<string, {ts_type(part, input_mode=input_mode)}>"
                if isinstance(part, dict)
                else "Record<string, unknown>"
            )
        else:
            value = "Record<string, unknown>"
    elif schema.get("type") in ("integer", "number"):
        value = "number"
    elif schema.get("type") == "boolean":
        value = "boolean"
    elif schema.get("type") == "string":
        value = "string"
    else:
        raise ValueError(f"Unsupported TypeScript schema: {schema}")
    return f"({value} | null)" if schema.get("nullable") else value


def py_type(raw, *, input_mode=False):
    schema = normalize(raw)
    if not schema or set(schema) <= {"nullable", "readOnly", "writeOnly", "description", "default"}:
        return "Any"
    if "$ref" in schema:
        value = ("InputOf" if input_mode else "") + ref_name(schema)
    elif "enum" in schema:
        value = "Literal[" + ", ".join(repr(item) for item in schema["enum"]) + "]"
    elif schema.get("type") == "array":
        value = f"list[{py_type(schema['items'], input_mode=input_mode)}]"
    elif schema.get("type") == "object" or "properties" in schema:
        if "additionalProperties" in schema and isinstance(schema["additionalProperties"], dict):
            value = f"dict[str, {py_type(schema['additionalProperties'], input_mode=input_mode)}]"
        else:
            value = "dict[str, Any]"
    elif schema.get("type") == "integer":
        value = "int"
    elif schema.get("type") == "number":
        value = "float"
    elif schema.get("type") == "boolean":
        value = "bool"
    elif schema.get("type") == "string":
        value = "str"
    else:
        raise ValueError(f"Unsupported Python schema: {schema}")
    return f"{value} | None" if schema.get("nullable") else value


def operation_response(operation):
    responses = operation.get("responses", {})
    success = [(code, item) for code, item in responses.items() if code.startswith("2")]
    if not success:
        return "never", "none"
    schemas = []
    media_kind = "none"
    for _, item in success:
        content = item.get("content", {})
        if "application/json" in content:
            schemas.append(ts_type(content["application/json"]["schema"]))
            media_kind = "json"
        elif content:
            schemas.append("string")
            media_kind = "text"
        else:
            schemas.append("null")
    return " | ".join(dict.fromkeys(schemas)), media_kind


def generate(schema):
    names = set(schema["components"]["schemas"])
    if any("InputOf" + name in names for name in names):
        raise ValueError("Input type name collides with an OpenAPI schema")
    ts_lines = ["// Generated from docs/api/openapi.yaml. Run scripts/generate_sdks.py.", ""]
    py_lines = [
        '"""Generated from docs/api/openapi.yaml. Run scripts/generate_sdks.py."""',
        "",
        "from __future__ import annotations",
        "",
        "from typing import Any, Literal, NotRequired, TypedDict",
        "",
    ]
    for name, definition in schema["components"]["schemas"].items():
        for input_mode in (False, True):
            type_name = ("InputOf" if input_mode else "") + name
            ts_lines += [
                f"export type {type_name} = {ts_type(definition, input_mode=input_mode)};",
                "",
            ]
            props = definition.get("properties")
            if definition.get("type") == "object" and props:
                py_lines.append(f"class {type_name}(TypedDict):")
                required = set(definition.get("required", []))
                included = [
                    (key, part)
                    for key, part in props.items()
                    if not input_mode or not part.get("readOnly")
                ]
                if not included:
                    py_lines.append("    pass")
                for key, part in included:
                    if not key.isidentifier():
                        raise ValueError(f"Unsupported Python property name: {key}")
                    annotation = py_type(part, input_mode=input_mode)
                    if key not in required:
                        annotation = f"NotRequired[{annotation}]"
                    py_lines.append(f"    {key}: {annotation}")
                py_lines.append("")
            else:
                py_lines += [f"{type_name} = {py_type(definition, input_mode=input_mode)}", ""]

    metadata = {}
    ts_lines += ["export interface Operations {"]
    for path, path_item in schema["paths"].items():
        for method, operation in path_item.items():
            if method not in METHODS:
                continue
            operation_id = operation["operationId"]
            if operation_id in metadata:
                raise ValueError(f"Duplicate operation ID: {operation_id}")
            parameters = operation.get("parameters", [])
            path_params = [item for item in parameters if item["in"] == "path"]
            query_params = [item for item in parameters if item["in"] == "query"]
            unsupported = [item for item in parameters if item["in"] not in ("path", "query")]
            if unsupported:
                raise ValueError(f"Unsupported parameters in {operation_id}: {unsupported}")
            if set(re.findall(r"\{([^}]+)\}", path)) != {item["name"] for item in path_params}:
                raise ValueError(f"Path parameters do not match template: {operation_id}")
            request_parts = []
            if path_params:
                fields = " ".join(
                    f"{json.dumps(item['name'])}: {ts_type(item['schema'])};"
                    for item in path_params
                )
                request_parts.append(f"path: {{ {fields} }};")
            if query_params:
                query_fields = []
                for item in query_params:
                    optional = "" if item.get("required") else "?"
                    query_fields.append(
                        f"{json.dumps(item['name'])}{optional}: {ts_type(item['schema'])};"
                    )
                fields = " ".join(query_fields)
                request_parts.append(f"query?: {{ {fields} }};")
            request_body = operation.get("requestBody")
            if request_body:
                content = request_body.get("content", {})
                if "application/json" not in content:
                    raise ValueError(f"Unsupported request media in {operation_id}")
                optional = "" if request_body.get("required") else "?"
                body_type = ts_type(content["application/json"]["schema"], input_mode=True)
                request_parts.append(f"body{optional}: {body_type};")
            response_type, response_kind = operation_response(operation)
            request_type = " ".join(request_parts)
            ts_lines.append(
                f"  {json.dumps(operation_id)}: "
                f"{{ request: {{ {request_type} }}; response: {response_type} }};"
            )
            metadata[operation_id] = {
                "method": method.upper(),
                "path": path,
                "path_params": [item["name"] for item in path_params],
                "query_params": [item["name"] for item in query_params],
                "request_body": bool(request_body),
                "response_kind": response_kind,
            }
    ts_lines += [
        "}",
        "",
        "export const operations = " + json.dumps(metadata, indent=2) + " as const;",
        "",
    ]
    py_lines += ["OPERATIONS = " + pprint.pformat(metadata, width=100, sort_dicts=True), ""]
    return "\n".join(ts_lines), "\n".join(py_lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    ts_output, py_output = generate(yaml.safe_load(SCHEMA.read_text()))
    ts_output = subprocess.run(
        ["pnpm", "exec", "prettier", "--stdin-filepath", str(TS_OUTPUT)],
        input=ts_output,
        text=True,
        capture_output=True,
        check=True,
        cwd=ROOT,
    ).stdout
    for path, content in ((TS_OUTPUT, ts_output), (PY_OUTPUT, py_output)):
        if args.check:
            if not path.exists() or path.read_text() != content:
                raise SystemExit(f"Generated SDK is stale: {path.relative_to(ROOT)}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)


if __name__ == "__main__":
    main()
