"""Notion API helpers (integration-token authenticated).

Token comes from `[notion] token = "secret_..."` in `.graft/auth.toml`, or
the `GRAFT_NOTION_TOKEN` env var. The graft daemon injects it as
`Authorization: Bearer <token>` automatically. The `Notion-Version` header
is required by the API on every request and is set here per-call.
"""

from typing import Any

from graft.context import request

_BASE = "https://api.notion.com/v1"
_HEADERS = {"Notion-Version": "2022-06-28"}


def list_pages(query: str = "", limit: int = 30) -> list[dict[str, Any]]:
    """Search for pages the integration can access (empty query = list all).

    Generalization:
        Works for any text query against page titles. Empty query returns recent pages.
        Variant example: list_pages("meeting notes", limit=10)
        Not applicable: searching block-level text (Notion search only matches titles);
        results capped at `limit` — pagination via `next_cursor` not handled in v1.
    """
    payload: dict[str, Any] = {"page_size": limit}
    if query:
        payload["query"] = query
    body = request("notion", "POST", f"{_BASE}/search", json=payload, headers=_HEADERS).json()
    return list(body.get("results", []))


def get_page(page_id: str) -> dict[str, Any]:
    """Fetch a page's properties and metadata (not its body content).

    Generalization:
        Works for any page id the integration is shared with. Returns properties only —
        use get_block_children() for the actual content blocks.
        Variant example: get_page("abc123def456...")
        Not applicable: pages the integration has not been explicitly invited to.
    """
    return dict(request("notion", "GET", f"{_BASE}/pages/{page_id}", headers=_HEADERS).json())


def get_block_children(block_id: str, limit: int = 50) -> list[dict[str, Any]]:
    """List child blocks of a page or block (the actual text/headings/lists).

    Generalization:
        Works for any page id (top-level body) or block id (nested children).
        Variant example: get_block_children(page_id, limit=100)
        Not applicable: deeply nested trees — only direct children returned, recurse manually;
        results capped at `limit`, pagination cursor not handled in v1.
    """
    url = f"{_BASE}/blocks/{block_id}/children"
    params = {"page_size": str(limit)}
    body = request("notion", "GET", url, params=params, headers=_HEADERS).json()
    return list(body.get("results", []))


def query_database(database_id: str, limit: int = 30) -> list[dict[str, Any]]:
    """Query rows (pages) from a Notion database.

    Generalization:
        Works for any database id the integration is shared with. Returns pages with their
        property values populated per the database schema.
        Variant example: query_database("def789...", limit=100)
        Not applicable: filter/sort DSL not exposed — extend the helper if needed;
        results capped at `limit`, pagination cursor not handled in v1.
    """
    url = f"{_BASE}/databases/{database_id}/query"
    body = request("notion", "POST", url, json={"page_size": limit}, headers=_HEADERS).json()
    return list(body.get("results", []))


def append_block(block_id: str, text: str) -> dict[str, Any]:
    """Append a paragraph block containing `text` to a page or block.

    Generalization:
        Works for any page id or block id the integration can write to.
        Variant example: append_block(page_id, "Status update: shipped helper v0.1")
        Not applicable: rich text formatting, headings, lists, code blocks — this only
        appends plain paragraph blocks. Compose the children payload manually for richer types.
    """
    url = f"{_BASE}/blocks/{block_id}/children"
    payload = {
        "children": [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": text}}]},
            }
        ]
    }
    return dict(request("notion", "PATCH", url, json=payload, headers=_HEADERS).json())
