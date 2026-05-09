"""scrapling-mcp-server — minimal MCP wrapper around Scrapling's stealthy_fetch."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional, Sequence

from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Cookie.txt parser (Netscape / curl format)
# ---------------------------------------------------------------------------

def _parse_cookie_file(path: str) -> list[dict]:
    """Parse a Netscape cookie.txt file into Playwright SetCookieParam dicts."""
    cookies: list[dict] = []
    with open(path, encoding="utf-8") as fh:
        for raw_line in fh:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) < 7:
                parts = line.split()
            if len(parts) < 7:
                continue
            domain, flag, path_str, secure, expires, name, value = parts[:7]
            cookies.append({
                "name": name,
                "value": value,
                "domain": domain,
                "path": path_str,
                "secure": secure.upper() == "TRUE",
                "expires": float(expires) if expires not in ("0", "") else -1,
                "httpOnly": False,
            })
    return cookies


def _load_cookies() -> Optional[Sequence[dict]]:
    """Load cookies from SCRAPLING_COOKIE_FILE env var."""
    env_path = os.environ.get("SCRAPLING_COOKIE_FILE", "").strip()
    if not env_path:
        return None
    p = Path(env_path)
    if not p.is_file():
        print(
            f"[scrapling-mcp-server] WARNING: SCRAPLING_COOKIE_FILE={env_path!r} not found, skipping.",
            file=sys.stderr,
        )
        return None
    cookies = _parse_cookie_file(str(p))
    print(
        f"[scrapling-mcp-server] Loaded {len(cookies)} cookie(s) from {env_path}",
        file=sys.stderr,
    )
    return cookies


# ---------------------------------------------------------------------------
# Content extraction
# ---------------------------------------------------------------------------

def _extract_content(
    page,
    extraction_type: str = "markdown",
    css_selector: Optional[str] = None,
    main_content_only: bool = True,
) -> list[str]:
    """Extract content from a Scrapling Response using its built-in Convertor."""
    from scrapling.core.shell import Convertor

    return list(
        Convertor._extract_content(
            page,
            css_selector=css_selector,
            extraction_type=extraction_type,
            main_content_only=main_content_only,
        )
    )


# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------

_SERVER_NAME = "scrapling-mcp-server"


def _build_server() -> FastMCP:
    server = FastMCP(name=_SERVER_NAME)

    async def fetch(
        url: str,
        extraction_type: str = "markdown",
        wait: float = 3000,
        timeout: float = 90000,
    ) -> dict:
        """Stealthy web fetch with anti-bot bypass.

        Uses Patchright + fingerprint spoofing + Cloudflare auto-solver.
        Optimal anti-bot defaults are applied automatically:
        - Cloudflare challenge solving enabled
        - Canvas/WebRTC fingerprint protection
        - Ad/tracker domain blocking
        - Google referer header
        - Real browser header generation via browserforge
        - Unnecessary resource blocking (fonts/images/media)

        Cookies: set SCRAPLING_COOKIE_FILE env var to a Netscape cookie.txt path.

        :param url: The URL to fetch.
        :param extraction_type: "markdown" (default), "html", or "text".
        :param wait: Milliseconds to wait after page load for JS rendering (default 3000).
        :param timeout: Operation timeout in milliseconds (default 90000).
        :returns: Dict with keys: status, url, content (list[str]).
        """
        from scrapling.fetchers.stealth_chrome import StealthyFetcher

        merged_cookies = _load_cookies()

        kwargs: dict = {
            "headless": True,
            "google_search": True,
            "real_chrome": False,
            "wait": wait,
            "timeout": timeout,
            "hide_canvas": True,
            "disable_resources": True,
            "network_idle": True,
            "block_webrtc": True,
            "allow_webgl": True,
            "solve_cloudflare": True,
            "block_ads": True,
        }
        if merged_cookies:
            kwargs["cookies"] = merged_cookies

        response = await StealthyFetcher.async_fetch(url, **kwargs)

        content = _extract_content(
            response,
            extraction_type=extraction_type,
            css_selector=None,
            main_content_only=True,
        )

        return {
            "status": response.status,
            "url": response.url,
            "content": content,
        }

    server.add_tool(fetch, title="fetch")

    return server


def main() -> None:
    """Entry point for `scrapling-mcp-server` console script."""
    _build_server().run(transport="stdio")


if __name__ == "__main__":
    main()
