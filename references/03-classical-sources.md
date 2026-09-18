# 数据出处与提取方法（可复现）

## 1. 数据来源

所有原文取自 **维基文库（zh.wikisource.org）公版古籍**，2026-09-18 抓取。

| 典籍 | 朝代/作者 | 用途 | 原始体量 |
|---|---|---|---|
| 《针灸大成》 | 明·杨继洲 | **主干**。卷八/九「考正穴法」取穴位定位与灸量；卷十「神应经」；卷十一「治症总要」 | 全 12 卷，约 24 万字 |
| 《备急灸法》 | 宋·张涣（孙炬卿刻） | 灸法急救、骑竹马灸法 | 1 卷 |
| 《扁鹊心书》 | 宋·窦材 | 「保命之法，灼艾第一」理论 | 残卷 |
| 《外台秘要》 | 唐·王焘 | 灸法方剂旁证 | 40 卷（选读） |

**为何选这些**：《针灸大成》是明代集大成之作，体例完整（穴名→定位→针法→灸量→主治），且含大量灸法记载（卷十灸密度 16.1‰，为全书之冠），是最适合结构化提取的底本。

## 2. 抓取与提取流程

```
① 抓取      curl 维基文库 HTML（各卷独立页面）
② 清洗      剥离页面导航/编辑链接/版权页，仅留正文（clean.py）
③ 解析      按「穴名 定位，针X，灸Y壮，主…」体例切分条目（parse_acupoints.py）
④ 症状索引  15 类症状的关键词全文检索，保留含灸法的段落（build_symptoms.py）
⑤ 禁灸分类  区分「明确禁灸 / 典籍分歧 / 解析噪声」（curate_forbidden3.py）
⑥ 字符修复  Unicode 私用区(PUA)缺字 → 标记为 □（fix_pua.py）
```

## 3. 产出规模

| 文件 | 内容 | 量 |
|---|---|---|
| `data/acupoints.json` | 穴位条目（定位/灸壮/禁灸/原文摘录） | **451** 条，其中 **327** 条载有灸壮数 |
| `data/symptoms.json` | 症状 → 古籍段落 | **15** 类，**1,542** 处命中，**889** 处含灸法 |
| `data/moxa_forbidden.json` | 禁灸穴分类 | 明确 **17** / 分歧 **11** / 噪声 **6** |

## 4. 已知数据局限（重要）

### 4.1 缺字（□ 标记）
维基文库部分页面字体缺字，提取后成为 Unicode 私用区字符（无法显示）。
已全部替换为 **□** 并保留位置，**共 140 处**（含古籍 corpus 953 处）。
例：大椎「灸之令人□」——原文该字通作「瘖」（失音）。
**影响**：个别原文串不完整；**穴位名无一受损**，查询功能不受影响。

### 4.2 禁灸记载的典籍分歧
古籍间常有冲突，本库**不代为裁定**，而是分类呈现：

```
下关   素注灸三壮 / 铜人禁灸
耳门   铜人灸三壮 / 下经禁灸（并注「病宜灸者，不过三壮」）
太杼   铜人灸七壮 / 明堂禁灸（资生云「非大急不灸」）
```

→ 这类必须由执业医师判读，**不要当作「可以用」或「绝对不能用」**。

### 4.3 古籍 ≠ 现代循证
- 「主 XXX」是原文适应证罗列，非现代临床结论
- 壮数为古籍量级（「灸百壮」），**现代艾条灸远小于此**
- 本库无现代临床试验数据、无禁忌证更新、无个体化辨证

### 4.4 提取为规则近似，非人工校勘
条目切分基于体例规则，可能有遗漏或误切。
已剔除 6 条明显噪声，其余未逐条人工校勘。
**重要决策勿仅凭本库** —— 请核对原文（`references/` 引文均可回溯到维基文库对应卷次）。

## 5. 简体 / 繁体处理

**古籍原文本身是繁体**（维基文库原始录入）。为便于阅读，本库提供简体层：

| 层 | 内容 | 位置 |
|---|---|---|
| 原始繁体 | 抓取所得原文，**为准** | `data/*.json` 的 `name` / `text` / `ctx` 等字段 |
| 简体层 | 预先生成的简体变体 | 同上的 `name_s` / `text_s` / `ctx_s` 等字段 |

设计要点：

1. **预转换存库**，不在运行时转换 —— 保证 skill **零运行时依赖**（仅标准库）。
2. 用 `opencc`（`t2s` 配置）转换，它是**词组感知**的，比逐字映射表准确。
3. 转换是一次性的，**结果可审计、可 diff**（原始字段始终保留）。
4. `query.py` 默认输出简体，`--trad` 输出繁体原文；**输入简繁皆可**（内部建双向索引）。

**中医专有字的人工修正**（opencc 通用词典未覆盖，需额外处理）：

| 原文 | opencc 输出 | 修正为 | 说明 |
|---|---|---|---|
| 太谿 / 後谿 | 太谿 / 后谿 | **太溪 / 后溪** | 简化通行作「溪」 |
| 齗交 | 龂交 | **龈交** | 简化通行作「龈」 |
| 譩譆 | 譩𫍻 | 譩譆 | opencc 误转，回退 |

> 转换脚本：`scripts/extraction/build_simplified.py`（需 `opencc-python-reimplemented`，仅构建期依赖）。
> 校验：`scripts/validate_skill.py` 检查简体字段无残留繁体（`[5] 简体层完整性`）。

## 6. 复现方式（已验证）

数据**可精确重建**：从 `*.html` 跑完整流水线，产出的 `acupoints.json`（451 条）、
`moxa_forbidden.json`、`symptoms.json` 与线上**逐字段一致**（2026-09-18 验证，
差异 0 处）。

一条命令：

```bash
pip install --target /tmp/occdir opencc-python-reimplemented   # 简体层需要
bash scripts/run_pipeline.sh
```

路径通过环境变量覆盖，便于隔离测试（**不会误改线上数据**）：

| 变量 | 默认 | 说明 |
|---|---|---|
| `TCM_WORKSPACE` | `/tmp/tcm-src` | 语料与中间产物目录 |
| `TCM_DATA` | `<repo>/data` | 目标 skill 数据目录 |
| `SKIP_COPY` | — | 设为 `1` 则只重建到 `skill-data/`，不覆盖 `TCM_DATA` |

### 完整 8 阶段（`run_pipeline.sh` 即按此顺序）

```bash
WS=/tmp/tcm-src    # 语料区

# 0) 抓取（各卷独立，注意加间隔避免限流）
curl -A 'Mozilla/5.0' 'https://zh.wikisource.org/wiki/针灸大成/卷十' -o "$WS/zjdc_十.html"

# 1) HTML → 纯文本
python3 scripts/extraction/clean.py
# 2) 卷八/九/十/十一 → 穴位原始条目      ($WS/acupoints_raw.json)
python3 scripts/extraction/parse_acupoints.py
# 3) 症状关键字全文检索 → 症状索引        ($WS/symptom_index.json)
python3 scripts/extraction/build_symptoms.py
# 4) 组装 skill 数据                      ($WS/skill-data/*.json)
python3 scripts/extraction/build_skill_data.py

# 5) 交付：把 $WS/skill-data/*.json 复制进 skill 的 data/  ← 此步之后操作 $TCM_DATA
# 6) 禁灸穴分类（明确 17 / 分歧 11 / 噪声 6）
python3 scripts/extraction/curate_forbidden3.py
# 7) 缺字修复（Unicode 私用区 → □）
python3 scripts/extraction/fix_pua.py
# 8) 简体层生成 + 非穴位噪声清理
python3 scripts/extraction/build_simplified.py
python3 scripts/extraction/clean_v2.py

# 校验
python3 scripts/validate_skill.py
```

### 阶段间的数据依赖（易错点）

- **6 必须在 8 之前**：`clean_v2.py` 会读取 `moxa_forbidden.json` 的 `noise_dropped`
  清单来剔除人工判定的 6 条噪声（截断名/章节标题/药名）。顺序颠倒会导致
  复现结果多出 6 条（457 而非 451）。
- **8 在 7 之后**：`build_simplified.py` 负责生成 `_s` 简体字段，`clean_v2.py` 依赖它
  补齐 `forbidden_by_s` 等字段。
- 中间产物 `acupoints_raw.json`（516 条）≠ 最终库（451 条）：前者是规则切分结果，
  含噪声；后者经过 6→8 的清理与标注（组装后 475 条，剔除 24 条噪声得 451）。

### 其他脚本（辅助/探索，非流水线环节）

- `audit_forbidden.py` —— 审查禁灸条目，区分真穴位/噪声/典籍分歧
- `curate_forbidden2.py` —— `curate_forbidden3.py` 的前一版（出处归因不完整，保留供追溯）
- `clean.py` 之外的早期探索脚本已废弃（如 HTML 转文本的第一版）

## 7. 与其他 skill 的关系

| skill | 分工 |
|---|---|
| **tcm-moxibustion**（本 skill） | **艾灸取穴**：症状→穴位、灸壮、禁灸 |
| `nihaixia` | 倪海厦**针刺**教程、五输穴、经络流注、急救配穴 |
| `tcm-materia-medica` | **中药方剂**：性味、功效、方解（无穴位） |
| `like-perspective` / `wujutong` / `胡希恕·经方临床` | 经方/温病**方药辨证** |
| `family-health-archives` | 家庭健康档案**工作流** |

> 交叉验证：`nihaixia` 的「常见病症取穴公式」含部分灸法标注（如「肾虚腰痛→肾俞灸、命门灸、太溪」），可与本库互参。

## 8. 版本

- 建立：2026-09-18
- 数据源抓取日：2026-09-18
- 穴位 451 条 / 症状 15 类 / 禁灸 17+11 分类
- 2026-09-18 补充：简体层、清理 18 条非穴位噪声、修复 PUA 缺字、补 2 个参考文件
