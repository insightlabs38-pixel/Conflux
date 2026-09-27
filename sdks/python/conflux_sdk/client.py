"""HTTP transport for the generated Conflux operation catalog."""

import json
from urllib.error import HTTPError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from .generated import OPERATIONS


class ApiError(Exception):
    def __init__(self, status: int, body):
        self.status = status
        self.body = body
        super().__init__(f"Conflux API returned {status}")


class ConfluxClient:
    def __init__(self, base_url: str, *, bearer_token=None, session_token=None, opener=None):
        self.base_url = base_url.rstrip("/")
        self.bearer_token = bearer_token
        self.session_token = session_token
        self.opener = opener or urlopen

    def call(self, operation_id: str, *, path=None, query=None, body=None):
        spec = OPERATIONS[operation_id]
        url_path = spec["path"]
        path = path or {}
        extra_path = set(path) - set(spec["path_params"])
        if extra_path:
            raise ValueError(f"Unknown path parameters: {sorted(extra_path)}")
        for name in spec["path_params"]:
            if name not in path or path[name] is None:
                raise ValueError(f"Missing path parameter: {name}")
            url_path = url_path.replace("{" + name + "}", quote(str(path[name]), safe=""))
        url = self.base_url + url_path
        if query:
            extra_query = set(query) - set(spec["query_params"])
            if extra_query:
                raise ValueError(f"Unknown query parameters: {sorted(extra_query)}")
            values = {
                name: str(value).lower() if isinstance(value, bool) else value
                for name, value in query.items()
                if value is not None
            }
            if values:
                url += "?" + urlencode(values)
        headers = {}
        if self.bearer_token:
            headers["Authorization"] = f"Bearer {self.bearer_token}"
        if self.session_token:
            headers["Cookie"] = f"session={self.session_token}"
        data = None
        if body is not None:
            if not spec["request_body"]:
                raise ValueError(f"Operation does not accept a JSON body: {operation_id}")
            headers["Content-Type"] = "application/json"
            data = json.dumps(body).encode("utf-8")
        request = Request(url, data=data, headers=headers, method=spec["method"])
        try:
            with self.opener(request) as response:
                status = response.status
                raw = response.read()
        except HTTPError as error:
            raw = error.read()
            try:
                problem = json.loads(raw)
            except (ValueError, UnicodeDecodeError):
                problem = raw.decode("utf-8", errors="replace")
            raise ApiError(error.code, problem) from error
        if status == 204 or spec["response_kind"] == "none":
            return None
        if spec["response_kind"] == "json":
            return json.loads(raw)
        return raw.decode("utf-8")
