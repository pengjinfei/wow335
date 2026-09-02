#!/usr/bin/env bash
# 上游同步脚本 —— 见 docs/03-上游同步与分支策略.md
# 用法:
#   ./sync-upstream.sh            只 fetch + 报告落后情况，不做修改
#   ./sync-upstream.sh --apply    实际同步: 基线分支 ff 前进, 并 merge 进 dev
#   ./sync-upstream.sh --status   打印各仓库当前 HEAD

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CORE="$ROOT/azerothcore-wotlk"
MOD="$CORE/modules/mod-playerbots"

# 仓库 路径:基线分支:开发分支
REPOS=(
  "core|$CORE|Playerbot|dev"
  "mod-playerbots|$MOD|master|dev"
)

ACTION="${1:-report}"

current_branch() { git -C "$1" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "?"; }

sync_one() {
  local name="$1" path="$2" base="$3" dev="$4"
  if [[ ! -d "$path/.git" ]]; then
    echo "⚠️  [$name] 仓库不存在: $path （先跑 setup-macos.sh clone）"
    return
  fi
  echo ""
  echo "━━━ $name ($path)"
  echo "    当前分支: $(current_branch "$path")  HEAD: $(git -C "$path" rev-parse --short HEAD)"

  git -C "$path" fetch origin "$base" --quiet
  local behind_dev behind_base
  behind_dev=$(git -C "$path" rev-list --count "origin/$base..$dev" 2>/dev/null || echo "?")
  behind_base=$(git -C "$path" rev-list --count "$dev..origin/$base" 2>/dev/null || echo "?")
  echo "    dev 领先上游 $base: $behind_dev 个提交 (我们的改动)"
  echo "    dev 落后上游 $base: $behind_base 个提交 (待同步)"

  if [[ "$ACTION" == "--apply" ]]; then
    local start_branch
    start_branch=$(current_branch "$path")
    echo "    → 更新 $base ..."
    git -C "$path" checkout "$base" --quiet
    git -C "$path" pull --ff-only origin "$base" --quiet
    echo "    → merge $base 进 $dev ..."
    git -C "$path" checkout "$dev" --quiet
    if git -C "$path" merge "$base" --no-edit; then
      echo "    ✅ $name 同步完成"
    else
      echo "    ❌ $name 有冲突，请手工解决:"
      echo "       cd $path && git status   # 解冲突后: git add -A && git merge --continue"
      echo "       放弃本次: git merge --abort"
      git -C "$path" checkout "$start_branch" --quiet 2>/dev/null || true
      return 1
    fi
    git -C "$path" checkout "$start_branch" --quiet
  fi
}

echo "== 上游同步 ($ACTION) =="
FAILED=0
for spec in "${REPOS[@]}"; do
  IFS='|' read -r name path base dev <<< "$spec"
  sync_one "$name" "$path" "$base" "$dev" || FAILED=1
done

if [[ "$ACTION" == "report" ]]; then
  echo ""
  echo "（报告模式。确认要同步后运行: $0 --apply）"
fi
exit "$FAILED"
