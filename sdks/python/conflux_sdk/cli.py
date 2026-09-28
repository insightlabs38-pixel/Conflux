import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, build_opener
from uuid import UUID

from .client import ApiError, ConfluxClient

EVENTS = "api_v1_workspaces_workspace_public_id_events"
DETAIL = EVENTS + "_event_public_id"
ARCHIVE = "api_v1_workspaces_workspace_public_id_archive"


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def origin(value):
    if any(ord(character) <= 32 for character in value) or "\\" in value:
        raise ValueError("Invalid API origin characters.")
    parts = urlsplit(value)
    try:
        port = parts.port
    except ValueError as exc:
        raise ValueError("Invalid API origin port.") from exc
    local = parts.hostname in ("localhost", "127.0.0.1", "::1")
    if (
        not parts.hostname
        or parts.scheme not in ("http", "https")
        or (parts.scheme == "http" and not local)
        or parts.username is not None
        or parts.password is not None
        or parts.path not in ("", "/")
        or parts.query
        or parts.fragment
        or port == 0
    ):
        raise ValueError(
            "Use an HTTPS API origin, or HTTP on loopback, without credentials/path/query."
        )
    return value.rstrip("/")


def read_object(path):
    with Path(path).open(encoding="utf-8") as source:
        data = json.load(source)
    if not isinstance(data, dict) or not data:
        raise ValueError("Input must be a nonempty JSON object.")
    return data


def write_result(value, output=None):
    text = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    if output is None or output == "-":
        sys.stdout.write(text)
        return
    destination = Path(output)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=destination.parent, delete=False
        ) as target:
            temporary = Path(target.name)
            target.write(text)
            target.flush()
            os.fsync(target.fileno())
        os.link(temporary, destination)
    finally:
        if temporary:
            temporary.unlink(missing_ok=True)


def parser():
    root = argparse.ArgumentParser(description="Administer Conflux through its canonical API.")
    root.add_argument("--base-url", default=os.environ.get("CONFLUX_BASE_URL"))
    root.add_argument("--workspace", type=UUID, default=os.environ.get("CONFLUX_WORKSPACE"))
    root.add_argument("--timeout", type=float, default=30)
    commands = root.add_subparsers(dest="command", required=True)
    commands.add_parser("whoami", help="Read the current identity and workspace IDs")
    events = commands.add_parser("events").add_subparsers(dest="action", required=True)
    events.add_parser("list")
    for name in ("get", "update", "status", "export"):
        item = events.add_parser(name)
        item.add_argument("event", type=UUID)
        if name == "update":
            item.add_argument("--input", required=True, help="JSON object of changed event fields")
        elif name == "status":
            item.add_argument("--status", choices=["open", "closed", "archived"], required=True)
        elif name == "export":
            item.add_argument("--mode", choices=["config", "full"], default="config")
            item.add_argument("--output", required=True, help="New private file, or - for stdout")
    create = events.add_parser("create")
    create.add_argument("--name", required=True)
    create.add_argument("--slug", required=True)
    create.add_argument("--timezone", default="UTC")
    create.add_argument("--description", default="")
    importing = events.add_parser(
        "import", help="Preview archive import; --apply creates a new draft"
    )
    importing.add_argument("--input", required=True)
    importing.add_argument("--name", required=True)
    importing.add_argument("--slug", required=True)
    importing.add_argument("--apply", action="store_true")
    return root


def execute(args, client):
    if args.command == "whoami":
        return client.call("get_api_v1_accounts_me")
    if args.workspace is None:
        raise ValueError("Supply --workspace or CONFLUX_WORKSPACE for event commands.")
    path = {"workspace_public_id": str(args.workspace)}
    if hasattr(args, "event"):
        path["event_public_id"] = str(args.event)
    action = args.action
    if action == "list":
        return client.call("get_" + EVENTS, path=path)
    if action == "get":
        return client.call("get_" + DETAIL, path=path)
    if action == "create":
        return client.call(
            "post_" + EVENTS,
            path=path,
            body={
                "name": args.name,
                "slug": args.slug,
                "timezone": args.timezone,
                "description": args.description,
                "is_public": False,
            },
        )
    if action == "update":
        return client.call("patch_" + DETAIL, path=path, body=read_object(args.input))
    if action == "status":
        return client.call("post_" + DETAIL + "_status", path=path, body={"status": args.status})
    if action == "export":
        if args.output != "-" and Path(args.output).exists():
            raise ValueError("Export output already exists; choose a new path.")
        result = client.call("get_" + DETAIL + "_archive", path=path, query={"mode": args.mode})
        write_result(result, args.output)
        return None
    if action == "import":
        archive = read_object(args.input)
        return client.call(
            "post_" + ARCHIVE + ("_import" if args.apply else "_preview"),
            path=path,
            body={
                "archive": archive,
                "name": args.name,
                "slug": args.slug,
            },
        )
    raise ValueError("Unknown event command.")


def main(argv=None, *, client_factory=ConfluxClient):
    args = parser().parse_args(argv)
    secrets = [os.environ.get("CONFLUX_SESSION_TOKEN"), os.environ.get("CONFLUX_BEARER_TOKEN")]
    try:
        if not args.base_url:
            raise ValueError("Supply --base-url or CONFLUX_BASE_URL.")
        base_url = origin(args.base_url)
        session, bearer = secrets
        if bool(session) == bool(bearer):
            raise ValueError("Set exactly one of CONFLUX_SESSION_TOKEN or CONFLUX_BEARER_TOKEN.")
        if any(character in (session or bearer) for character in "\r\n;"):
            raise ValueError("Invalid credential characters.")
        if not 0 < args.timeout <= 300:
            raise ValueError("Timeout must be greater than zero and at most 300 seconds.")
        transport = build_opener(NoRedirect())
        client = client_factory(
            base_url,
            session_token=session,
            bearer_token=bearer,
            opener=lambda request: transport.open(request, timeout=args.timeout),
        )
        result = execute(args, client)
        if result is not None:
            write_result(result)
        return 0
    except (ApiError, OSError, ValueError, URLError) as exc:
        message = (
            f"HTTP {exc.status}: {json.dumps(exc.body)}" if isinstance(exc, ApiError) else str(exc)
        )
        for secret in secrets:
            if secret:
                message = message.replace(secret, "[redacted]")
        print(message, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
