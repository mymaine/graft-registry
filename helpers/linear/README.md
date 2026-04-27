# linear

Linear GraphQL API helpers — list/get issues, list teams, create issues.

Single endpoint: `POST https://api.linear.app/graphql` with `{query, variables}`.
The 4 helpers cover the cold-start path. Add more (status updates, comments,
projects) by editing `helpers/linear.py` in your project.

## Auth

Create a Personal API Key at <https://linear.app/settings/api>, then store it
one of two ways:

```toml
# .graft/auth.toml (gitignored)
[linear]
token = "lin_api_..."
```

```bash
export GRAFT_LINEAR_TOKEN=lin_api_...
```

graft normalizes on `token` even though Linear's UI calls it an API key.

Linear expects `Authorization: <key>` *without* the `Bearer ` prefix the
graft daemon injects by default. Each helper sets the `Authorization`
header itself; the daemon detects an existing header and skips its default.

## Functions

| Helper | Purpose |
|---|---|
| `list_teams()` | List teams visible to the key — call first to discover team IDs |
| `list_issues(team_id=None, state=None, limit=30)` | List issues, filter by team and/or state name |
| `get_issue(issue_id)` | Fetch one issue by UUID or human id (`"ENG-123"`) |
| `create_issue(team_id, title, description="")` | Create a new issue in a team |

Returns parsed JSON — no wrapping types so you see Linear's actual GraphQL shape.

## Example

```python
from helpers.linear import list_teams, list_issues, get_issue, create_issue

eng = next(t for t in list_teams() if t["key"] == "ENG")

for i in list_issues(team_id=eng["id"], state="In Progress", limit=10):
    print(f"{i['identifier']}: {i['title']}")

print(get_issue("ENG-42")["description"])
print(create_issue(eng["id"], "Bug: parser crashes on empty input")["issue"]["url"])
```

## Rate limits

- 1,500 requests/hour per API key (GraphQL complexity also metered)
- Daemon does not retry; on `429` or `RATELIMITED`, back off and retry yourself

## Not in this helper (extend yourself)

- State changes / `IssueUpdateInput` mutations (large schema)
- Comments, attachments, labels, projects, cycles
- Webhook setup, OAuth flow (PAT-only here)
- Cursor pagination beyond `first: limit`
