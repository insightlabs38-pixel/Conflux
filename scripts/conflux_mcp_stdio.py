#!/usr/bin/env python3
"""Bridge an MCP client that speaks stdio to a Conflux MCP endpoint.

    CONFLUX_MCP_URL=https://host/api/v1/workspaces/W/events/E/mcp/ \
    CONFLUX_MCP_TOKEN=<api credential> python scripts/conflux_mcp_stdio.py

Reads one JSON-RPC message per line from stdin, posts it to the endpoint with the
credential as a bearer token, and writes the reply line (if any) to stdout.
The credential is read from the environment only, never from arguments.
"""

import json
import os
import sys
import urllib.error
import urllib.request


def forward(line, url, token, opener=urllib.request.urlopen):
    request = urllib.request.Request(
        url,
        data=line.encode(),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {token}",
        },
        method="POST",
    )
    try:
        with opener(request, timeout=60) as response:
            body = response.read().decode()
            return body.strip() or None
    except urllib.error.HTTPError as exc:
        try:
            message = json.loads(line)
        except ValueError:
            message = {}
        if "id" not in message:
            return None
        return json.dumps(
            {
                "jsonrpc": "2.0",
                "id": message["id"],
                "error": {"code": -32000, "message": f"HTTP {exc.code} from Conflux"},
            }
        )


def main():
    url, token = os.environ.get("CONFLUX_MCP_URL"), os.environ.get("CONFLUX_MCP_TOKEN")
    if not url or not token:
        sys.exit("Set CONFLUX_MCP_URL and CONFLUX_MCP_TOKEN.")
    for line in sys.stdin:
        if line.strip():
            reply = forward(line, url, token)
            if reply:
                sys.stdout.write(reply + "\n")
                sys.stdout.flush()


if __name__ == "__main__":
    main()
