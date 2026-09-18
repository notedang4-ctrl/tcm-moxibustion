#!/usr/bin/env python3
"""Strip wikisource chrome, keep only the work text."""
import re
import html
from pathlib import Path


# --- workspace / data paths (override via env) -------------------------------
import os as _os

_HERE = Path(__file__).resolve()
SKILL_ROOT = _HERE.parents[2]      # scripts/extraction/x.py -> skill root
DATA = Path(_os.environ.get("TCM_DATA", str(SKILL_ROOT / "data")))
WORKSPACE = Path(_os.environ.get("TCM_WORKSPACE", "/tmp/tcm-src"))
# -----------------------------------------------------------------------------


SRC = WORKSPACE
OUT = (WORKSPACE / "clean")
OUT.mkdir(exist_ok=True)

# content begins after these markers, ends before the license footer
START_MARKERS = ["下一卷▶", "下一卷 ►", "▶", "目錄"]
END_MARKERS = [
    "本作品在全世界都属于公有领域",
    "本作品在全世界都屬於公有領域",
    "Public domain",
    "Public Domain",
    "检索自",
    "取自",
]


def clean(h: str) -> str:
    m = re.search(r'<div class="mw-parser-output">(.*)', h, re.S)
    body = m.group(1) if m else h
    body = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", body, flags=re.S)
    body = re.sub(r'<div[^>]*class="[^"]*(toc|mw-editsection|noprint|printfooter|catlinks)[^"]*"[^>]*>.*?</div>', " ", body, flags=re.S)
    body = re.sub(r"<sup[^>]*>.*?</sup>", " ", body, flags=re.S)
    body = re.sub(r"<br\s*/?>", "\n", body)
    body = re.sub(r"</(p|div|li|h[1-6]|tr|dd|dt)>", "\n", body)
    body = re.sub(r"<[^>]+>", "", body)
    body = html.unescape(body)

    # trim leading chrome: start after the last START_MARKER hit
    last = 0
    for mk in START_MARKERS:
        idx = body.rfind(mk)
        if idx > last:
            last = idx + len(mk)
    if last:
        body = body[last:]
    # trim trailing license
    for mk in END_MARKERS:
        idx = body.find(mk)
        if idx != -1:
            body = body[:idx]

    body = re.sub(r"\[\s*编辑\s*\]|\[\s*編輯\s*\]", "", body)
    body = re.sub(r"[ \t\u3000]+", " ", body)
    body = re.sub(r"\n\s*\n\s*\n+", "\n\n", body)
    lines = [l.strip() for l in body.splitlines()]
    lines = [l for l in lines if l and l not in ("", " ")]
    return "\n".join(lines)


print(f"{'file':14s} {'chars':>8s} {'灸':>5s}")
print("-" * 32)
for f in sorted(SRC.glob("*.html")):
    t = clean(f.read_text(encoding="utf-8", errors="ignore"))
    (OUT / (f.stem + ".txt")).write_text(t, encoding="utf-8")
    print(f"{f.stem:14s} {len(t):8d} {t.count('灸'):5d}")
