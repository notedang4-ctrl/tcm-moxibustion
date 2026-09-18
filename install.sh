#!/usr/bin/env bash
# 安装 tcm-moxibustion 到 WorkBuddy / Hermes / Claude Code / Codex
# macOS + Linux 通用。单一数据源：本脚本所在目录（真身），其余 agent 通过 symlink 共享。
# 注意：所有 "$VAR后跟中文" 的写法都用 ${VAR} 花括号界定，避免 bash 把中文标点纳入变量名。
set -euo pipefail

SKILL_NAME="tcm-moxibustion"

# 真身 = 脚本所在目录（跨平台：macOS/Linux 的 $0 都能正确解析）
SKROOT="$(cd "$(dirname "$0")" && pwd)"

# 检测 python3：优先 WorkBuddy 隔离环境，回退系统 python3（脚本仅依赖标准库）
detect_python() {
  local cand
  for cand in "$HOME"/.workbuddy/binaries/python/versions/*/bin/python3; do
    [ -x "$cand" ] && { printf '%s' "$cand"; return 0; }
  done
  if command -v python3 >/dev/null 2>&1; then printf 'python3'; return 0; fi
  return 1
}
PY_BIN="$(detect_python)"
if [ -z "$PY_BIN" ]; then
  echo "错误: 未找到可用的 python3（系统 python3 或 ~/.workbuddy/binaries/...）" >&2
  exit 1
fi

echo "==> 安装 ${SKILL_NAME}"
echo "    源(真身): ${SKROOT}"
echo "    python:  ${PY_BIN}"

# 校验真身完整
[ -f "${SKROOT}/SKILL.md" ]          || { echo "错误: 缺少 ${SKROOT}/SKILL.md" >&2; exit 1; }
[ -f "${SKROOT}/scripts/query.py" ]  || { echo "错误: 缺少 ${SKROOT}/scripts/query.py" >&2; exit 1; }
[ -d "${SKROOT}/data" ]              || { echo "错误: 缺少 ${SKROOT}/data" >&2; exit 1; }

# --- 易失目录守卫 ---------------------------------------------------------
# 真身必须是持久目录：各 agent 的 skills 目录都 symlink 到它。若从 /tmp 之类的
# 易失位置运行，会把已有真身移成 .bak、换成指向 /tmp 的软链，清理后即失效。
is_volatile() {
  case "$1" in
    /tmp/*|/var/tmp/*|/private/tmp/*|/dev/shm/*|/run/*|/var/run/*) return 0 ;;
    *) return 1 ;;
  esac
}
if is_volatile "$SKROOT"; then
  # 检查是否已有真实安装会被顶替
  existing=""
  for d in "$HOME/.workbuddy/skills" "$HOME/.hermes/skills" "$HOME/.claude/skills"; do
    p="$d/$SKILL_NAME"
    if [ -d "$p" ] && [ ! -L "$p" ]; then existing="$p"; break; fi
  done
  if [ -n "$existing" ]; then
    if [ "${FORCE_VOLATILE:-0}" != "1" ]; then
      cat >&2 <<EOF
错误: 真身位于易失目录，且已有真实安装会被顶替。

  易失真身: ${SKROOT}
  将被顶替: ${existing}

从 /tmp 运行会把已有的真实 skill 目录移成 .bak，并让各 agent 的软链
指向 ${SKROOT} —— 该目录被系统清理后 skill 即失效。

请改为把仓库 clone 到持久位置后再装，例如：
  git clone https://github.com/notedang4-ctrl/tcm-moxibustion.git ~/skills/tcm-moxibustion
  bash ~/skills/tcm-moxibustion/install.sh

确实要强行继续（不推荐）：FORCE_VOLATILE=1 bash install.sh
EOF
      exit 1
    fi
    echo "  ⚠️  警告: 真身位于易失目录 ${SKROOT}，已按 FORCE_VOLATILE=1 强行继续" >&2
  else
    echo "  ⚠️  注意: 真身位于易失目录 ${SKROOT}（清理后 skill 即失效）"
  fi
fi

chmod +x "${SKROOT}/scripts/query.py" 2>/dev/null || true

# 数据自检（内置回归，失败即中止，避免装上坏数据）
echo "==> 数据自检"
if ! "${PY_BIN}" "${SKROOT}/scripts/validate_skill.py" >/tmp/tcm-moxi-validate.log 2>&1; then
  echo "错误: 数据自检未通过，详见 /tmp/tcm-moxi-validate.log" >&2
  tail -20 /tmp/tcm-moxi-validate.log >&2
  exit 1
fi
echo "  ✓ 47 项回归验证通过"

# 把真身链接到某个 agent 的 skills 目录；目录不存在则跳过
link_into() {
  local dest_dir="$1"
  [ -d "$dest_dir" ] || { echo "  - 跳过(未安装 ${dest_dir##*/}): $dest_dir"; return 0; }
  local dest="$dest_dir/$SKILL_NAME"
  if [ -L "$dest" ]; then
    local cur; cur="$(readlink "$dest")"
    if [ "$cur" = "$SKROOT" ]; then echo "  ✓ 已链接: $dest"; return; fi
    echo "  ~ 替换旧链接: $dest -> $cur"; rm -f "$dest"
  elif [ -e "$dest" ]; then
    if [ "$(cd "$dest" && pwd)" = "$SKROOT" ]; then
      echo "  - 真身已在此目录: $dest (无需链接)"; return
    fi
    local bak="$dest.bak-$(date +%Y%m%d%H%M%S)"
    echo "  ~ 备份已有目录: $bak"; mv "$dest" "$bak"
  fi
  ln -s "$SKROOT" "$dest"
  echo "  ✓ 已链接: $dest -> $SKROOT"
}

link_into "$HOME/.workbuddy/skills"
link_into "$HOME/.hermes/skills"
link_into "$HOME/.claude/skills"

# Codex: AGENTS.md 追加指针（不支持目录式 skill，用文本指向真身）
CODEX_MD="$HOME/.codex/AGENTS.md"
MARKER="# >>> ${SKILL_NAME} skill >>>"
if [ -f "$CODEX_MD" ] && grep -qF "$MARKER" "$CODEX_MD" 2>/dev/null; then
  echo "  ✓ Codex AGENTS.md 已含指针，跳过"
else
  mkdir -p "$(dirname "$CODEX_MD")"
  {
    printf '\n%s\n' "$MARKER"
    printf '## 本地 Skill: 中医艾灸取穴速查 (%s)\n' "$SKILL_NAME"
    printf '\n真身位于 %s（与 WorkBuddy/Hermes/Claude 共享同一份，升级只改一处）。\n' "$SKROOT"
    printf '调用前先设置解释器（脚本仅依赖 Python 标准库，系统 python3 即可）：\n'
    printf '```bash\n'
    printf 'PY=%s\n' "$PY_BIN"
    printf '%s/scripts/query.py symptom 脚冷\n' "$SKROOT"
    printf '%s/scripts/query.py symptom 腰痛\n' "$SKROOT"
    printf '%s/scripts/query.py point 肾俞 关元\n' "$SKROOT"
    printf '%s/scripts/query.py forbidden\n' "$SKROOT"
    printf '```\n\n'
    printf '规则：涉及穴位/灸法/取穴，先跑脚本再回答，禁止凭记忆；\n'
    printf '输出默认简体，需繁体原文加 --trad；穴位名简繁输入皆可。\n'
    printf '本工具为古籍文献检索，非诊疗建议；热证/阴虚火旺/孕期腹部腰骶禁灸，\n'
    printf '糖尿病者烫伤风险极高，有红旗症状先就医。施灸前必读 references/02-safety-contraindications.md。\n'
    printf '%s\n' "$MARKER"
  } >> "$CODEX_MD"
  echo "  ✓ 已追加指针到 $CODEX_MD"
fi

echo "==> 完成。版本: $(grep '^version:' "${SKROOT}/SKILL.md" | head -1 | sed 's/^version:[[:space:]]*//')"
echo "    试跑: ${PY_BIN} ${SKROOT}/scripts/query.py symptom 脚冷"
