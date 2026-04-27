# echo

Dogfood helper for the graft pipeline. Calls `https://httpbin.org/anything`,
which echoes whatever request you send back as a JSON response. Useful for
end-to-end verification (daemon routing, request relay, response parsing,
stats append, retry path) without needing a real authenticated service.

## When to use

- Verifying a fresh `graft serve` setup actually relays HTTP and writes
  `.graft/stats.jsonl`.
- Smoke-testing `graft add` end to end.
- Examples in graft docs that need a real, no-auth HTTP target.

Not intended for real production work.

## Usage

```python
from helpers.echo import echo_get, echo_post

# GET with no params
r = echo_get()
# r["url"] == "https://httpbin.org/anything"

# GET with query params and a sub-path
r = echo_get("/anything/foo", params={"x": "1"})
# r["args"] == {"x": "1"}

# POST a JSON body
r = echo_post({"hello": "world"})
# r["json"] == {"hello": "world"}
```

The response is the parsed JSON dict from httpbin — it always contains keys
like `args`, `data`, `headers`, `json`, `method`, `origin`, `url`. See the
[httpbin docs](https://httpbin.org/) for the full shape.

## Auth

None. httpbin is public.

## Why this lives in the registry

`echo` is the smallest possible real helper — it forces the entire graft
pipeline to be wired correctly (validator, daemon, request relay, stats,
git auto-commit) but introduces zero auth or rate-limit complexity. Every
`graft add` change is regression-tested against `graft add echo`.
