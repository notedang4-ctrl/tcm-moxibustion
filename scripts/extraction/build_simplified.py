#!/usr/bin/env python3
"""Pre-compute simplified (简体) variants for every string in the skill data.

Why pre-compute instead of converting at runtime:
  - opencc is phrase-aware (better quality than a char-by-char table)
  - the skill stays dependency-free (标准库 only), which matters on this host
  - conversion happens once, results are auditable and diffable

TCM-specific overrides are needed because opencc's generic t2s dictionary
misses a few acupoint conventions (see SUPPLEMENTS).
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, "/tmp/occdir")
from opencc import OpenCC  # noqa: E402

DATA = Path("/root/.hermes/skills/tcm-moxibustion/data")
cc = OpenCC("t2s")

# opencc t2s misses these TCM conventions
SUPPLEMENTS = [
    ("谿", "溪"),    # 太谿→太溪, 後谿→后溪（简化通行作「溪」）
    ("龂", "龈"),    # 齗交→龈交
    ("𫍻", "譆"),    # opencc 误转，回退
    ("籥", "钥"),
]


def s(text: str) -> str:
    if not isinstance(text, str):
        return text
    out = cc.convert(text)
    for a, b in SUPPLEMENTS:
        out = out.replace(a, b)
    return out


def add_variants(obj, fields):
    """For each dict item, add '<field>_s' simplified variants."""
    if isinstance(obj, dict):
        for f in fields:
            if isinstance(obj.get(f), str):
                obj[f + "_s"] = s(obj[f])
        for v in obj.values():
            if isinstance(v, (dict, list)):
                add_variants(v, fields)
    elif isinstance(obj, list):
        for v in obj:
            add_variants(v, fields)


report = {}

# --- acupoints ---
f = DATA / "acupoints.json"
pts = json.loads(f.read_text(encoding="utf-8"))
for p in pts:
    p["name_s"] = s(p["name"])
    p["location_s"] = s(p.get("location", ""))
    p["text_s"] = s(p.get("text", ""))
f.write_text(json.dumps(pts, ensure_ascii=False, indent=1), encoding="utf-8")
report["acupoints.json"] = len(pts)

# --- symptoms ---
f = DATA / "symptoms.json"
sym = json.loads(f.read_text(encoding="utf-8"))
n = 0
for k, d in sym.items():
    for p in d.get("passages", []):
        p["ctx_s"] = s(p["ctx"])
        n += 1
f.write_text(json.dumps(sym, ensure_ascii=False, indent=1), encoding="utf-8")
report["symptoms.json"] = n

# --- forbidden ---
f = DATA / "moxa_forbidden.json"
fb = json.loads(f.read_text(encoding="utf-8"))
n = 0
for key in ("forbidden", "disputed"):
    for i in fb.get(key, []):
        i["name_s"] = s(i["name"])
        i["excerpt_s"] = s(i.get("excerpt", ""))
        if i.get("consequence"):
            i["consequence_s"] = s(i["consequence"])
        n += 1
f.write_text(json.dumps(fb, ensure_ascii=False, indent=1), encoding="utf-8")
report["moxa_forbidden.json"] = n

print("已写入简体变体:")
for k, v in report.items():
    print(f"  {k:24s} {v} 条")

print("\n=== 抽查穴位名转换 ===")
for p in pts[:0] or []:
    pass
for name in ("腎俞", "氣海", "太谿", "後谿", "關元", "陽陵泉", "齗交", "肩髃", "臑會"):
    hit = [p for p in pts if p["name"] == name]
    if hit:
        print(f"  {name:6s} -> {hit[0]['name_s']}")
