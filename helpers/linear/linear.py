"""Linear GraphQL helpers (Personal API Key).

Single endpoint: POST https://api.linear.app/graphql with {query, variables}.

Auth: Linear expects `Authorization: <api-key>` (NO `Bearer` prefix), unlike
most services. The graft daemon's default would inject `Bearer <token>`, so
each helper sets the `Authorization` header itself via `_headers()` — the
daemon detects an existing `Authorization` header and skips its default
injection (see daemon._handle_request).

Token comes from `[linear] token = "lin_api_..."` in `.graft/auth.toml`, or
the `GRAFT_LINEAR_TOKEN` env var. The TOML field is named `token` even
though Linear calls it an "API key" / PAT — graft normalizes on `token`.
"""

from typing import Any

from graft.context import auth, request

_URL = "https://api.linear.app/graphql"


def _headers() -> dict[str, str]:
    if (key := auth("linear")) is None:
        raise RuntimeError("linear token missing: configure .graft/auth.toml or GRAFT_LINEAR_TOKEN")
    return {"Authorization": key, "Content-Type": "application/json"}


def _post(query: str, variables: dict[str, Any]) -> dict[str, Any]:
    body = {"query": query, "variables": variables}
    return dict(request("linear", "POST", _URL, json=body, headers=_headers()).json())


def list_issues(
    team_id: str | None = None, state: str | None = None, limit: int = 30
) -> list[dict[str, Any]]:
    """List issues, optionally filtered by team and state name.

    Generalization:
        Works for any workspace the API key can read. Filter by team_id
        (from `list_teams`) and/or state name ("Todo", "In Progress", "Done").
        Variant example: list_issues(team_id="abc-123", state="In Progress", limit=10)
        Not applicable: cursor pagination beyond `first: limit` — extend with
        `pageInfo` if you need >250 results in one call.
    """
    q = (
        "query Issues($filter: IssueFilter, $first: Int) { issues(filter: $filter, first: $first)"
        " { nodes { id identifier title state { name } team { id key name } createdAt url } } }"
    )
    f: dict[str, Any] = {}
    if team_id is not None:
        f["team"] = {"id": {"eq": team_id}}
    if state is not None:
        f["state"] = {"name": {"eq": state}}
    data = _post(q, {"filter": f, "first": limit})
    return list(data.get("data", {}).get("issues", {}).get("nodes", []))


def get_issue(issue_id: str) -> dict[str, Any]:
    """Fetch one issue by UUID or human identifier (e.g. "ENG-123").

    Generalization:
        Works for any issue id (UUID or team-prefixed identifier like "ENG-123").
        Variant example: get_issue("ENG-42")
        Not applicable: archived issues require `includeArchived: true` — extend if needed.
    """
    q = (
        "query Issue($id: String!) { issue(id: $id) { id identifier title description"
        " state { name } team { id key name } assignee { id name } url createdAt updatedAt } }"
    )
    data = _post(q, {"id": issue_id})
    return dict(data.get("data", {}).get("issue") or {})


def create_issue(team_id: str, title: str, description: str = "") -> dict[str, Any]:
    """Create a new issue in the given team.

    Generalization:
        Works for any team_id the API key has write access to (from `list_teams`).
        Variant example: create_issue("abc-123", "Bug: parser crashes on empty input")
        Not applicable: setting assignee/labels/priority/state — extend the
        IssueCreateInput payload if needed.
    """
    m = (
        "mutation IssueCreate($input: IssueCreateInput!) { issueCreate(input: $input)"
        " { success issue { id identifier title url } } }"
    )
    payload = {"teamId": team_id, "title": title, "description": description}
    data = _post(m, {"input": payload})
    return dict(data.get("data", {}).get("issueCreate") or {})


def list_teams() -> list[dict[str, Any]]:
    """List all teams visible to the API key — call this first to discover team IDs.

    Generalization:
        Works for any workspace; returns every team the key can see.
        Variant example: list_teams() then pick the team whose `key` is "ENG".
        Not applicable: archived teams (Linear hides them from this query by default).
    """
    q = "query { teams { nodes { id key name description } } }"
    data = _post(q, {})
    return list(data.get("data", {}).get("teams", {}).get("nodes", []))
