# notion

Notion API helpers — search/get pages, read block content, query databases, append paragraphs.

5 helpers cover the read-mostly cold-start path plus a write entrypoint.
Notion's data model splits **pages** (a node with properties) from **block
children** (the visible content). Both are first-class here.

## Auth

Create an integration at https://www.notion.so/my-integrations and copy
the **Internal Integration Secret** (`secret_...`). Then **share each page
or database** with the integration from the Notion UI — tokens alone grant
no access.

```toml
# .graft/auth.toml (gitignored)
[notion]
token = "secret_..."
```

or via environment:

```bash
export GRAFT_NOTION_TOKEN=secret_...
```

The graft daemon injects `Authorization: Bearer <token>` on every call.
The helpers add the required `Notion-Version: 2022-06-28` header.

## Functions

| Helper | Purpose |
|---|---|
| `list_pages(query="", limit=30)` | Search pages by title (empty query = recent) |
| `get_page(page_id)` | Fetch a page's properties (not content) |
| `get_block_children(block_id, limit=50)` | List child blocks (page body or nested) |
| `query_database(database_id, limit=30)` | Query rows from a database |
| `append_block(block_id, text)` | Append a paragraph to a page or block |

All return parsed JSON (`dict` or `list[dict]`) — no wrapping types so the
agent sees Notion's actual schema.

## Example

```python
from helpers.notion import list_pages, get_page, get_block_children, append_block

hits = list_pages("roadmap", limit=5)
for p in hits:
    print(p["id"], p.get("properties", {}))

page = get_page(hits[0]["id"])
blocks = get_block_children(page["id"], limit=100)
for b in blocks:
    print(b["type"], b)

append_block(page["id"], "Status: helper v0.1 shipped.")
```

## Rate limits

Notion enforces ~3 requests/second per integration on average. Bursts
return `429`; the daemon does not retry rate-limit responses. Respect
`Retry-After` if you see one.

## Not in this helper (extend yourself)

- Pagination beyond `limit` (`has_more` + `next_cursor` cursor walking)
- Database `filter` / `sort` DSL on `query_database`
- Rich text, headings, lists, toggles, code blocks in `append_block`
- Page creation, page property updates, database creation
- File uploads, comments, user listing
