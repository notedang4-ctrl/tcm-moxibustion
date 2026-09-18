#!/usr/bin/env bash
# 卸载 tcm-moxibustion（仅移除各平台的 symlink 与 Codex 指针段；不删除真身）
# macOS + Linux 通用。变量名均用 ${VAR} 花括号，避免中文标点被纳入变量名。
set -euo pipefail

SKILL_NAME="tcm-moxibustion"
SKROOT="$(cd "$(dirname "$0")" && pwd)"

echo "==> 卸载 ${SKILL_NAME} (保留真身: ${SKROOT})"

unlink_from() {
  local dest_dir="$1"
  [ -d "$dest_dir" ] || return 0
  local dest="$dest_dir/$SKILL_NAME"
  if [ -L "$dest" ]; then
    rm -f "$dest"; echo "  ✓ 移除链接: $dest"
  elif [ -e "$dest" ]; then
    if [ "$(cd "$dest" && pwd)" = "$SKROOT" ]; then
      echo "  - 真身即在此目录: $dest (不删除)"; return
    fi
    echo "  ! 跳过: $dest 非软链(独立副本)，未删除"
  else
    echo "  - 不存在: $dest"
  fi
}

unlink_from "$HOME/.workbuddy/skills"
unlink_from "$HOME/.hermes/skills"
unlink_from "$HOME/.claude/skills"

# Codex: 删除 AGENTS.md 中的指针段（marker 之间）
CODEX_MD="$HOME/.codex/AGENTS.md"
MARKER="# >>> ${SKILL_NAME} skill >>>"
if [ -f "$CODEX_MD" ] && grep -qF "$MARKER" "$CODEX_MD" 2>/dev/null; then
  awk -v m="$MARKER" '
    $0==m { skip=!skip; next }
    skip { next }
    { print }
  ' "$CODEX_MD" > "$CODEX_MD.tmp" && mv "$CODEX_MD.tmp" "$CODEX_MD"
  echo "  ✓ 已移除 Codex AGENTS.md 指针段"
else
  echo "  - Codex 指针段不存在，跳过"
fi

echo "==> 完成。真身仍在 ${SKROOT}，如需彻底删除请手动 rm -rf。"
