import json
import re
from urllib.parse import urlencode

from django.core.handlers.wsgi import WSGIHandler
from django.test import RequestFactory
from django.urls import reverse

from .tools import BY_NAME, PATH_ARG_NAMES, TOOLS, UUID_PATTERN

SUPPORTED_VERSIONS = ("2025-06-18", "2025-03-26", "2024-11-05")
MAX_RESULT_BYTES = 64 * 1024
INSTRUCTIONS = (
    "Conflux event tools. Every call runs as the API credential's owner, limited to the "
    "actions that credential allows, and is audited."
)
_UUID = re.compile(UUID_PATTERN)
_handler = None


class ToolInputError(ValueError):
    pass


def error(request_id, code, message):
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def allowed_tools(credential):
    return [tool for tool in TOOLS if tool.action in credential.allowed_actions]


def _validated_arguments(tool, arguments):
    if not isinstance(arguments, dict):
        raise ToolInputError("arguments must be an object")
    schema = tool.input_schema()
    unknown = set(arguments) - set(schema["properties"])
    if unknown:
        raise ToolInputError(f"unexpected arguments: {', '.join(sorted(unknown))}")
    for name in schema["required"]:
        if name not in arguments:
            raise ToolInputError(f"missing argument: {name}")
    for name, value in arguments.items():
        spec = schema["properties"][name]
        if not isinstance(value, str):
            raise ToolInputError(f"{name} must be a string")
        if "pattern" in spec and not _UUID.fullmatch(value):
            raise ToolInputError(f"{name} must be a UUID")
        if "enum" in spec and value not in spec["enum"]:
            raise ToolInputError(f"{name} must be one of {spec['enum']}")
        if len(value) > spec.get("maxLength", 200):
            raise ToolInputError(f"{name} is too long")
    return arguments


def _internal_handler():
    global _handler
    if _handler is None:
        _handler = WSGIHandler()
    return _handler


def call_route(http_request, tool, arguments, kwargs):
    """Run the tool's route through the complete middleware/auth/permission stack."""
    route_kwargs = {
        "workspace_public_id": kwargs["workspace_public_id"],
        "event_public_id": kwargs["event_public_id"],
    }
    route_kwargs.update({PATH_ARG_NAMES[a]: arguments[a] for a in tool.path_args})
    url = reverse(tool.url_name, kwargs=route_kwargs)
    query = {k: arguments[k] for k in tool.query if k in arguments}
    if query:
        url += "?" + urlencode(query)
    body = {k: arguments[k] for k in tool.body if k in arguments}
    extra = {
        "HTTP_AUTHORIZATION": http_request.META["HTTP_AUTHORIZATION"],
        "HTTP_HOST": http_request.get_host(),
        "REMOTE_ADDR": http_request.META.get("REMOTE_ADDR", ""),
    }
    if "HTTP_X_FORWARDED_FOR" in http_request.META:
        extra["HTTP_X_FORWARDED_FOR"] = http_request.META["HTTP_X_FORWARDED_FOR"]
    factory = RequestFactory()
    if tool.read_only:
        inner = factory.get(url, **extra)
    else:
        inner = factory.generic(
            tool.method, url, json.dumps(body), content_type="application/json", **extra
        )
    response = _internal_handler().get_response(inner)
    raw = b"".join(response.streaming_content) if response.streaming else response.content
    return response.status_code, raw


def tool_result(status, raw):
    truncated = len(raw) > MAX_RESULT_BYTES
    text = raw[:MAX_RESULT_BYTES].decode("utf-8", "replace")
    if status >= 400:
        text = f"HTTP {status}: {text}"
    if truncated:
        text += "\n[truncated]"
    return {"content": [{"type": "text", "text": text}], "isError": status >= 400}


def handle(message, credential, http_request, kwargs, audit):
    """One JSON-RPC message -> response dict, or None for a notification."""
    if not isinstance(message, dict) or message.get("jsonrpc") != "2.0":
        return error(None, -32600, "Invalid request.")
    request_id = message.get("id")
    method = message.get("method")
    params = message.get("params") or {}
    if "id" not in message:
        return None
    if not isinstance(method, str) or not isinstance(params, dict):
        return error(request_id, -32600, "Invalid request.")
    if method == "initialize":
        asked = params.get("protocolVersion")
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": asked if asked in SUPPORTED_VERSIONS else SUPPORTED_VERSIONS[0],
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "conflux", "version": "1"},
                "instructions": INSTRUCTIONS,
            },
        }
    if method == "ping":
        return {"jsonrpc": "2.0", "id": request_id, "result": {}}
    if method == "tools/list":
        tools = [tool.describe() for tool in allowed_tools(credential)]
        return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": tools}}
    if method == "tools/call":
        tool = BY_NAME.get(params.get("name"))
        if tool is None or tool.action not in credential.allowed_actions:
            return error(request_id, -32602, "Unknown tool.")
        try:
            arguments = _validated_arguments(tool, params.get("arguments", {}))
        except ToolInputError as exc:
            return error(request_id, -32602, f"Invalid arguments: {exc}")
        status, raw = call_route(http_request, tool, arguments, kwargs)
        audit(tool, status, sorted(arguments))
        return {"jsonrpc": "2.0", "id": request_id, "result": tool_result(status, raw)}
    return error(request_id, -32601, "Method not found.")
