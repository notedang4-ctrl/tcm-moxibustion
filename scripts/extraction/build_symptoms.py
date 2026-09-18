#!/usr/bin/env python3
"""Build a symptom -> acupoint index from the cleaned classical corpus.

Focus: moxibustion-relevant (cold/deficiency patterns) conditions.
Each hit keeps the classical sentence so nothing is invented.
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


CLEAN = (WORKSPACE / "clean")

# symptom -> search terms (traditional forms as they appear in the texts)
SYMPTOMS = {
    "脚冷/手足冰凉": ["四逆", "厥冷", "足冷", "腳冷", "手足冷", "手足寒", "足脛寒"],
    "腰痛/腰酸/肾虚": ["腰痛", "腰疼", "腰重", "腰脊", "腎敗腰疼", "腎弱腰疼"],
    "胃寒/胃痛/腹胀": ["胃寒", "胃痛", "心腹痛", "腹脹", "胃冷", "中脘"],
    "腹泻/久泄": ["泄瀉", "下利", "洞泄", "冷痢", "飱泄"],
    "宫寒/痛经/月经": ["痛經", "經行", "崩漏", "帶下", "胞寒", "子宮"],
    "失眠/多梦": ["失眠", "不寐", "不得臥", "多夢", "健忘"],
    "咳嗽/哮喘/痰": ["咳嗽", "哮喘", "氣喘", "痰飲", "久咳", "喘"],
    "体虚/易感冒/气虚": ["虛勞", "羸瘦", "氣虛", "自汗", "盜汗", "虛損"],
    "关节冷痛/风湿": ["冷痺", "風濕", "痺痛", "歷節", "骨痺"],
    "夜尿/尿频/遗尿": ["遺尿", "小便頻", "頻數", "夜尿", "遺精"],
    "疲劳/阳虚体质": ["陽虛", "陽衰", "真氣", "元氣", "補陽"],
    "头痛/头晕": ["頭痛", "眩暈", "頭重"],
    "肩颈/背痛": ["肩背", "項強", "頸", "肩膊"],
    "发背/痈疽/疮": ["發背", "癰疽", "瘡", "腫毒"],
    "中风/急救": ["中風", "不省人事", "猝死", "屍厥", "中暑"],
}

WINDOW = 110
MAX_PER_SYMPTOM = 8


def passages(term: str):
    out = []
    for f in sorted(CLEAN.glob("*.txt")):
        t = f.read_text(encoding="utf-8")
        for m in re.finditer(re.escape(term), t):
            s, e = max(0, m.start() - WINDOW), min(len(t), m.end() + WINDOW)
            ctx = t[s:e].replace("\n", "")
            out.append({"source": f.stem, "term": term, "ctx": ctx})
    return out


index = {}
for sym, terms in SYMPTOMS.items():
    hits, seen = [], set()
    for term in terms:
        for p in passages(term):
            key = p["ctx"][:60]
            if key in seen:
                continue
            seen.add(key)
            p["has_moxa"] = "灸" in p["ctx"]
            hits.append(p)
    # moxibustion-bearing passages first - that is this skill's focus
    hits.sort(key=lambda x: (not x["has_moxa"],))
    with_moxa = [h for h in hits if h["has_moxa"]]
    index[sym] = {"terms": terms, "total_hits": len(hits),
                  "moxa_hits": len(with_moxa),
                  "passages": (with_moxa or hits)[:MAX_PER_SYMPTOM]}

(WORKSPACE / "symptom_index.json").write_text(
    json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")

print(f"{'症状':22s} {'总命中':>6s} {'带灸法':>7s}")
print("-" * 40)
for sym, d in index.items():
    print(f"{sym:22s} {d['total_hits']:6d} {d['moxa_hits']:7d}")

print("\n\n=== 样例：脚冷/手足冰凉（带灸法）===")
for p in index["脚冷/手足冰凉"]["passages"][:4]:
    print(f"[{p['source']}] {p['ctx'][:190]}")
