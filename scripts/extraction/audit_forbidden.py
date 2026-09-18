#!/usr/bin/env python3
"""Audit the 41 'moxa forbidden' entries: separate real acupoints from
section headings, and detect classical-source disagreements (some entries
say 禁灸 while another source says 灸N壮)."""
import json
import re
import sys
from pathlib import Path


# --- workspace / data paths (override via env) -------------------------------
import os as _os

_HERE = Path(__file__).resolve()
SKILL_ROOT = _HERE.parents[2]      # scripts/extraction/x.py -> skill root
DATA = Path(_os.environ.get("TCM_DATA", str(SKILL_ROOT / "data")))
WORKSPACE = Path(_os.environ.get("TCM_WORKSPACE", "/tmp/tcm-src"))
# -----------------------------------------------------------------------------


sys.path.insert(0, str(WORKSPACE))

D = (DATA / "acupoints.json")
pts = json.loads(D.read_text(encoding="utf-8"))

# headings / non-acupoint tokens that leaked through the parser
NOT_POINTS = {
    "名醫治法", "治病要穴", "艾葉", "二伏兔", "小商", "絲竹",
}

forbidden = [p for p in pts if p["moxa_forbidden"]]
print(f"标禁灸条目: {len(forbidden)}\n")

real, junk, conflicting = [], [], []
for p in forbidden:
    n = p["name"]
    if n in NOT_POINTS:
        junk.append(p)
        continue
    t = p.get("text", "")
    # conflicting if the entry ALSO carries a positive moxa cone count
    has_positive = bool(p["moxa_cones"])
    # find the sentence around 禁灸
    m = re.search(r".{0,30}禁灸.{0,30}", t)
    snippet = m.group(0) if m else ""
    (conflicting if has_positive else real).append((p, snippet, has_positive))

print("=" * 72)
print("A. 非穴位条目（章节标题/药名/解析噪声）→ 应剔除")
print("=" * 72)
for p in junk:
    print(f"  {p['name']:8s} | {p.get('text','')[:70]}")

print()
print("=" * 72)
print("B. 典籍有分歧（既标禁灸、又载灸N壮）→ 需人工判读")
print("=" * 72)
for p, snip, _ in conflicting:
    print(f"  {p['name']:8s} 灸={p['moxa_cones']}")
    print(f"           …{snip}…")

print()
print("=" * 72)
print("C. 明确禁灸（无正向灸数）→ 可信")
print("=" * 72)
for p, snip, _ in real:
    print(f"  {p['name']:8s} …{snip[:78]}…")

print()
print(f"小结: 噪声 {len(junk)} / 分歧 {len(conflicting)} / 明确 {len(real)}")
