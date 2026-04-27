# Contributing to graft-registry

graft's bet is simple: **the agent writes the helper, the human reviews it.**
The registry is the shared layer of that bet — what you submit here isn't just
code other people install. It's your agent's hard-won "service-level API
experience" sinking into a public git memory. The next person (or agent)
reaching for service `X` doesn't have to learn it from zero. They `graft add x`
and start from where you left off.

That's the contract. Helpers in this registry are read like documentation,
extended like scaffolding, and trusted enough to land on someone else's disk
without a sandbox. Keep that in mind as you read on.

---

## Table of contents

- [Repository layout](#repository-layout)
- [Step 1: Fork and create your helper directory](#step-1-fork-and-create-your-helper-directory)
- [Step 2: Write `manifest.json` entry](#step-2-write-manifestjson-entry)
- [Step 3: Write `<svc>.py`](#step-3-write-svcpy)
- [CI checks — what each one wants from you](#ci-checks--what-each-one-wants-from-you)
- [Local verification before opening a PR](#local-verification-before-opening-a-pr)
- [PR title format](#pr-title-format)

---

## Repository layout

```
graft-registry/
├── manifest.json               single source of truth
└── helpers/
    └── <service>/
        ├── <service>.py        the helper (single file, v1)
        ├── README.md           usage + example
        └── tests/              optional; runs in CI if present
```

Read `helpers/echo/` end-to-end before writing your own — it is the smallest
complete example and the dogfood reference for the daemon-to-helper pipeline.
`helpers/github/`, `helpers/linear/`, `helpers/notion/`, `helpers/stripe/`
demonstrate the same pattern against real authenticated APIs.

---

## Step 1: Fork and create your helper directory

```bash
# 1. Fork mymaine/graft-registry on GitHub
git clone https://github.com/<you>/graft-registry.git
cd graft-registry
git checkout -b add-<svc>

mkdir -p helpers/<svc>
touch helpers/<svc>/<svc>.py
touch helpers/<svc>/README.md
```

The directory name, the filename, and the manifest service key all use the
same `<svc>` token. It must be a valid Python identifier (lowercase, no
hyphens, no dots). CI rejects anything else.

---

## Step 2: Write `manifest.json` entry

Add an entry under `services` in the top-level `manifest.json`. Required
fields and constraints (CI enforces these):

| Field | Constraint |
|---|---|
| `version` | semver string (e.g. `"0.1.0"`) |
| `path` | `"helpers/<svc>/<svc>.py"` — must not start with `/`, must not contain `..` |
| `description` | one human-readable sentence; non-empty |
| `summary_for_index` | <= 60 chars, lands in user-side `helpers/INDEX.md` |
| `auth_required` | `true` if helper needs a credential; `false` otherwise |
| `tags` | free-form list, used for future search |

The service key itself (the thing under `"services": { ... }`) must satisfy
Python's `str.isidentifier()`. CI checks this — `my-svc` and `123svc` both
fail.

Example:

```json
"<svc>": {
  "version": "0.1.0",
  "path": "helpers/<svc>/<svc>.py",
  "description": "What this helper covers in one sentence.",
  "summary_for_index": "<svc> API (N helpers)",
  "auth_required": true,
  "tags": ["category", "official"]
}
```

---

## Step 3: Write `<svc>.py`

Helpers are files agents read, edit, and trust. The shape is rigid on purpose.

**Hard rules** (graft's ast validator enforces; CI runs the same validator):

1. **Every public function has a `Generalization:` section in its docstring.**
   This is not a stylistic preference. The `Generalization:` block tells the
   next agent *what variants of input this function actually handles* and
   *what is out of scope*. Without it the validator fails the helper.

2. **No forbidden imports**: `httpx`, `helpers.*` (sibling helper imports),
   `importlib`, anything that bypasses the daemon's HTTP path or reaches into
   another service.

3. **No forbidden builtins**: `__import__`, `exec`, `eval`, `compile`. If you
   feel you need them, you don't.

4. **All HTTP goes through `graft.context.request`.** This is the single
   choke-point that gives the daemon auth injection, retry, and stats.

   ```python
   from graft.context import request

   def list_things(query: str) -> dict:
       """List things matching query.

       Generalization:
           Works for any non-empty query string up to ~200 chars.
           Variant example: list_things("recent")
           Not applicable: empty query (server returns 400); requires
           SVC_TOKEN configured in .graft/auth.toml.
       """
       url = "https://api.example.com/v1/things"
       return request("<svc>", "GET", url, params={"q": query}).json()
   ```

5. **Hardcode service identity, parameterize what varies between calls.** Base
   URL and auth scheme are constants of the service, not arguments. Resource
   paths, query params, payloads are arguments.

6. **Type-annotate everything**, top to bottom. CI runs `mypy --strict` on
   your file.

For the full design rationale see graft's
[SKILL.md](https://github.com/mymaine/graft/blob/main/src/graft/templates/SKILL.md).

---

## CI checks — what each one wants from you

CI fires on PRs that touch `helpers/**` or `manifest.json`. It only checks
the helper directories your PR actually changed (one helper's PR doesn't
re-validate the whole registry). For each changed `helpers/<svc>/`, five
checks run in order:

### 1. `ruff check helpers/<svc>/`

Standard lint. Run `ruff check helpers/<svc>/` locally; fix anything it
flags. No project-specific ruff config — defaults apply.

### 2. `mypy --strict helpers/<svc>/<svc>.py`

`mypy --strict` on your single helper file. Every parameter and return type
annotated, no implicit `Any`, no untyped function bodies. Use `dict[str, Any]`
for opaque JSON responses; that's the convention the existing helpers follow.

### 3. graft validator

CI installs graft pinned to **`v0.2.0`** (git tag, not `main`, not `latest`)
and runs the same `graft.validator.check(source, "<svc>")` that the daemon
runs at install time. It checks two things:

- Every public function has a `Generalization:` section in its docstring.
- The file imports nothing forbidden and calls no forbidden builtins
  (see Step 3 rules 2 and 3).

If this fails, the daemon would also refuse to load your helper — fix it
before the CI even sees it.

### 4. `manifest.json` schema

CI re-parses `manifest.json` and asserts, for the changed `<svc>`:

- `<svc>` key satisfies `str.isidentifier()`.
- The `path` field exists, doesn't start with `/`, and contains no `..`
  segment. (Path-traversal guard — the daemon would reject the helper anyway,
  but CI catches it earlier.)
- `description`, `version`, and `path` are all present and non-empty.

### 5. `pytest helpers/<svc>/tests/` (conditional)

If your helper directory contains a `tests/` subdirectory, CI runs pytest on
it. If there's no `tests/`, this check is skipped. Tests are encouraged but
not required for v1 — most helpers are thin enough that the validator and
mypy carry the load. If you do add tests, mock the HTTP layer; don't hit the
real API in CI.

---

## Local verification before opening a PR

You can run the same five checks locally. From the repo root, with `<svc>`
as your service name:

```bash
# Install the same deps CI uses
python -m pip install ruff mypy pytest
pip install 'git+https://github.com/mymaine/graft.git@v0.2.0'

svc=<svc>
dir=helpers/$svc
file=$dir/$svc.py

# 1. ruff
ruff check "$dir/"

# 2. mypy
mypy --strict "$file"

# 3. graft validator
python -c "
from graft.validator import check
import sys
src = open(sys.argv[1]).read()
fail = check(src, sys.argv[2])
if fail:
    print(fail); sys.exit(1)
" "$file" "$svc"

# 4. manifest schema
python -c "
import json, sys
svc = sys.argv[1]
data = json.load(open('manifest.json'))
e = data['services'][svc]
assert svc.isidentifier(), 'service key not a Python identifier'
for f in ('description', 'version', 'path'):
    assert e.get(f), f'missing {f}'
assert not e['path'].startswith('/'), 'path starts with /'
assert '..' not in e['path'].split('/'), 'path contains ..'
print('manifest ok')
" "$svc"

# 5. pytest (only if tests/ exists)
[ -d "$dir/tests" ] && pytest "$dir/tests" || echo "no tests; skipped"
```

If all five pass locally, the same five will pass in CI.

---

## PR title format

Use conventional-commits style:

```
feat(helper): add <svc>
```

For follow-up changes to an existing helper:

```
fix(helper): <svc> handle 429 retry
docs(helper): <svc> clarify pagination contract
```

Keep one helper per PR. Reviewers want to compare a single helper file
against a single manifest entry — a PR that touches three services makes
that loop slow.
