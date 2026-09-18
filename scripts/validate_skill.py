#!/usr/bin/env python3
"""Final validation for tcm-moxibustion skill (incl. simplified-Chinese layer)."""
import json
import re
import subprocess
import sys
from pathlib import Path

SK = Path(__file__).resolve().parent.parent
DATA = SK / "data"
PUA = re.compile(r"[\ue000-\uf8ff]")

# 真正「简繁相异」的字（同形字如 髎臑髀髃郄膻膈膏肓腑 不计入，否则假阳性）
TRAD_ONLY = set("腎氣關門谿陽陰衝會經絡脈澤淵闕靈臺風頭頸項犢厲鳩攢顴頷顱齗譩"
                "熱發實虛腫脹濕溫補瀉針壯數醫藥證體臟腸膽學說讀寫電腦網點線圖書"
                "報張開閉與國")

ok = True


def check(label, cond, detail=""):
    global ok
    if not cond:
        ok = False
    print(f"  {'✅' if cond else '❌'} {label}{(' — ' + detail) if detail else ''}")


def run(*args):
    return subprocess.run([sys.executable, str(SK / "scripts" / "query.py"), *args],
                          capture_output=True, text=True, timeout=90)


print("=" * 70)
print("tcm-moxibustion 最终验证")
print("=" * 70)

print("\n[1] 文件完整性")
for rel in ["SKILL.md", "references/01-moxa-methods.md",
            "references/02-safety-contraindications.md",
            "references/03-classical-sources.md", "data/acupoints.json",
            "data/symptoms.json", "data/moxa_forbidden.json", "scripts/query.py"]:
    check(rel, (SK / rel).exists())

print("\n[2] 数据规模")
pts = json.loads((DATA / "acupoints.json").read_text(encoding="utf-8"))
sym = json.loads((DATA / "symptoms.json").read_text(encoding="utf-8"))
fb = json.loads((DATA / "moxa_forbidden.json").read_text(encoding="utf-8"))
check("穴位库 451 条", len(pts) == 451, f"实际 {len(pts)}")
check("症状分类 15 类", len(sym) == 15, f"实际 {len(sym)}")
check("禁灸分类存在", len(fb["forbidden"]) > 0 and len(fb["disputed"]) > 0,
      f"明确 {len(fb['forbidden'])} / 分歧 {len(fb['disputed'])}")
check("噪声剔除有审计记录", len(fb["noise_dropped"]) > 0, f"{len(fb['noise_dropped'])} 条")

print("\n[3] 非穴位噪声已清理")
noise = [p["name"] for p in pts if p["name"].startswith("灸") or "灸法" in p["name"]]
check("无「灸XX」治法条目", not noise, f"残留 {noise}" if noise else "")
prose = [p["name"] for p in pts if re.search(r"之|為|者|其|所|故", p["name"])]
check("无散文片段", not prose, f"残留 {prose}" if prose else "")
for r in ["神闕", "腎俞", "風池", "印堂"]:
    check(f"被剔除条目引用的真实穴「{r}」仍在", r in {p["name"] for p in pts})

print("\n[4] 无残留私用区字符（PUA）")
for f in DATA.glob("*.json"):
    n = len(PUA.findall(f.read_text(encoding="utf-8")))
    check(f.name, n == 0, f"{n} 处")

print("\n[5] 简体层完整性")
miss = [p["name"] for p in pts if not p.get("name_s")]
check("穴名均有简体字段", not miss, f"缺 {len(miss)}")
bad = [(p["name"], p["name_s"]) for p in pts
       if any(c in TRAD_ONLY for c in p["name_s"])]
check("简体字段无残留繁体", not bad, f"{len(bad)} 条: {bad[:3]}")
check("定位有简体字段", all("location_s" in p for p in pts))
fbm = [i["name"] for i in fb["forbidden"] + fb["disputed"] if not i.get("forbidden_by_s")]
check("禁灸出处有简体字段", not fbm, f"缺 {len(fbm)}")
# 中医专有字修正
t2s = {p["name"]: p["name_s"] for p in pts}
check("谿→溪 修正", t2s.get("太谿") == "太溪", f"太谿→{t2s.get('太谿')}")
check("齗交→龈交 修正", t2s.get("齗交") == "龈交", f"齗交→{t2s.get('齗交')}")
check("腎俞→肾俞", t2s.get("腎俞") == "肾俞")
check("氣海→气海", t2s.get("氣海") == "气海")

print("\n[6] 关键穴位齐全")
KEY = ["氣海", "腎俞", "關元", "命門", "太谿", "湧泉", "足三里", "三陰交",
       "中脘", "太衝", "委中", "神闕", "肝俞", "陽陵泉"]
have = {p["name"] for p in pts}
m = [k for k in KEY if k not in have]
check("14 个关键穴位", not m, f"缺 {m}" if m else "14/14")

print("\n[7] 委中禁灸断言（防回归）")
check("委中标记禁灸", any(p["name"] == "委中" for p in fb["forbidden"]))

print("\n[8] query.py — 简体输入")
for args, expect in [(["symptom", "脚冷"], "脚冷"), (["symptom", "腰痛"], "腰痛"),
                     (["point", "肾俞"], "肾俞"), (["forbidden"], "委中"),
                     (["symptom-list"], "分类"), (["point-list", "脐"], "穴位"),
                     (["moxa-list"], "壮")]:
    r = run(*args)
    check(f"query.py {' '.join(args)}", r.returncode == 0 and expect in r.stdout,
          f"rc={r.returncode}")

print("\n[9] query.py — 繁体输入仍可用")
for args, expect in [(["point", "腎俞"], "肾俞"), (["symptom", "腳冷"], "脚冷")]:
    r = run(*args)
    check(f"query.py {' '.join(args)}", r.returncode == 0 and expect in r.stdout)

print("\n[10] --trad 输出繁体原文")
r = run("point", "肾俞", "--trad")
check("--trad 保留繁体", "腎俞" in r.stdout and "銅人" in r.stdout)

print("\n[11] 简体输出无繁体残留（抽查输出文本）")
r = run("point", "气海")
check("气海输出为简体", "氣海" not in r.stdout.replace("繁体：氣海", ""))

print("\n[12] 安全内容存在")
safety = (SK / "references" / "02-safety-contraindications.md").read_text(encoding="utf-8")
for kw in ["糖尿病", "孕妇", "红旗", "就医", "水泡"]:
    check(f"安全文档含「{kw}」", kw in safety)

print("\n[13] 文档为简体（03 例外：含原文繁体对照表）")
for name in ["SKILL.md", "references/01-moxa-methods.md",
             "references/02-safety-contraindications.md"]:
    t = (SK / name).read_text(encoding="utf-8")
    hits = sorted({c for c in t if c in TRAD_ONLY})
    check(name, not hits, f"残留 {hits[:8]}" if hits else "")

print("\n[14] frontmatter 完好")
sm = (SK / "SKILL.md").read_text(encoding="utf-8")
check("以 --- 开头", sm.startswith("---\n"))
check("含 name 字段", "\nname: tcm-moxibustion\n" in sm)
check("含 description 字段", "\ndescription: " in sm)

print("\n[15] 文档数字与数据一致（防文档飘移）")
n_pts = len(pts)
n_cones = sum(1 for p in pts if p["moxa_cones"])
src = (SK / "references" / "03-classical-sources.md").read_text(encoding="utf-8")
check(f"03 文件穴位数=实际 {n_pts}", f"**{n_pts}** 条" in src,
      "未找到匹配数字" if f"**{n_pts}** 条" not in src else "")
check(f"03 文件灸壮数=实际 {n_cones}", f"**{n_cones}** 条" in src,
      "未找到匹配数字" if f"**{n_cones}** 条" not in src else "")
check("SKILL.md 穴位数=实际", f"{n_pts} 个穴位" in sm)
ver_skill = next((l for l in sm.split("\n") if l.startswith("version:")), "")
ver_cl = (SK / "CHANGELOG.md").read_text(encoding="utf-8")
top = re.search(r"^## \[([0-9.]+)\]", ver_cl, re.M)
v_num = ver_skill.replace("version:", "").strip()
check(f"版本三元同步 ({v_num})", top and top.group(1) == v_num,
      f"SKILL.md={v_num} CHANGELOG={top.group(1) if top else '?'}")

print("\n" + "=" * 70)
print("结果:", "全部通过 ✅" if ok else "存在失败项 ❌")
print("=" * 70)
sys.exit(0 if ok else 1)
