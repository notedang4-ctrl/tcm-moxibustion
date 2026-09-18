#!/usr/bin/env python3
"""tcm-moxibustion 查询脚本（仅标准库，无运行时依赖）

用法：
  python3 query.py symptom 脚冷          # 症状 → 穴位（含古文献原文）
  python3 query.py symptom-list          # 列出所有症状分类
  python3 query.py point 肾俞 气海        # 穴位详情（简体/繁体输入都行）
  python3 query.py point-list [关键词]    # 列出穴位（可按名或定位筛选）
  python3 query.py moxa-list             # 所有带灸壮数的穴位
  python3 query.py forbidden             # 禁灸穴（明确 + 典籍分歧，分类呈现）
  python3 query.py forbidden disputed    # 只看典籍分歧项

  --trad   显示繁体原文（默认显示简体；古籍原文以繁体为准）

数据源：维基文库公版《针灸大成》等（详见 references/03-classical-sources.md）
⚠️ 本工具为古籍文献检索，不构成诊疗建议；施灸前请读 references/02-safety-contraindications.md
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"

# 繁体原文中的引用来源名，作为「定位」字段尾部噪声剔除
SRC_TAIL = re.compile(r"[。，,]?\s*(銅人|铜人|素註|素注|素問|素问|明堂|甲乙|下經|下经|千金|資生|资生|外臺|外台|聖濟|圣济|東垣|东垣|丹溪|難經|难经|聚英|醫學入門|医学入门)[。\s]*$")

# 简体写法 -> 库内症状键
ALIAS = {
    "脚冷": "脚冷/手足冰凉", "腳冷": "脚冷/手足冰凉", "手足冰凉": "脚冷/手足冰凉",
    "手冷": "脚冷/手足冰凉", "四肢冷": "脚冷/手足冰凉", "厥冷": "脚冷/手足冰凉",
    "四肢冰凉": "脚冷/手足冰凉", "脚冰凉": "脚冷/手足冰凉",
    "阳虚": "疲劳/阳虚体质", "阳气虚": "疲劳/阳虚体质", "体寒": "疲劳/阳虚体质",
    "腰痛": "腰痛/腰酸/肾虚", "腰疼": "腰痛/腰酸/肾虚", "腰酸": "腰痛/腰酸/肾虚",
    "肾虚": "腰痛/腰酸/肾虚", "腰": "腰痛/腰酸/肾虚", "腰背痛": "腰痛/腰酸/肾虚",
    "胃寒": "胃寒/胃痛/腹胀", "胃痛": "胃寒/胃痛/腹胀", "腹胀": "胃寒/胃痛/腹胀",
    "胃胀": "胃寒/胃痛/腹胀",
    "拉肚子": "腹泻/久泄", "腹泻": "腹泻/久泄", "泄泻": "腹泻/久泄", "久泄": "腹泻/久泄",
    "痛经": "宫寒/痛经/月经", "宫寒": "宫寒/痛经/月经", "月经": "宫寒/痛经/月经",
    "月经不调": "宫寒/痛经/月经", "带下": "宫寒/痛经/月经",
    "失眠": "失眠/多梦", "睡不着": "失眠/多梦", "多梦": "失眠/多梦", "不寐": "失眠/多梦",
    "咳嗽": "咳嗽/哮喘/痰", "哮喘": "咳嗽/哮喘/痰", "痰": "咳嗽/哮喘/痰",
    "气喘": "咳嗽/哮喘/痰", "久咳": "咳嗽/哮喘/痰",
    "怕冷": "体虚/易感冒/气虚", "体虚": "体虚/易感冒/气虚", "气虚": "体虚/易感冒/气虚",
    "易感冒": "体虚/易感冒/气虚", "自汗": "体虚/易感冒/气虚", "盗汗": "体虚/易感冒/气虚",
    "风湿": "关节冷痛/风湿", "关节痛": "关节冷痛/风湿", "关节冷": "关节冷痛/风湿",
    "冷痹": "关节冷痛/风湿", "老寒腿": "关节冷痛/风湿", "腿冷": "关节冷痛/风湿",
    "夜尿": "夜尿/尿频/遗尿", "尿频": "夜尿/尿频/遗尿", "遗尿": "夜尿/尿频/遗尿",
    "疲劳": "疲劳/阳虚体质", "乏力": "疲劳/阳虚体质", "累": "疲劳/阳虚体质",
    "头痛": "头痛/头晕", "头晕": "头痛/头晕", "眩晕": "头痛/头晕",
    "肩颈": "肩颈/背痛", "颈椎": "肩颈/背痛", "背痛": "肩颈/背痛", "肩膀": "肩颈/背痛",
    "发背": "发背/痈疽/疮", "痈疽": "发背/痈疽/疮", "疮": "发背/痈疽/疮",
    "中风": "中风/急救", "急救": "中风/急救", "中暑": "中风/急救",
}


def load(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def pick(d: dict, field: str, trad: bool) -> str:
    """Simplified field by default; original traditional when trad=True."""
    if trad:
        return d.get(field) or d.get(field + "_s") or ""
    return d.get(field + "_s") or d.get(field) or ""


def tidy_location(s: str) -> str:
    return SRC_TAIL.sub("", s or "").strip(" 。，,")


def parse_flags(argv):
    trad = False
    rest = []
    for a in argv:
        if a in ("--trad", "--繁", "--繁体"):
            trad = True
        else:
            rest.append(a)
    return trad, rest


# ---------------------------------------------------------------- commands

def cmd_symptom_list():
    sym = load("symptoms.json")
    print(f"{'分类':22s} {'古文献命中':>8s} {'其中含灸':>8s}")
    print("-" * 44)
    for k, v in sym.items():
        print(f"{k:22s} {v['total_hits']:8d} {v['moxa_hits']:8d}")
    print("\n提示：也可直接用小写/简体词，如 `query.py symptom 脚冷`")


def cmd_symptom(term: str, trad: bool):
    sym = load("symptoms.json")
    key = term if term in sym else ALIAS.get(term)
    if not key:
        cand = [k for k in sym if term in k or k in term]
        if not cand:
            print(f"未收录症状「{term}」。可用分类：")
            cmd_symptom_list()
            return 1
        key = cand[0]

    d = sym[key]
    print(f"# {key}")
    print(f"（古文献命中 {d['total_hits']} 处，其中含灸法 {d['moxa_hits']} 处）")
    if not trad:
        print("（以下原文由繁体转为简体；如需原始繁体，加 --trad）")
    print()
    for i, p in enumerate(d["passages"], 1):
        flag = "【含灸】" if p.get("has_moxa") else ""
        src = p["source"]
        print(f"--- {i}. {flag} 出处 {src}（关键词「{p['term']}」）")
        print(f"    {pick(p, 'ctx', trad)}\n")
    print("⚠️ 以上为古籍原文摘录，仅供学习参考，不构成诊疗建议。")
    return 0


def cmd_point(names, trad: bool):
    pts = load("acupoints.json")
    by_trad = {p["name"]: p for p in pts}
    by_simp = {}
    for p in pts:
        by_simp.setdefault(p.get("name_s") or p["name"], p)

    for n in names:
        p = by_trad.get(n) or by_simp.get(n)
        if not p:
            cand = [k for k in list(by_trad) + list(by_simp) if n in k]
            if not cand:
                print(f"[{n}] 未收录\n")
                continue
            p = by_trad.get(cand[0]) or by_simp.get(cand[0])

        title = p["name"] if trad else (p.get("name_s") or p["name"])
        alt = "" if trad else f"（繁体：{p['name']}）"
        print(f"# {title}{alt}")
        loc = tidy_location(pick(p, "location", trad))
        if loc:
            print(f"  定位：{loc}")
        if p["moxa_cones"]:
            print(f"  灸壮：{'/'.join(p['moxa_cones'])} 壮")
        print(f"  禁灸：{'是 ⚠️' if p['moxa_forbidden'] else '否'}")
        print(f"  出处：{p['source']}")
        txt = pick(p, "text", trad)
        if txt:
            print(f"  原文：{txt[:260]}")
        print()


def cmd_point_list(kw: str, trad: bool):
    pts = load("acupoints.json")
    def hay(p):
        return " ".join([p["name"], p.get("name_s", ""), p.get("location", ""), p.get("location_s", "")])
    hits = [p for p in pts if (not kw or kw in hay(p))]
    print(f"共 {len(hits)} 个穴位" + (f"（匹配「{kw}」）" if kw else ""))
    shown = 0
    for p in hits:
        name = p["name"] if trad else (p.get("name_s") or p["name"])
        cones = "/".join(p["moxa_cones"]) if p["moxa_cones"] else "-"
        warn = " ⚠️禁灸" if p["moxa_forbidden"] else ""
        print(f"  {name:6s} 灸{cones:>6s}{warn}")
        shown += 1
        if shown >= 80:
            break
    if len(hits) > shown:
        print(f"  … 还有 {len(hits)-shown} 个")


def cmd_moxa_list(trad: bool):
    pts = [p for p in load("acupoints.json") if p["moxa_cones"] and not p["moxa_forbidden"]]
    print(f"有灸壮数且未标禁灸的穴位：{len(pts)} 个\n")
    for p in pts:
        name = p["name"] if trad else (p.get("name_s") or p["name"])
        loc = tidy_location(pick(p, "location", trad))[:40]
        print(f"  {name:6s} {'/'.join(p['moxa_cones']):>6s} 壮  {loc}")


def cmd_forbidden(mode: str, trad: bool):
    d = load("moxa_forbidden.json")
    fb, dp = d.get("forbidden", []), d.get("disputed", [])
    print("古籍禁灸记载（数据源：《针灸大成》）")
    print(f"  明确禁灸 {len(fb)} 穴 / 典籍分歧 {len(dp)} 穴")
    if not trad:
        print("  （默认简体；如需原始繁体，加 --trad）")
    print()

    def by_of(p):
        return "/".join(p.get("forbidden_by_s" if not trad else "forbidden_by")
                        or p.get("forbidden_by") or [])

    if mode != "disputed":
        print("=" * 66)
        print("一、明确禁灸（另无灸量记载）")
        print("=" * 66)
        for p in fb:
            name = p["name"] if trad else (p.get("name_s") or p["name"])
            print(f"  {name:6s} 出处 {by_of(p)}")
            c = pick(p, "consequence", trad)
            if c:
                print(f"         后果：{c}")
        print()

    if mode != "forbidden":
        print("=" * 66)
        print("二、典籍分歧（同条既言禁灸、又载灸N壮）—— 须医师判读，勿自行灸")
        print("=" * 66)
        for p in dp:
            name = p["name"] if trad else (p.get("name_s") or p["name"])
            print(f"  {name:6s} 禁灸于 {by_of(p)}；但同条另有灸 {'/'.join(p.get('also_moxa_cones', []))} 壮")
        print()

    print("⚠️ 禁灸记载在各典籍间存在分歧，本库分类呈现、不代为裁定。")
    print("⚠️ 本清单为文献检索结果，非临床禁忌标准；施灸前请咨询执业医师。")


def main():
    argv = sys.argv[1:]
    if not argv:
        print(__doc__)
        return 0
    trad, rest = parse_flags(argv)
    if not rest:
        print(__doc__)
        return 0

    c, *args = rest
    if c == "symptom":
        return cmd_symptom(args[0], trad) if args else (cmd_symptom_list() or 0)
    if c == "symptom-list":
        cmd_symptom_list()
        return 0
    if c == "point":
        if not args:
            print(__doc__)
            return 1
        cmd_point(args, trad)
        return 0
    if c == "point-list":
        cmd_point_list(args[0] if args else "", trad)
        return 0
    if c == "moxa-list":
        cmd_moxa_list(trad)
        return 0
    if c == "forbidden":
        cmd_forbidden(args[0] if args else "", trad)
        return 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main())
