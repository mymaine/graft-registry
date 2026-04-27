# graft-registry

A community git registry of graft helpers — pure git, no server.

[graft](https://github.com/maine/graft) is a thin Python harness that lets
agents (Claude Code, Codex, etc.) accumulate HTTP API capabilities as plain
`helpers/<service>.py` files. This repository is the shared pool that
`graft add <service>` pulls from.

## How `graft add` uses this registry

```
graft add echo
```

1. Client shallow-clones (or fetches updates for) this repo into a local cache.
2. Reads `manifest.json`, looks up `services["echo"]`.
3. Copies the file at `services.echo.path` into the user's project at
   `helpers/echo.py` (the directory layer in this registry collapses to one
   file in the consuming project — see "Repository layout" below).
4. Runs the same ast validator that the daemon uses (`Generalization:`
   docstring + forbidden imports/builtins) before writing.
5. If `auth_required: true`, prompts the user to fill in
   `.graft/auth.toml` for the service.

No server, no package index, no auth token to publish. The registry is just
a git repo.

## Repository layout

```
graft-registry/
├── README.md
├── LICENSE                     MIT
├── manifest.json               single source of truth: service → metadata
└── helpers/
    └── <service>/
        ├── <service>.py        the helper (single file, v1)
        └── README.md           usage + example
```

Each service gets its own directory. v1 ships one `.py` per service; the
directory leaves room for future split files (`linear/issues.py`,
`linear/projects.py`) without breaking the manifest path contract.

## manifest.json schema (v1)

```json
{
  "$schema_version": "1",
  "services": {
    "<service>": {
      "version": "0.1.0",
      "path": "helpers/<service>/<service>.py",
      "description": "human-readable, used in service README",
      "summary_for_index": "<= 60 chars, used in helpers/INDEX.md",
      "auth_required": false,
      "tags": ["category", "..."]
    }
  }
}
```

| Field | Purpose |
|---|---|
| `$schema_version` | Compatibility anchor. v1 = `"1"`. Bump on breaking schema changes. |
| `version` | Semver of the helper itself. Future `graft add --version` may pin it. |
| `path` | Path relative to this repo root. |
| `description` | One sentence, human-readable. |
| `summary_for_index` | <= 60 chars, drops into the user's `helpers/INDEX.md` row. |
| `auth_required` | If true, `graft add` prompts the user to configure auth. |
| `tags` | Free-form classification. Used for future `graft search`. |

Deliberately not in v1 (YAGNI): `dependencies` (helpers may not import each
other), `python_version` (registry tracks graft's own >= 3.11), and
`min_graft_version` (no version gate yet — bump `$schema_version` instead).

## Contributing a helper

1. Fork this repo.
2. Add a directory `helpers/<service>/` with `<service>.py` and `README.md`.
3. Write the helper following graft's
   [SKILL.md design principles](https://github.com/maine/graft/blob/main/src/graft/templates/SKILL.md):
   - Hardcode the service identity (base URL, auth scheme).
   - Parameterize anything that varies between calls.
   - Every public function gets a `Generalization:` docstring section.
   - Only import from stdlib and `graft.context`. No `httpx`, no
     `helpers.*`, no `importlib`, no `__import__` / `exec` / `eval`.
4. Add an entry to `manifest.json` under `services`.
5. Open a PR.

## Quality gates

Every helper that lands in this registry must pass graft's ast validator
(`Generalization:` docstring + 4 forbidden imports + 4 forbidden builtins).
v1 trusts contributor-side checks; future automation will run the validator,
`ruff`, and `mypy --strict` in CI.

## License

MIT — see `LICENSE`.
