#!/usr/bin/env python3
"""v2: attribute each 禁灸 to the nearest preceding classical text name in the
same sentence, and clean up the stated consequence."""
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

SOURCES = ["銅人", "明堂", "素註", "素問", "甲乙", "下經", "千金", "資生", "外臺", "聖濟", "聚英", "醫學入門", "東垣", "丹溪"]
POS_RE = re.compile(r"灸\s*([一二三四五六七八九十百\d]+)\s*[壯壮]")


def attribute(t: str, idx: int) -> list[str]:
    """Nearest source names appearing before the 禁灸 position, within the clause."""
    clause = t[max(0, idx - 90): idx]
    found = []
    for s in SOURCES:
        p = clause.rfind(s)
        if p != -1:
            found.append((p, s))
    if not found:
        return []
    found.sort()
    # keep sources in the same clause, nearest first
    return [s for _, s in found][-2:]


def consequence(t: str, idx: int) -> str:
    after = t[idx + 2: idx + 46]
    after = re.split(r"[。；;]", after)[0].strip(" ，,、）)")
    # keep only if it actually describes harm/effect
    if re.match(r"^(灸|針|刺|主|[，,、])", after) or len(after) < 3:
        after = after.lstrip("灸針刺")
        after = after.lstrip("之令人")
    if re.search(r"(令人|使人|生|傷|壞|失|盲|啞|傴|夭|死|不可|不宜)", after) or "灸" in t[idx:idx+30]:
        return after[:40]
    return ""


def classify(p):
    name = p["name"]
    if name in NOISE:
        return {"name": name, "kind": "noise", "reason": NOISE[name]}

    t = p.get("text", "")
    m = re.search(",?禁灸", t)
    if not m:
        return None
    idx = m.start()

    forbidders = attribute(t, idx)
    positives = POS_RE.findall(t)

    base = {"name": name, "forbidden_by": forbidders or ["针灸大成（未细分注家）"]}
    if positives:
        return {**base, "kind": "disputed", "also_moxa_cones": positives[:4],
                "note": "同一条目内既见「禁灸」又见「灸N壮」，系不同典籍分歧",
                "excerpt": t[:220]}
    return {**base, "kind": "forbidden", "consequence": consequence(t, idx), "excerpt": t[:200]}


items = [c for c in (classify(p) for p in pts) if c]
forbidden = sorted([i for i in items if i["kind"] == "forbidden"], key=lambda x: x["name"])
disputed = sorted([i for i in items if i["kind"] == "disputed"], key=lambda x: x["name"])
noise = sorted([i for i in items if i["kind"] == "noise"], key=lambda x: x["name"])

out = {
    "meta": {
        "source": "《针灸大成》卷八/卷九/卷十/卷十一（明·杨继洲），维基文库公版",
        "warning": "禁灸记载在各典籍（铜人/明堂/素注/甲乙等）间存在分歧，已分类，勿混用",
        "counts": {"forbidden": len(forbidden), "disputed": len(disputed), "noise_dropped": len(noise)},
    },
    "forbidden": forbidden,
    "disputed": disputed,
    "noise_dropped": noise,
}
(DATA / "moxa_forbidden.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

print(f"禁灸: 明确 {len(forbidden)} / 分歧 {len(disputed)} / 噪声剔除 {len(noise)}\n")
print("=== 明确禁灸（含出处与后果）===")
for i in forbidden:
    print(f"  {i['name']:6s} 出处:{'/'.join(i['forbidden_by']):28s} 后果: {i['consequence'][:30]}")
print("\n=== 典籍分歧 ===")
for i in disputed:
    print(f"  {i['name']:6s} 禁灸于:{'/'.join(i['forbidden_by']):22s} 另有灸{i['also_moxa_cones']}")
