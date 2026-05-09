# scrapling-mcp-server

A minimal [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server that wraps [Scrapling](https://github.com/D4Vinci/Scrapling)'s `StealthyFetcher` — one tool, full stealth.

## Features

- **Single `fetch` tool** — exposes the complete `stealthy_fetch` API as an MCP tool
- **Anti-bot bypass** — Patchright + fingerprint spoofing + Cloudflare challenge solver
- **cookie.txt support** — load cookies from a Netscape cookie.txt file via `SCRAPLING_COOKIE_FILE` env var
- **Zero config** — `uvx` one-liner to run

## Quick Start

### As MCP server (stdio)

```jsonc
// Claude Desktop / Cursor / any MCP client
{
  "mcpServers": {
    "scrapling": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/ptbsare/scrapling-mcp-server",
        "scrapling-mcp-server"
      ],
      "env": {
        // Optional: path to Netscape cookie.txt
        "SCRAPLING_COOKIE_FILE": "/path/to/cookies.txt"
      }
    }
  }
}
```

### Install from GitHub

```bash
uv pip install git+https://github.com/ptbsare/scrapling-mcp-server
```

### Run directly

```bash
# stdio mode (default, for MCP clients)
uvx --from git+https://github.com/ptbsare/scrapling-mcp-server scrapling-mcp-server

# Or with cookie file
SCRAPLING_COOKIE_FILE=./cookies.txt uvx --from git+https://github.com/ptbsare/scrapling-mcp-server scrapling-mcp-server
```

### Development

```bash
git clone https://github.com/ptbsare/scrapling-mcp-server
cd scrapling-mcp-server
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
```

## Tool Reference

### `fetch`

Stealthy web fetch that bypasses anti-bot protections.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | `str` | *required* | The URL to fetch |
| `extraction_type` | `str` | `"markdown"` | `"markdown"`, `"html"`, or `"text"` |
| `css_selector` | `str?` | `None` | CSS selector to extract specific elements |
| `main_content_only` | `bool` | `true` | Extract only `<body>` main content |
| `headless` | `bool` | `true` | Run browser in headless mode |
| `google_search` | `bool` | `true` | Set Google referer header |
| `real_chrome` | `bool` | `false` | Use real Chrome instead of Chromium |
| `wait` | `float` | `0` | Milliseconds to wait after page load |
| `proxy` | `str?` | `None` | Proxy URL (`http://user:pass@host:port`) |
| `timezone_id` | `str?` | `None` | Browser timezone (e.g. `"America/New_York"`) |
| `locale` | `str?` | `None` | Browser locale (e.g. `"en-US"`) |
| `extra_headers` | `dict?` | `None` | Additional HTTP headers |
| `useragent` | `str?` | `None` | Custom User-Agent string |
| `hide_canvas` | `bool` | `false` | Add noise to canvas fingerprinting |
| `cdp_url` | `str?` | `None` | Connect to existing browser via CDP |
| `timeout` | `float` | `30000` | Operation timeout in ms |
| `disable_resources` | `bool` | `false` | Block fonts/images/media |
| `wait_selector` | `str?` | `None` | CSS selector to wait for |
| `cookies` | `list?` | `None` | Playwright SetCookieParam list |
| `network_idle` | `bool` | `false` | Wait for network idle |
| `wait_selector_state` | `str` | `"attached"` | `"attached"`/`"detached"`/`"hidden"`/`"visible"` |
| `block_webrtc` | `bool` | `false` | Prevent WebRTC IP leak |
| `allow_webgl` | `bool` | `true` | Allow WebGL (disabling is suspicious) |
| `solve_cloudflare` | `bool` | `false` | Auto-solve Cloudflare challenges |
| `additional_args` | `dict?` | `None` | Extra Playwright context args |

**Returns:** `{ "status": int, "url": str, "content": list[str] }`

## Cookie.txt Support

Set the `SCRAPLING_COOKIE_FILE` environment variable to the path of a [Netscape cookie.txt](https://curl.se/docs/http-cookies.html) file:

```bash
export SCRAPLING_COOKIE_FILE="$HOME/cookies.txt"
```

The cookie.txt format (tab-separated):

```
# Netscape HTTP Cookie File
.example.com	TRUE	/	TRUE	1735689600	session_id	abc123
```

Fields: `domain`, `flag`, `path`, `secure`, `expires`, `name`, `value`

Cookies from the file are merged with any `cookies` parameter passed to `fetch`. Explicit cookies override file cookies by `(name, domain)` pair.

### Obtaining cookie.txt

Use browser extensions like:
- [Get cookies.txt LOCALLY](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc) (Chrome)
- [cookies.txt](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/) (Firefox)

## License

MIT
