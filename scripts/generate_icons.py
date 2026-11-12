"""One-off: rasterize the montaz mark (web/public/favicon.svg) into PWA icons
(512/192 PNG) + a Windows favicon.ico. Run with the project venv python."""
from __future__ import annotations

import base64
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

PUBLIC = Path(__file__).resolve().parent.parent / "web" / "public"
SVG = PUBLIC / "favicon.svg"


def rasterize(size: int, out: Path) -> None:
    data = base64.b64encode(SVG.read_bytes()).decode()
    html = (
        f'<body style="margin:0;background:transparent">'
        f'<img src="data:image/svg+xml;base64,{data}" width="{size}" height="{size}">'
        f"</body>"
    )
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": size, "height": size})
        page.set_content(html)
        page.wait_for_timeout(200)
        page.screenshot(path=str(out), omit_background=True)
        browser.close()
    print(f"  {out.name}: {out.stat().st_size} bytes")


print("Rasterizing PWA icons from", SVG.name)
rasterize(512, PUBLIC / "icon-512.png")
rasterize(192, PUBLIC / "icon-192.png")

# Windows .ico from the 512 master (PIL picks/derives the embedded sizes).
ico = PUBLIC / "favicon.ico"
Image.open(PUBLIC / "icon-512.png").save(ico, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (256, 256)])
print(f"  favicon.ico: {ico.stat().st_size} bytes")
