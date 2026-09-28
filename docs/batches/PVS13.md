# PVS13 — Permissioned MCP adapter
## Result
An MCP endpoint lets an assistant use 14 event tools that are thin wrappers over existing API routes, gated by the API credential's allowed actions, scope, owner role and the existing audit layer.
## Changes
- `mcp_adapter`: JSON-RPC handling (`initialize`, `ping`, `tools/list`, `tools/call`), strict argument validation, dispatch through the real Django handler with the caller's bearer token, 64 KB result cap, extra `mcp.tool_called` audit.
- Credential-only (cookies refused), Origin-checked, POST-only; unlisted and unknown tools are indistinguishable.
- `scripts/conflux_mcp_stdio.py` bridges stdio-only MCP clients.
## Verification
- `test_mcp_adapter.py` (18): auth matrix, handshake, filtered `tools/list`, real read/write calls, owner-role enforcement, event/workspace scoping, argument-injection cases, transport hygiene, truncation, bridge.
- Full suite 1257 passed/23 skipped; ruff clean for all PVS code; OpenAPI + SDK checks clean.
## Limitations
- Tools only (no resources/prompts/batching/streaming); `list_my_projects` reflects the existing member-scoped route.
## Next
PVS14 (workspace-level cross-event portfolio).
