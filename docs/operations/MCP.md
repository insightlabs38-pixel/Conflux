# Permissioned MCP adapter (PVS13)

`POST /api/v1/workspaces/{ws}/events/{event}/mcp/` speaks the Model Context Protocol (streamable HTTP, JSON replies, tools only) so an AI assistant can read — and, if explicitly allowed, act on — one event. It adds **no capability of its own**: each tool is one existing API route, dispatched through the full middleware, authentication, role-permission, validation and audit stack as the credential's owner.

## Granting access

1. An organizer issues an API credential (`POST …/api-credentials/`, see CREDENTIALS.md) whose `allowed_actions` include `POST:mcp-endpoint` plus the route actions each tool needs, e.g. `GET:evaluation-plan-progress`. Scope it to one event where possible; it expires in ≤ 90 days and can be revoked.
2. `tools/list` shows only tools whose route action the credential allows; anything else is reported as an unknown tool. Even an allowed tool still fails (as an MCP tool error carrying the HTTP status) if the owner's workspace role does not permit the route, so demoting or removing the owner takes effect immediately.
3. Browser session cookies are refused, and requests with a foreign `Origin` are rejected.

| Tool                                                                                               | Route action                                                      | Notes                                                |
| -------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------- | ---------------------------------------------------- |
| `list_stages`, `list_my_projects`, `get_project`                                                   | `GET:stage-list`, `GET:project-list`, `GET:project-detail`        | project tools return the owner's own projects        |
| `plan_progress`, `plan_results`                                                                    | `GET:evaluation-plan-progress`, `GET:evaluation-plan-results`     |                                                      |
| `voting_results`, `judge_workload`, `event_analytics`                                              | `GET:voting-results`, `GET:judge-workload`, `GET:event-analytics` |                                                      |
| `list_announcements`, `list_result_corrections`, `mentor_request_queue`, `list_exception_requests` | matching `GET:` routes                                            |                                                      |
| `create_announcement`, `add_mentor_note`                                                           | `POST:announcement-list`, `POST:mentor-note-list`                 | the only writes; both are ordinary audited mutations |

Tool arguments are strict (UUIDs and enums are validated before any route is built; unknown arguments are rejected). Results larger than 64 KB are truncated, and tool descriptions warn that participant-written text is data, not instructions. Every call also writes an `mcp.tool_called` audit event naming the tool, HTTP status and argument _names_ (never values).

## Connecting

Clients with HTTP support: URL above, header `Authorization: Bearer <credential>`. Stdio-only clients: run `scripts/conflux_mcp_stdio.py` with `CONFLUX_MCP_URL` and `CONFLUX_MCP_TOKEN` set.

Limitations: no JSON-RPC batching, no server-initiated streams, no resources/prompts, no per-credential rate limit beyond the API's own.
