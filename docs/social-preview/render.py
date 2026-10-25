#!/usr/bin/env python3
"""Render a 1280x640 GitHub social preview in the painterly "OpenAI blog cover" style.

A full-bleed abstract oil-painting background (generated separately, no text in
it) with a white monochrome icon and a white wordmark, like OpenAI's blog
covers. Text is laid out here with HTML so it is always spelled exactly right.

Everything is kept inside the central square: chat apps (iMessage, Slack,
WeChat, Telegram) crop link previews to a centered square thumbnail, so a long
one-line name gets cut off. Use "|" in --name to break it into lines.

Example:
  python3 docs/social-preview/render.py
"""

from __future__ import annotations

import argparse
import html
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

CHROME_CANDIDATES = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "google-chrome",
    "chromium",
    "chromium-browser",
)

PAGE = """<!doctype html><html><head><meta charset="utf-8"><style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1280px;height:640px;overflow:hidden;position:relative;
background:#e9735f url("{background}") center/cover no-repeat;
font-family:system-ui,-apple-system,"Inter","PingFang SC",sans-serif;color:#fff;
display:flex;align-items:center;justify-content:center}}
body::before{{content:"";position:absolute;inset:0;
background:radial-gradient(ellipse 40% 50% at 50% 50%,rgba(0,0,0,{veil}) 0,transparent 75%)}}
.lockup{{position:relative;display:flex;align-items:center;gap:26px;max-width:540px;
filter:drop-shadow(0 2px 18px rgba(0,0,0,.16))}}
.icon{{flex:none;width:{icon_size}px;height:{icon_size}px;background:#fff;
-webkit-mask:url("{icon}") center/contain no-repeat;mask:url("{icon}") center/contain no-repeat}}
h1{{font-size:{size}px;font-weight:550;letter-spacing:-.03em;line-height:1.02;text-align:left}}
p{{margin-top:16px;font-size:24px;font-weight:450;opacity:.95;text-align:left}}
</style></head><body><div class="lockup">{icon_div}<div><h1>{name}</h1>{tagline}</div></div></body></html>"""


def find_chrome() -> str:
    for candidate in CHROME_CANDIDATES:
        path = candidate if os.path.isabs(candidate) else shutil.which(candidate)
        if path and os.path.exists(path):
            return path
    raise SystemExit("Chrome/Chromium not found")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    here = Path(__file__).resolve().parent
    parser.add_argument("--background", default=str(here / "background.jpg"), help="painterly background image, no text")
    parser.add_argument("--name", default="Social Media|Toolkit", help='wordmark; "|" breaks lines, e.g. "Telegram|Agent CLI"')
    parser.add_argument("--icon", default=str(here / "icon.svg"), help="icon (SVG or transparent PNG); rendered white via its alpha")
    parser.add_argument("--tagline", default="", help="optional short line under the wordmark")
    parser.add_argument("--size", type=int, default=0, help="wordmark px (default: fit to length)")
    parser.add_argument("--veil", type=float, default=0.3, help="center darkening 0-0.4 for legibility")
    parser.add_argument("--out", default=str(here.parent / "social-preview.jpg"))
    args = parser.parse_args()

    lines = [line.strip() for line in args.name.split("|")]
    longest = max(len(line) for line in lines)
    room = 520 - (130 if args.icon else 0)
    size = args.size or max(56, min(104, int(room / (0.56 * max(longest, 1)))))
    icon_size = int(size * len(lines) * 1.02) if len(lines) > 1 else int(size * 1.15)
    page = PAGE.format(
        background=Path(args.background).resolve().as_uri(),
        veil=args.veil,
        size=size,
        icon=Path(args.icon).resolve().as_uri() if args.icon else "",
        icon_size=icon_size,
        icon_div='<div class="icon"></div>' if args.icon else "",
        name="<br>".join(html.escape(line) for line in lines),
        tagline=f"<p>{html.escape(args.tagline)}</p>" if args.tagline else "",
    )
    out = Path(args.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="social-preview-") as tmp:
        page_path = Path(tmp) / "card.html"
        page_path.write_text(page, encoding="utf-8")
        shot = Path(tmp) / "card.png"
        subprocess.run(
            [find_chrome(), "--headless=new", "--disable-gpu", "--hide-scrollbars",
             "--allow-file-access-from-files", f"--user-data-dir={tmp}/profile",
             "--window-size=1280,640", f"--screenshot={shot}", page_path.as_uri()],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        if out.suffix.lower() in (".jpg", ".jpeg"):
            # GitHub rejects social previews over 1 MB; painterly PNGs are ~1.7 MB.
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(shot), "-q:v", "3", str(out)], check=True)
        else:
            shutil.copyfile(shot, out)
    if out.stat().st_size > 1_000_000:
        print(f"warning: {out.name} is over 1 MB; GitHub will reject it — use a .jpg --out")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
