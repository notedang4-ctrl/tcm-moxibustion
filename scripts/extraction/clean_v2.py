#!/usr/bin/env python3
"""Clean remaining parser noise from the acupoint list and add missing
simplified variants (forbidden_by), then re-verify."""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, "/tmp/occdir")
from opencc import OpenCC

DATA = Path("/root/.hermes/skills/tcm-moxibustion/data")
cc = OpenCC("t2s")
SUPP = [("谿", "溪"), ("龂", "龈"), ("𫍻", "譆")]


def s(t):
    if not isinstance(t, str):
        return t
    o = cc.convert(t)
    for a, b in SUPP:
        o = o.replace(a, b)
    return o


# --- 1. remove non-acupoint noise ---
PROSE = re.compile(r"之|為|者|其|所|故|皆|則")
pts = json.loads((DATA / "acupoints.json").read_text(encoding="utf-8"))

removed = []
keep = []
for p in pts:
    n = p["name"]
    if n.startswith("灸") or "灸法" in n:
        removed.append((n, "治法条目/章节标题（非穴名）"))
        continue
    if PROSE.search(n):
        removed.append((n, "散文片段（非穴名）"))
        continue
    keep.append(p)

print(f"穴位库: {len(pts)} -> {len(keep)}（剔除 {len(removed)} 条）")
for n, why in removed:
    print(f"  剔除 {n:8s} {why}")

# 确认被剔除条目引用的真实穴位仍在
refs = ["神闕", "腎俞", "風池", "印堂", "大杼"]
have = {p["name"] for p in keep}
print("\n被剔除条目引用的真实穴位是否仍在库中:")
for r in refs:
    print(f"  {r:6s} {'✅ 在' if r in have else '❌ 丢失'}")

# --- 2. ensure simplified variants present for all fields ---
for p in keep:
    p["name_s"] = p.get("name_s") or s(p["name"])
    p["location_s"] = s(p.get("location", ""))
    p["text_s"] = s(p.get("text", ""))

(DATA / "acupoints.json").write_text(
    json.dumps(keep, ensure_ascii=False, indent=1), encoding="utf-8")

# --- 3. forbidden_by simplified ---
f = DATA / "moxa_forbidden.json"
fb = json.loads(f.read_text(encoding="utf-8"))
for key in ("forbidden", "disputed"):
    for i in fb.get(key, []):
        i["name_s"] = i.get("name_s") or s(i["name"])
        i["forbidden_by_s"] = [s(x) for x in (i.get("forbidden_by") or [])]
        i["excerpt_s"] = s(i.get("excerpt", ""))
        if i.get("consequence"):
            i["consequence_s"] = s(i["consequence"])
f.write_text(json.dumps(fb, ensure_ascii=False, indent=1), encoding="utf-8")

# --- 4. verify no traditional-only chars remain in name_s ---
TRAD_ONLY = set("腎氣關門谿陽陰衝會經絡脈澤淵髎闕靈臺風頭頸項臑髀犢髃郄厲鳩攢"
                "膻顴頷顱齗譩熱發實虛腫脹濕溫補瀉針壯數醫藥證體臟腑腸膽"
                "東與國學說讀寫電腦網點線畫圖書報紙張開閉")
leftover = [(p["name"], p["name_s"]) for p in keep if any(c in TRAD_ONLY for c in p["name_s"])]
print(f"\n简体字段残留繁体字: {len(leftover)} 条")
for t, ss in leftover[:10]:
    print(f"  {t} -> {ss}")

print(f"\n最终穴位库: {len(keep)} 条")
print(f"  有灸壮数: {sum(1 for p in keep if p['moxa_cones'])}")
print(f"  标禁灸  : {sum(1 for p in keep if p['moxa_forbidden'])}")
