#!/usr/bin/env python3
"""Render the README hero demo GIF from synthetic terminal frames.

Pipeline: scenes -> terminal-styled HTML frames -> headless Chrome PNGs (2x)
-> ffmpeg palettegen/paletteuse (-> gifsicle if installed). All content is fake.
Run:  python3 docs/demo/build_demo.py   (writes docs/demo.gif)
"""
from __future__ import annotations

import html
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
W, H = 960, 590          # CSS px; screenshots are 2x
ROWS = 23                # visible terminal rows
CHARS_PER_FRAME = 5      # typing speed
TYPE_DT = 0.07           # seconds per typing frame
OUT = Path(__file__).resolve().parent.parent / "demo.gif"

CSS = """
*{box-sizing:border-box}body{margin:0;background:#0b0e14;font:16px/22px Menlo,Monaco,'DejaVu Sans Mono',monospace;color:#d6dbe4}
.win{width:%dpx;height:%dpx;display:flex;flex-direction:column}
.bar{height:44px;background:#161b26;display:flex;align-items:center;padding:0 16px;border-bottom:1px solid #232a3a}
.dot{width:12px;height:12px;border-radius:6px;margin-right:8px}
.cap{margin-left:14px;font:600 15px -apple-system,'Helvetica Neue',sans-serif;color:#9fb3d9}
.cap b{color:#7ee2a8}
pre{margin:0;padding:12px 18px;white-space:pre;flex:1;overflow:hidden;font:inherit}
.p{color:#7ee2a8}.c{color:#fff}.dim{color:#6b7689}.ok{color:#7ee2a8}.chg{color:#f3c969}
.k{color:#7cc4ff}.s{color:#a6e3a1}.n{color:#fab387}.cur{background:#d6dbe4;color:#0b0e14}
""" % (W, H)


def hl_json(line: str) -> str:
    out = html.escape(line)
    out = re.sub(r'(&quot;[^&]*?&quot;)(:)', r'<span class="k">\1</span>\2', out)
    out = re.sub(r':( ?)(&quot;.*?&quot;)', r':\1<span class="s">\2</span>', out)
    out = re.sub(r'(?<![\w&;])(-?\d[\d.]*|true|false|null)(?=[,\s]|$)', r'<span class="n">\1</span>', out)
    return out


def fmt(line: tuple[str, str]) -> str:
    text, cls = line
    if cls == "json":
        return hl_json(text)
    return f'<span class="{cls}">{html.escape(text)}</span>'


def build_frames(scenes):
    """Yield (html, seconds)."""
    for sc in scenes:
        buf: list[tuple[str, str]] = []
        cap = sc["caption"]
        for step in sc["steps"]:
            kind = step[0]
            if kind == "cmd":
                cmd_lines = step[1]  # list of lines (continuations)
                text = "\n".join(cmd_lines)
                for i in range(0, len(text) + 1, CHARS_PER_FRAME):
                    typed = text[:i]
                    shown = buf + [(("$ " if j == 0 else "  ") + l, "cmd") for j, l in enumerate(typed.split("\n"))]
                    yield page_cmd(cap, shown), TYPE_DT
                buf += [(("$ " if j == 0 else "  ") + l, "cmd") for j, l in enumerate(cmd_lines)]
                yield page_cmd(cap, buf), step[2] if len(step) > 2 else 0.35
            elif kind == "out":
                buf += step[1]
                yield page_cmd(cap, buf), step[2]


def page_cmd(cap, buf):
    rows = buf[-ROWS:]
    lines = []
    for text, cls in rows:
        if cls == "cmd":
            if text.startswith("$ "):
                lines.append(f'<span class="p">$ </span><span class="c">{html.escape(text[2:])}</span>')
            else:
                lines.append(f'<span class="c">{html.escape(text)}</span>')
        else:
            lines.append(fmt((text, cls)))
    body = "\n".join(lines)
    return (f"<!doctype html><meta charset=utf-8><style>{CSS}</style><div class=win>"
            f'<div class=bar><span class=dot style="background:#ff5f57"></span><span class=dot style="background:#febc2e"></span>'
            f'<span class=dot style="background:#28c840"></span><span class=cap>{cap}</span></div><pre>{body}</pre></div>')


def main(scenes) -> None:
    tmp = Path(tempfile.mkdtemp(prefix="demo-frames-"))
    try:
        frames = list(build_frames(scenes))
        # dedupe consecutive identical pages by merging durations
        merged: list[list] = []
        for h, d in frames:
            if merged and merged[-1][0] == h:
                merged[-1][1] += d
            else:
                merged.append([h, d])
        concat = []
        for i, (h, d) in enumerate(merged):
            (tmp / f"f{i:04d}.html").write_text(h, encoding="utf-8")
            subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                            f"--screenshot={tmp / f'f{i:04d}.png'}", f"--window-size={W},{H}",
                            "--force-device-scale-factor=2", f"file://{tmp / f'f{i:04d}.html'}"],
                           check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            concat += [f"file 'f{i:04d}.png'", f"duration {d / 2 if i == len(merged) - 1 else d:.2f}"]  # last entry is repeated below
        concat.append(f"file 'f{len(merged)-1:04d}.png'")
        (tmp / "list.txt").write_text("\n".join(concat) + "\n")
        total = sum(d for _, d in merged)
        print(f"{len(merged)} frames, {total:.1f}s")
        vf = "fps=12,scale=1200:-1:flags=lanczos"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-i", "list.txt",
                        "-vf", f"{vf},palettegen=max_colors=64:stats_mode=diff", "palette.png"], cwd=tmp, check=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-i", "list.txt", "-i", "palette.png",
                        "-lavfi", f"{vf}[x];[x][1:v]paletteuse=dither=none", "-loop", "0", str(OUT)], cwd=tmp, check=True)
        if shutil.which("gifsicle"):
            subprocess.run(["gifsicle", "-O3", "-b", str(OUT)], check=True)
        print(f"wrote {OUT} ({OUT.stat().st_size/1e6:.2f} MB)")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
