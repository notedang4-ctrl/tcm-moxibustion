# tcm-moxibustion

中医**艾灸取穴**速查 skill —— 供 WorkBuddy / Hermes / Claude Code / Codex 等 agent 调用。
按症状反查该灸哪些穴位、灸多少壮、哪些穴禁灸，每条结论都附古籍原文出处，不靠模型记忆。

## 功能

- **按症状查取穴**：脚冷、腰痛、胃寒、宫寒痛经、久泄、失眠、夜尿、关节冷痛、中风急救等 15 类
- **查单个穴位**：定位、灸壮数、是否禁灸、古籍原文主治
- **禁灸穴清单**：区分「明确禁灸」与「典籍分歧」，不代为裁定
- **按名/定位筛穴**：如「脐」「内踝」
- **简繁双层**：默认输出简体，`--trad` 看繁体原文；输入简繁皆可

覆盖：**451 个穴位**（327 个载有灸壮数）+ **15 类症状**、共 1542 处古文献命中（其中 889 处含灸法）。

数据源为维基文库公版古籍：《针灸大成》全 12 卷、《备急灸法》（宋·张涣）、《扁鹊心书》（宋·窦材）、《外台秘要》（唐·王焘）。

## 安装

```bash
git clone https://github.com/notedang4-ctrl/tcm-moxibustion.git
cd tcm-moxibustion
bash install.sh
```

`install.sh` 会把本目录（真身）通过 symlink 链接到各 agent 的 skills 目录，
真身只有一份，升级只改一处。已装 WorkBuddy / Hermes / Claude Code 的会被自动识别；
Codex 会在 `~/.codex/AGENTS.md` 追加指针段。

> **请 clone 到持久目录**（如 `~/skills/`）。从 `/tmp` 等易失位置运行 `install.sh`
> 会把已有安装顶替为指向该位置的软链，清理后即失效 —— 脚本会检测并直接拒绝。

## 使用

```bash
SK=~/.hermes/skills/tcm-moxibustion     # 或 clone 下来的目录

python3 $SK/scripts/query.py symptom 脚冷      # 症状 → 取穴（含古籍原文）
python3 $SK/scripts/query.py symptom 腰痛
python3 $SK/scripts/query.py symptom-list      # 列出 15 个症状分类
python3 $SK/scripts/query.py point 肾俞 关元    # 穴位详情
python3 $SK/scripts/query.py point-list 脐      # 按名/定位筛
python3 $SK/scripts/query.py moxa-list         # 有灸壮数且未禁灸的穴位
python3 $SK/scripts/query.py forbidden         # 禁灸穴（分类呈现）
python3 $SK/scripts/query.py forbidden disputed   # 只看典籍分歧项

python3 $SK/scripts/query.py point 肾俞 --trad  # 看繁体原文
```

仅依赖 Python 标准库，无需安装任何第三方包。

## 校验

```bash
python3 $SK/scripts/validate_skill.py     # 47 项回归验证
```

覆盖：文件完整性、数据规模、噪声清理、无 PUA 缺字、简体层完整、关键穴位在位、
委中禁灸断言、简繁双向查询、文档语言、frontmatter。

## 数据可复现

一条命令从古籍 HTML 重建全部数据：

```bash
pip install --target /tmp/occdir opencc-python-reimplemented   # 简体层需要
bash scripts/run_pipeline.sh
```

产出的 `acupoints.json`（451 条）、`moxa_forbidden.json`、`symptoms.json` 与仓库内数据
**逐字段完全一致**（已验证，差异 0 处）。`scripts/extraction/` 保留 10 个提取脚本，
数据不是黑盒。

路径可用环境变量覆盖以便隔离测试，**不会误改线上数据**：
`TCM_WORKSPACE`（语料区，默认 `/tmp/tcm-src`）、`TCM_DATA`（目标数据目录）、
`TCM_OPENCC_DIR`。详见 `references/03-classical-sources.md` §6。

## ⚠️ 重要边界

**本 skill 是古籍文献检索工具，不是诊断或治疗建议。**

- 古籍记载 ≠ 现代循证证据；「主 XXX」是原文适应证罗列，不等于该穴对现代疾病有效
- 壮数为古籍量级（如「灸百壮」），**现代艾条灸用量远小于此**，勿照搬
- 热证、阴虚火旺、孕期（腹部腰骶）、皮肤破损处禁灸；**糖尿病者烫伤风险极高**
- 有红旗症状（腰痛伴大小便失禁/鞍区麻木、单侧突发肢冷伴苍白剧痛等）**先就医，勿自行施灸**
- 禁灸记载在各典籍间存在分歧，本库分类呈现、不代为裁定

施灸前请读 `references/02-safety-contraindications.md`。涉及诊断、用药、针刺操作请咨询执业医师。

## 相关 skill

| skill | 分工 |
|---|---|
| **tcm-moxibustion**（本 skill） | 艾灸取穴：症状→穴位、灸壮、禁灸 |
| [tcm-materia-medica](https://github.com/notedang4-ctrl/tcm-materia-medica) | 中药材 / 方剂速查 |
| `nihaixia` | 倪海厦针刺教程、五输穴、经络流注 |

## 许可与出处

古籍原文取自[维基文库](https://zh.wikisource.org/)公版文献，原文以繁体为准（本库保留原始字段，
另存简体层）。提取脚本与整理数据见本仓库。

**医学免责**：本项目仅供中医文献学习与研究，不构成医疗建议。使用者须自行判断，
并对自己的一切健康决策负责。
