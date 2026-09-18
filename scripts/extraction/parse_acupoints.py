#!/usr/bin/env python3
"""Parse classical acupoint entries (name / location / needle / moxa dosage / indications).

Sources:
  卷八 考正穴法 (针灸大成)  -> 穴名（别名）定位。铜人针X灸Y。主...
  卷十 神应经 (针灸大成)     -> 穴名 定位，针X，灸Y壮，...
"""
import json
import re
from pathlib import Path

CLEAN = Path("/tmp/tcm-src/clean")

CN_NUM = {"一":1,"二":2,"三":3,"四":4,"五":5,"六":6,"七":7,"八":8,"九":9,"十":10,
          "十一":11,"十二":12,"十四":14,"十六":16,"十八":18,"二十":20,"廿":20,
          "三七":21,"二七":14,"七七":49,"五七":35,"四七":28,"六六":36,"三三":9}


def cn2int(s: str):
    """Best-effort Chinese numeral -> int for moxa cone counts."""
    s = s.strip()
    if s in CN_NUM:
        return CN_NUM[s]
    if s.isdigit():
        return int(s)
    # forms like 二七 / 三七 handled by table; try digit-mix
    m = re.fullmatch(r"([一二三四五六七八九十]+)([一二三四五六七八九十]*)", s)
    if not m:
        return None
    return CN_NUM.get(s)


def split_entries(text: str):
    """Yield (name, body) chunks. An entry starts at line begin with a short name token."""
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    cur_name, cur = None, []
    for ln in lines:
        # entry name: 2-6 CJK chars at line start, followed by space or 在/（
        m = re.match(r"^([\u4e00-\u9fff]{2,7})(?:\s|（|在|一名)", ln)
        if m and "。" not in ln[:len(m.group(1))]:
            name = m.group(1)
            # guard: skip obvious prose starts
            if name not in ("主治", "銅人", "素註", "明堂", "甲乙", "東垣", "丹溪", "一云", "按", "又"):
                if cur_name:
                    yield cur_name, "".join(cur)
                cur_name, cur = name, [ln]
                continue
        if cur_name:
            cur.append(ln)
    if cur_name:
        yield cur_name, "".join(cur)


MOXA_RE = re.compile(r"灸\s*([一二三四五六七八九十百\d]+)\s*壯|灸\s*([一二三四五六七八九十百\d]+)\s*壮")
NOCAUTERY_RE = re.compile(r"禁灸|不可灸|不宜灸")


def parse(path: Path):
    out = []
    for name, body in split_entries(path.read_text(encoding="utf-8")):
        cones = MOXA_RE.findall(body)
        cones = [c[0] or c[1] for c in cones if (c[0] or c[1])]
        no_moxa = bool(NOCAUTERY_RE.search(body))
        # location heuristic: text between name and first 針/灸
        loc = re.split(r"針|灸|主", body[len(name):], maxsplit=1)[0]
        loc = re.sub(r"^[\s（(一名)】]*", "", loc)[:60]
        out.append({
            "name": name,
            "location": loc.strip(" 。，,、"),
            "moxa_cones": cones[:4],
            "moxa_forbidden": no_moxa,
            "source": path.stem,
            "raw": body[:400],
        })
    return out


allp = []
for f in ("zjdc_八.txt", "zjdc_九.txt", "zjdc_十.txt", "zjdc_十一.txt"):
    got = parse(CLEAN / f)
    print(f"{f}: {len(got)} entries")
    allp += got

# dedupe by name, prefer 卷八 (考正穴法, richer)
by = {}
for e in allp:
    k = e["name"]
    if k not in by or (e["source"] == "zjdc_八" and by[k]["source"] != "zjdc_八"):
        by[k] = e

Path("/tmp/tcm-src/acupoints_raw.json").write_text(
    json.dumps(list(by.values()), ensure_ascii=False, indent=1), encoding="utf-8")

print(f"\n去重后穴位条目: {len(by)}")
print(f"有灸壮数的: {sum(1 for e in by.values() if e['moxa_cones'])}")
print(f"明确禁灸的: {sum(1 for e in by.values() if e['moxa_forbidden'])}")
print("\n样例:")
for e in list(by.values())[:8]:
    print(f"  {e['name']:6s} 灸={e['moxa_cones']} 禁灸={e['moxa_forbidden']} | {e['location'][:34]}")
