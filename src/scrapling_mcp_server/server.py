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
                # Also accept space-separated (some exporters use spaces)
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
                "httpOnly": False,  # cookie.txt format has no httpOnly field
            })
    return cookies


def _load_cookies(
    explicit_cookies: Optional[Sequence[dict]] = None,
) -> Optional[Sequence[dict]]:
    """Merge explicit cookies with those from SCRAPLING_COOKIE_FILE env var."""
    env_path = os.environ.get("SCRAPLING_COOKIE_FILE", "").strip()
    file_cookies: list[dict] = []
    if env_path:
        p = Path(env_path)
        if not p.is_file():
            print(
                f"[scrapling-mcp-server] WARNING: SCRAPLING_COOKIE_FILE={env_path!r} not found, skipping.",
                file=sys.stderr,
            )
        else:
            file_cookies = _parse_cookie_file(str(p))
            print(
                f"[scrapling-mcp-server] Loaded {len(file_cookies)} cookie(s) from {env_path}",
                file=sys.stderr,
            )

    if explicit_cookies and file_cookies:
        # Explicit cookies take priority (override by name+domain)
        seen = {(c["name"], c.get("domain", "")) for c in explicit_cookies}
        merged = list(explicit_cookies)
        for c in file_cookies:
            if (c["name"], c.get("domain", "")) not in seen:
                merged.append(c)
        return merged
    if explicit_cookies:
        return explicit_cookies
    if file_cookies:
        return file_cookies
    return None


# ---------------------------------------------------------------------------
# Content extraction helpers (re-use Scrapling internals)
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

    # ------------------------------------------------------------------
    # fetch — the one and only tool
    # ------------------------------------------------------------------
    async def fetch(
        url: str,
        extraction_type: str = "markdown",
        css_selector: Optional[str] = None,
        main_content_only: bool = True,
        headless: bool = True,
        google_search: bool = True,
        real_chrome: bool = False,
        wait: float = 0,
        proxy: Optional[str] = None,
        timezone_id: Optional[str] = None,
        locale: Optional[str] = None,
        extra_headers: Optional[dict[str, str]] = None,
        useragent: Optional[str] = None,
        hide_canvas: bool = False,
        cdp_url: Optional[str] = None,
        timeout: float = 30000,
        disable_resources: bool = False,
        wait_selector: Optional[str] = None,
        cookies: Optional[Sequence[dict]] = None,
        network_idle: bool = False,
        wait_selector_state: str = "attached",
        block_webrtc: bool = False,
        allow_webgl: bool = True,
        solve_cloudflare: bool = False,
        additional_args: Optional[dict] = None,
    ) -> dict:
        """Stealthy web fetch that bypasses anti-bot protections.

        Uses Scrapling's StealthyFetcher (Patchright + fingerprint spoofing +
        Cloudflare solver) under the hood.

        Cookies can be supplied in three ways (merged with priority order):
          1. ``cookies`` parameter  (Playwright SetCookieParam list)
          2. ``SCRAPLING_COOKIE_FILE`` environment variable pointing to a
             Netscape cookie.txt file
          3. Both are merged, explicit cookies override file cookies by
             (name, domain) pair.

        :param url: The URL to fetch.
        :param extraction_type: "markdown" (default), "html", or "text".
        :param css_selector: Optional CSS selector to extract specific elements.
        :param main_content_only: Extract only <body> main content (default True).
        :param headless: Run browser headless (default True).
        :param google_search: Set Google referer header (default True).
        :param real_chrome: Use real Chrome instead of Chromium (default False).
        :param wait: Milliseconds to wait after page load (default 0).
        :param proxy: Proxy URL, e.g. "http://user:pass@host:port".
        :param timezone_id: Browser timezone, e.g. "America/New_York".
        :param locale: Browser locale, e.g. "en-US".
        :param extra_headers: Additional HTTP headers.
        :param useragent: Custom User-Agent string.
        :param hide_canvas: Add noise to canvas fingerprinting (default False).
        :param cdp_url: Connect to existing browser via CDP ws:// URL.
        :param timeout: Operation timeout in milliseconds (default 30000).
        :param disable_resources: Block fonts/images/media etc (default False).
        :param wait_selector: CSS selector to wait for before returning.
        :param cookies: Playwright SetCookieParam list.
        :param network_idle: Wait for network idle (default False).
        :param wait_selector_state: "attached"|"detached"|"hidden"|"visible".
        :param block_webrtc: Prevent WebRTC IP leak (default False).
        :param allow_webgl: Allow WebGL (default True, disabling is suspicious).
        :param solve_cloudflare: Auto-solve Cloudflare challenges (default False).
        :param additional_args: Extra Playwright context args.
        :returns: Dict with keys: status, url, content (list[str]).
        """
        from scrapling.fetchers.stealth_chrome import StealthyFetcher

        merged_cookies = _load_cookies(cookies)

        kwargs: dict = {
            "headless": headless,
            "google_search": google_search,
            "real_chrome": real_chrome,
            "wait": wait,
            "timeout": timeout,
            "hide_canvas": hide_canvas,
            "disable_resources": disable_resources,
            "network_idle": network_idle,
            "block_webrtc": block_webrtc,
            "allow_webgl": allow_webgl,
            "solve_cloudflare": solve_cloudflare,
            "block_ads": True,
        }
        if proxy:
            kwargs["proxy"] = proxy
        if timezone_id:
            kwargs["timezone_id"] = timezone_id
        if locale:
            kwargs["locale"] = locale
        if extra_headers:
            kwargs["extra_headers"] = extra_headers
        if useragent:
            kwargs["useragent"] = useragent
        if cdp_url:
            kwargs["cdp_url"] = cdp_url
        if wait_selector:
            kwargs["wait_selector"] = wait_selector
        if wait_selector_state != "attached":
            kwargs["wait_selector_state"] = wait_selector_state
        if merged_cookies:
            kwargs["cookies"] = merged_cookies
        if additional_args:
            kwargs["additional_args"] = additional_args

        response = await StealthyFetcher.async_fetch(url, **kwargs)

        content = _extract_content(
            response,
            extraction_type=extraction_type,
            css_selector=css_selector,
            main_content_only=main_content_only,
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
