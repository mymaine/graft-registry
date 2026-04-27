"""httpbin.org echo helper for dogfooding the graft pipeline.

Used to verify daemon routing, auth-injection no-op path, retry behaviour, and
stats append end-to-end without requiring a real authenticated service.
"""

from typing import Any

from graft.context import request


def echo_get(path: str = "/anything", params: dict[str, str] | None = None) -> dict[str, Any]:
    """Echo a GET request through httpbin and return its parsed JSON body.

    Generalization:
        Works for any path under /anything/* and arbitrary string-valued query params.
        Variant example: echo_get("/anything/foo", params={"x": "1"})
        Not applicable: requires httpbin.org reachable from the network; non-/anything
        paths exist on httpbin but are not part of this helper's contract.
    """
    url = f"https://httpbin.org{path}"
    return request("echo", "GET", url, params=params).json()


def echo_post(payload: dict[str, Any], path: str = "/anything") -> dict[str, Any]:
    """Echo a JSON POST through httpbin and return its parsed JSON body.

    Generalization:
        Works for any JSON-serializable payload and any path under /anything/*.
        Variant example: echo_post({"hello": "world"})
        Not applicable: requires httpbin.org reachable; payload must be JSON-serializable;
        non-JSON content types are out of scope (use a different helper).
    """
    url = f"https://httpbin.org{path}"
    return request("echo", "POST", url, json=payload).json()
