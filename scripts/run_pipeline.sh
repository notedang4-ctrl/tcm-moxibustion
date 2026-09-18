#!/usr/bin/env bash
# tcm-moxibustion 数据流水线 —— 从古籍 HTML 重建 skill 数据（可完整复现）
#
# 用法：
#   bash run_pipeline.sh                 # 用默认路径跑全流程
#   TCM_WORKSPACE=/path/to/ws bash run_pipeline.sh
#   TCM_DATA=/path/to/data  bash run_pipeline.sh
#
# 环境变量：
#   TCM_WORKSPACE  语料与中间产物目录（默认 /tmp/tcm-src）
#   TCM_DATA       目标 skill 数据目录（默认 <repo>/data）
#   SKIP_COPY=1    只重建到 $TCM_WORKSPACE/skill-data，不覆盖 $TCM_DATA
#
# 前置条件：
#   - $TCM_WORKSPACE 下已有 ① 抓取的 *.html（见下方 curl 示例）
#   - 简体层需要 opencc：pip install --target /tmp/occdir opencc-python-reimplemented
#
# 抓取示例（各卷独立，注意加间隔避免限流）：
#   curl -A 'Mozilla/5.0' 'https://zh.wikisource.org/wiki/针灸大成/卷一' -o "$WS/zjdc_一.html"
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
SKROOT="$(cd "$HERE/.." && pwd)"          # scripts/ -> skill root
WS="${TCM_WORKSPACE:-/tmp/tcm-src}"
export TCM_WORKSPACE="$WS"
export TCM_DATA="${TCM_DATA:-$SKROOT/data}"
E="$HERE/extraction"

PY="$(command -v python3 || true)"
[ -n "$PY" ] || { echo "错误: 未找到 python3" >&2; exit 1; }

step() { printf '\n=== %s ===\n' "$1"; }

mkdir -p "$WS"

step "1/8  clean.py — HTML → 纯文本"
"$PY" "$E/clean.py"
step "2/8  parse_acupoints.py — 纯文本 → 穴位原始条目"
"$PY" "$E/parse_acupoints.py"
step "3/8  build_symptoms.py — 纯文本 → 症状索引"
"$PY" "$E/build_symptoms.py"
step "4/8  build_skill_data.py — 组装 skill 数据"
"$PY" "$E/build_skill_data.py"

if [ "${SKIP_COPY:-0}" != "1" ]; then
  step "5/8  交付：$WS/skill-data → $TCM_DATA"
  mkdir -p "$TCM_DATA"
  cp "$WS"/skill-data/acupoints.json "$WS"/skill-data/symptoms.json "$TCM_DATA"/
  echo "  已复制 acupoints.json / symptoms.json"
else
  step "5/8  跳过复制（SKIP_COPY=1）"
  TCM_DATA="$WS/skill-data"
  export TCM_DATA
fi

step "6/8  curate_forbidden3.py — 禁灸穴分类"
"$PY" "$E/curate_forbidden3.py" >/dev/null
echo "  moxa_forbidden.json 已生成（明确/分歧/噪声分类）"

step "7/8  fix_pua.py — 缺字修复（PUA → □）"
"$PY" "$E/fix_pua.py"

step "8/8  build_simplified.py + clean_v2.py — 简体层 + 噪声清理"
"$PY" "$E/build_simplified.py" >/dev/null
"$PY" "$E/clean_v2.py"

step "校验"
"$PY" "$SKROOT/scripts/validate_skill.py" | tail -3
