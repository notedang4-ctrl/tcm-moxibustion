#!/usr/bin/env python3
"""v3 (final): curated moxa_forbidden data for the skill."""
import json
import re
from pathlib import Path

DATA = Path("/root/.hermes/skills/tcm-moxibustion/data")
pts = json.loads((DATA / "acupoints.json").read_text(encoding="utf-8"))

NOISE = {
    "名醫治法": "章节标题（非穴位）",
    "治病要穴": "章节标题（非穴位）",
    "艾葉": "药名（艾叶，非穴位）",
    "二伏兔": "编号误切（应为「伏兔」，已单列）",
    "小商": "形近误字（应为「少商」，已单列）",
    "絲竹": "截断名（应为「絲竹空」，已单列）",
}

SOURCES = ["銅人", "明堂", "素註", "素問", "甲乙", "下經", "千金", "資生",
           "外臺", "聖濟", "聚英", "醫學入門", "東垣", "丹溪"]
POS_RE = re.compile(r"灸\s*([一二三四五六七八九十百\d]+)\s*[壯壮]")
# a consequence must stop before any further instruction
CUT = re.compile(r"(銅人|明堂|素註|素問|甲乙|下經|千金|資生|外臺|聖濟|聚英|醫學入門|東垣|丹溪|針|主|或|又|一名)")


def attribute(t: str, idx: int):
    clause = t[max(0, idx - 90): idx]
    found = [(clause.rfind(s), s) for s in SOURCES]
    found = [(p, s) for p, s in found if p != -1]
    found.sort()
    return [s for _, s in found][-2:]


def consequence(t: str, idx: int) -> str:
    after = t[idx + 2: idx + 50]
    after = re.split(r"[。；;]", after)[0]
    m = CUT.search(after)
    if m:
        after = after[:m.start()]
    after = after.strip(" ，,、）)之令人")
    # drop pure needle-dose artefacts
    if re.search(r"\d|[一二三四五六七八九十]+分", after):
        return ""
    return after[:36] if len(after) >= 3 else ""


def classify(p):
    name = p["name"]
    if name in NOISE:
        return {"name": name, "kind": "noise", "reason": NOISE[name]}
    t = p.get("text", "")
    m = re.search("禁灸", t)
    if not m:
        return None
    idx = m.start()
    base = {"name": name, "forbidden_by": attribute(t, idx) or ["针灸大成（未细分注家）"]}
    if POS_RE.findall(t):
        return {**base, "kind": "disputed", "also_moxa_cones": POS_RE.findall(t)[:4],
                "note": "同一条目内既见「禁灸」又见「灸N壮」，系不同典籍分歧，须专业判读"}
    return {**base, "kind": "forbidden", "consequence": consequence(t, idx), "excerpt": t[:200]}


items = [c for c in (classify(p) for p in pts) if c]
forbidden = sorted([i for i in items if i["kind"] == "forbidden"], key=lambda x: x["name"])
disputed = sorted([i for i in items if i["kind"] == "disputed"], key=lambda x: x["name"])

out = {
    "meta": {
        "source": "《针灸大成》卷八/九/十/十一（明·杨继洲），维基文库公版",
        "warning": "禁灸记载在各典籍间存在分歧，已分类；本文件为文献检索用，非临床禁忌标准",
        "counts": {"forbidden": len(forbidden), "disputed": len(disputed), "noise_dropped": len(NOISE)},
    },
    "forbidden": forbidden,
    "disputed": disputed,
    "noise_dropped": [{"name": k, "reason": v} for k, v in sorted(NOISE.items())],
}
(DATA / "moxa_forbidden.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

print(f"明确禁灸 {len(forbidden)} / 典籍分歧 {len(disputed)} / 记录剔除噪声 {len(NOISE)}\n")
for i in forbidden:
    c = i["consequence"] or "—"
    print(f"  {i['name']:6s} {'/'.join(i['forbidden_by']):22s} {c}")
print()
for i in disputed:
    print(f"  {i['name']:6s} {'/'.join(i['forbidden_by']):22s} 另有灸{i['also_moxa_cones']}")
