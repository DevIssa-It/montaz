"""Crawl a running web app: discover main pages (same-origin) for the demo walkthrough."""
from __future__ import annotations

import re
from typing import Any
from urllib.parse import urljoin, urlsplit

import httpx

MAX_PAGES = 6


def _same_origin(base: str, url: str) -> bool:
    b, u = urlsplit(base), urlsplit(url)
    return (b.netloc == u.netloc or not u.netloc) and not url.startswith(("mailto:", "tel:", "javascript:"))


def _title_of(html: str) -> str:
    match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    if not match:
        match = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.IGNORECASE | re.DOTALL)
    return re.sub(r"<[^>]+>|\s+", " ", match.group(1)).strip()[:80] if match else ""


def _links_of(html: str, base: str) -> list[dict[str, str]]:
    """Internal links with visible text: [{'href','text'}], crawled order."""
    found: list[dict[str, str]] = []
    seen: set[str] = set()
    for m in re.finditer(r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', html, re.IGNORECASE | re.DOTALL):
        href, inner = m.group(1), m.group(2)
        absolute = urljoin(base, href).split("#", 1)[0].rstrip("/")
        text = re.sub(r"<[^>]+>|\s+", " ", inner).strip()[:40]
        if not text or absolute in seen or not _same_origin(base, absolute):
            continue
        seen.add(absolute)
        found.append({"href": href, "text": text})
    return found[:6]


async def crawl_site(app_url: str) -> list[dict[str, Any]]:
    """Breadth-first crawl from app_url; returns pages with url/title/links."""
    app_url = app_url.rstrip("/")
    pages: list[dict[str, Any]] = []
    seen: set[str] = set()
    queue: list[str] = [app_url]
    async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
        while queue and len(pages) < MAX_PAGES:
            url = queue.pop(0)
            normalized = url.split("#", 1)[0]
            if normalized in seen:
                continue
            seen.add(normalized)
            try:
                resp = await client.get(url)
                content_type = resp.headers.get("content-type", "")
                if "text/html" not in content_type:
                    continue
            except httpx.HTTPError:
                continue
            page_url = str(resp.url).split("#")[0]
            pages.append(
                {
                    "url": page_url,
                    "title": _title_of(resp.text) or url,
                    "links": _links_of(resp.text, page_url),
                }
            )
            for href in re.findall(r'href=["\']([^"\']+)["\']', resp.text)[:40]:
                absolute = urljoin(str(resp.url), href)
                absolute = absolute.split("#", 1)[0].rstrip("/")
                if _same_origin(app_url, absolute) and absolute not in seen and not re.search(
                    r"\.(png|jpe?g|gif|svg|ico|css|js|woff2?|mp4|webm|pdf|zip)$", absolute, re.IGNORECASE
                ):
                    queue.append(absolute)
    return pages
