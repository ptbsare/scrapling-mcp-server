# scrapling-mcp-server

A minimal [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server wrapping [Scrapling](https://github.com/D4Vinci/Scrapling)'s stealthy fetcher — one tool, maximum stealth, minimum context.

## Features

- **Single `fetch` tool** — only `url` is required, everything else has optimal anti-bot defaults
- **Anti-bot bypass** — Patchright + fingerprint spoofing + Cloudflare auto-solver
- **cookie.txt support** — load cookies from `SCRAPLING_COOKIE_FILE` env var (Netscape format)
- **Zero config** — `uvx` one-liner to run

## Quick Start

### MCP client config (Claude Desktop / Cursor / etc.)

```jsonc
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

### Install

```bash
uv pip install git+https://github.com/ptbsare/scrapling-mcp-server
```

### Run directly

```bash
# stdio mode (for MCP clients)
uvx --from git+https://github.com/ptbsare/scrapling-mcp-server scrapling-mcp-server

# With cookie file
SCRAPLING_COOKIE_FILE=./cookies.txt uvx --from git+https://github.com/ptbsare/scrapling-mcp-server scrapling-mcp-server
```

## Tool: `fetch`

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `url` | ✅ | — | The URL to fetch |
| `extraction_type` | | `"markdown"` | `"markdown"`, `"html"`, or `"text"` |
| `wait` | | `3000` | Milliseconds to wait after page load for JS rendering |
| `timeout` | | `90000` | Operation timeout in ms |
| `solve_cloudflare` | | `false` | Auto-solve Cloudflare challenges (adds ~5s overhead) |

**Returns:** `{ "status": int, "url": str, "content": list[str] }`

### Hardcoded anti-bot defaults

These are applied automatically and not exposed as parameters:

| Setting | Value | Why |
|---------|-------|-----|
| `hide_canvas` | `true` | Randomize canvas fingerprint |
| `block_webrtc` | `true` | Prevent WebRTC IP leak |
| `disable_resources` | `true` | Block fonts/images/media for speed |
| `network_idle` | `true` | Wait for all JS to finish |
| `google_search` | `true` | Set Google referer header |
| `block_ads` | `true` | Block ~3500 ad/tracker domains |
| `allow_webgl` | `true` | Disabling WebGL is suspicious |
| `headless` | `true` | Server environment |
| `main_content_only` | `true` | Extract only `<body>` content |

## Cookie.txt Support

Set `SCRAPLING_COOKIE_FILE` to a [Netscape cookie.txt](https://curl.se/docs/http-cookies.html) file:

```bash
export SCRAPLING_COOKIE_FILE="$HOME/cookies.txt"
```

Format (tab-separated):

```
# Netscape HTTP Cookie File
.example.com	TRUE	/	TRUE	1735689600	session_id	abc123
```

### Getting cookie.txt

- Chrome: [Get cookies.txt LOCALLY](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
- Firefox: [cookies.txt](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)

## License

MIT
