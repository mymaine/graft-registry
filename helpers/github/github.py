"""GitHub REST API helpers (PAT-authenticated).

Token comes from `[github] token = "ghp_..."` in `.graft/auth.toml`, or
the `GRAFT_GITHUB_TOKEN` env var. The graft daemon injects it as
`Authorization: Bearer <token>` automatically — these helpers don't see
the token directly.
"""

from typing import Any

from graft.context import request

_BASE = "https://api.github.com"
_HEADERS = {"Accept": "application/vnd.github+json"}


def list_issues(
    owner: str, repo: str, state: str = "open", limit: int = 30
) -> list[dict[str, Any]]:
    """List issues for a repository.

    Generalization:
        Works for any (owner, repo). Filter by state ("open"/"closed"/"all"), cap by limit.
        Variant example: list_issues("python", "cpython", state="closed", limit=50)
        Not applicable: GitHub Enterprise on custom domains; pull requests appear in this
        list too (filter by `pull_request` key absent if you want issues only).
    """
    url = f"{_BASE}/repos/{owner}/{repo}/issues"
    params = {"state": state, "per_page": str(limit)}
    return list(request("github", "GET", url, params=params, headers=_HEADERS).json())


def get_repo(owner: str, repo: str) -> dict[str, Any]:
    """Fetch a repository's metadata (description, stars, default branch, ...).

    Generalization:
        Works for any public (owner, repo) and private repos the token can read.
        Variant example: get_repo("torvalds", "linux")
        Not applicable: GitHub Enterprise on custom domains.
    """
    url = f"{_BASE}/repos/{owner}/{repo}"
    return dict(request("github", "GET", url, headers=_HEADERS).json())


def search_code(query: str, limit: int = 30) -> list[dict[str, Any]]:
    """Search code across all repositories the token can access.

    Generalization:
        Works for any GitHub code-search query syntax (e.g. "fastapi repo:tiangolo/fastapi").
        Variant example: search_code("def parse_args language:python", limit=10)
        Not applicable: search is heavily rate-limited (10 req/min unauthenticated, 30 with token);
        results are capped by GitHub at 1000 regardless of `limit`.
    """
    url = f"{_BASE}/search/code"
    params = {"q": query, "per_page": str(limit)}
    body = request("github", "GET", url, params=params, headers=_HEADERS).json()
    return list(body.get("items", []))


def list_pulls(
    owner: str, repo: str, state: str = "open", limit: int = 30
) -> list[dict[str, Any]]:
    """List pull requests for a repository.

    Generalization:
        Works for any (owner, repo). Filter by state ("open"/"closed"/"all"), cap by limit.
        Variant example: list_pulls("rust-lang", "rust", state="closed", limit=50)
        Not applicable: GitHub Enterprise on custom domains.
    """
    url = f"{_BASE}/repos/{owner}/{repo}/pulls"
    params = {"state": state, "per_page": str(limit)}
    return list(request("github", "GET", url, params=params, headers=_HEADERS).json())


def create_issue(owner: str, repo: str, title: str, body: str = "") -> dict[str, Any]:
    """Open a new issue in a repository.

    Generalization:
        Works for any (owner, repo) the token has write access to.
        Variant example: create_issue("myorg", "tracker", "Bug: foo crashes on bar", body="...")
        Not applicable: requires `repo` (or `public_repo` for public repos) scope on the token;
        labels/assignees/milestones are not exposed by this helper — extend if needed.
    """
    url = f"{_BASE}/repos/{owner}/{repo}/issues"
    payload = {"title": title, "body": body}
    return dict(request("github", "POST", url, json=payload, headers=_HEADERS).json())
