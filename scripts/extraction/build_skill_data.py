#!/usr/bin/env python3
"""Clean the acupoint list and emit skill data files."""
import json
import re
from pathlib import Path


# --- workspace / data paths (override via env) -------------------------------
import os as _os

_HERE = Path(__file__).resolve()
SKILL_ROOT = _HERE.parents[2]      # scripts/extraction/x.py -> skill root
DATA = Path(_os.environ.get("TCM_DATA", str(SKILL_ROOT / "data")))
WORKSPACE = Path(_os.environ.get("TCM_WORKSPACE", "/tmp/tcm-src"))
# -----------------------------------------------------------------------------


RAW = json.loads((WORKSPACE / "acupoints_raw.json").read_text(encoding="utf-8"))
SYM = json.loads((WORKSPACE / "symptom_index.json").read_text(encoding="utf-8"))

# names that are section headings / prose, not acupoints
BAD = re.compile(r"歌|經穴|主治|其治|上焦|中焦|下焦|穴法|論|圖|序|一云|按|又|凡|右|左|內|外景|分寸|骨度|五臟|六腑")

points = []
for e in RAW:
    n = e["name"]
    if BAD.search(n) or len(n) < 2 or len(n) > 4:
        continue
    if not (e["location"] or e["moxa_cones"] or e["raw"]):
        continue
    points.append({
        "name": n,
        "location": e["location"],
        "moxa_cones": e["moxa_cones"],
        "moxa_forbidden": e["moxa_forbidden"],
        "source": e["source"],
        "text": e["raw"][:300],
    })

# de-dup again after cleaning
seen, uniq = set(), []
for p in points:
    if p["name"] in seen:
        continue
    seen.add(p["name"])
    uniq.append(p)

uniq.sort(key=lambda p: p["name"])

# key points the symptom index points to -- make sure they exist
KEY = ["氣海", "腎俞", "肝俞", "太谿", "神闕", "關元", "命門", "足三里", "三陰交",
       "湧泉", "委中", "中脘", "大椎", "膏肓", "陽陵泉", "百會", "太衝", "脾俞", "胃俞"]
have = {p["name"] for p in uniq}
print("穴位库总数:", len(uniq))
print("有灸壮数:", sum(1 for p in uniq if p["moxa_cones"]))
print("标禁灸:", sum(1 for p in uniq if p["moxa_forbidden"]))
print("\n关键穴位覆盖:")
for k in KEY:
    print(f"  {k:6s} {'✅' if k in have else '❌ 缺失'}")

outdir = (WORKSPACE / "skill-data")
outdir.mkdir(exist_ok=True)
(outdir / "acupoints.json").write_text(json.dumps(uniq, ensure_ascii=False, indent=1), encoding="utf-8")
(outdir / "symptoms.json").write_text(json.dumps(SYM, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"\n写出: {outdir}/acupoints.json ({len(uniq)}) / symptoms.json ({len(SYM)} 症状)")
