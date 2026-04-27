# github

GitHub REST API helpers — list/get repo, list issues + pulls, search code, open issues.

5 helpers cover the read-mostly cold-start path that an agent reaches for
first. Add more (review comments, releases, branches, ...) by editing
`helpers/github.py` in your project once `graft add github` has dropped
the file in.

## Auth

Get a [Personal Access Token](https://github.com/settings/tokens) with
`repo` scope (or `public_repo` for public-only access). Store it one of
two ways:

```toml
# .graft/auth.toml (gitignored)
[github]
token = "ghp_..."
```

or via environment:

```bash
export GRAFT_GITHUB_TOKEN=ghp_...
```

The graft daemon reads this and injects `Authorization: Bearer <token>`
on every helper call. The helpers themselves never see the token.

## Functions

| Helper | Purpose |
|---|---|
| `list_issues(owner, repo, state="open", limit=30)` | List issues (note: includes PRs in GitHub's data model) |
| `get_repo(owner, repo)` | Fetch repository metadata |
| `search_code(query, limit=30)` | Code search across accessible repos |
| `list_pulls(owner, repo, state="open", limit=30)` | List pull requests |
| `create_issue(owner, repo, title, body="")` | Open a new issue |

All return parsed JSON (`dict` or `list[dict]`) — no wrapping types so
the agent sees GitHub's actual schema.

## Example

```python
from helpers.github import list_issues, get_repo, create_issue

repo = get_repo("anthropics", "claude-code")
print(repo["description"], repo["stargazers_count"])

issues = list_issues("anthropics", "claude-code", state="open", limit=5)
for i in issues:
    print(f"#{i['number']}: {i['title']}")

new = create_issue("myorg", "tracker", "Bug: graft add fails on stale tempdir")
print(f"opened #{new['number']}")
```

## Rate limits

- Authenticated: 5,000 req/hour for REST, 30 req/min for code search
- Unauthenticated: 60 req/hour total — practically useless

The daemon does not handle rate-limit retry. If you hit `403` with
`X-RateLimit-Remaining: 0`, wait for the `X-RateLimit-Reset` epoch.

## Not in this helper (extend yourself)

- Review comments, status checks, branch protection, GitHub Apps OAuth
- GraphQL endpoint (REST only here)
- Pagination beyond `limit` — for >100 results, iterate `page=2,3,...`
