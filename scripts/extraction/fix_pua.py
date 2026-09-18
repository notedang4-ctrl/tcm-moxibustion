#!/usr/bin/env python3
"""Strip Unicode Private-Use-Area chars (U+E000-U+F8FF) left behind when the
wikisource font lacked a glyph, and report the damage per file.

PUA chars are not real text: they render as tofu and would silently corrupt
queries. We replace them with a visible marker so the loss is auditable.
"""
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



PUA = re.compile(r"[\ue000-\uf8ff]")

MARK = "□"  # visible marker for a lost glyph


def clean_str(s: str):
    if not isinstance(s, str):
        return s, 0
    n = len(PUA.findall(s))
    return PUA.sub(MARK, s), n


def walk(obj):
    total = 0
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, (dict, list)):
                total += walk(v)
            elif isinstance(v, str):
                obj[k], n = clean_str(v)
                total += n
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            if isinstance(v, (dict, list)):
                total += walk(v)
            elif isinstance(v, str):
                obj[i], n = clean_str(v)
                total += n
    return total


report = {}
for f in sorted(DATA.glob("*.json")):
    d = json.loads(f.read_text(encoding="utf-8"))
    n = walk(d)
    f.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    report[f.name] = n

print(f"{'文件':26s} {'PUA缺字':>8s}")
print("-" * 36)
for k, v in report.items():
    print(f"{k:26s} {v:8d}")
print(f"{'合计':26s} {sum(report.values()):8d}")

# also clean the extracted symptom corpus (used to rebuild passages)
CLEAN = (WORKSPACE / "clean")
tot = 0
for f in sorted(CLEAN.glob("*.txt")):
    t = f.read_text(encoding="utf-8")
    n = len(PUA.findall(t))
    if n:
        f.write_text(PUA.sub(MARK, t), encoding="utf-8")
    tot += n
print(f"\n古籍 corpus 清理: {tot} 处缺字已标记")
