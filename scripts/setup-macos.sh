#!/usr/bin/env bash
# macOS 一键环境搭建 —— 对应 docs/02-环境搭建手册-macOS.md
# 用法:
#   ./setup-macos.sh            # 依次执行全部阶段
#   ./setup-macos.sh <阶段>...  # 只跑指定阶段: deps clone config build db
# 可重复执行（幂等）：已存在的仓库/配置不会重复创建。
#
# 网络代理：默认走本机 7897，可通过环境变量覆盖，例如
#   PROXY="" ./setup-macos.sh            # 不用代理
#   PROXY="http://127.0.0.1:1080" ./setup-macos.sh

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CORE="$ROOT/azerothcore-wotlk"
MOD="$CORE/modules/mod-playerbots"
PROXY="${PROXY-http://127.0.0.1:7897}"
MIN_FREE_GB=20

CORE_REPO="https://github.com/mod-playerbots/azerothcore-wotlk.git"
CORE_BRANCH="Playerbot"
MOD_REPO="https://github.com/mod-playerbots/mod-playerbots.git"
MOD_BRANCH="master"

# 官方依赖里编译真正必需的 + 强烈建议的；系统自带的不重复装
BREW_REQUIRED=(openssl@3 readline boost mysql ccache cmake jq)

log()  { printf '\n\033[1;36m[%s]\033[0m %s\n' "$(date +%H:%M:%S)" "$*"; }
warn() { printf '\033[1;33m  ⚠ %s\033[0m\n' "$*"; }
die()  { printf '\033[1;31m  ✖ %s\033[0m\n' "$*" >&2; exit 1; }

proxy_env() {
  if [[ -n "$PROXY" ]]; then
    export https_proxy="$PROXY" http_proxy="$PROXY"
    log "已启用代理 $PROXY"
  fi
}

check_disk() {
  local free_gb
  free_gb=$(df -g "$ROOT" | awk 'NR==2{print $4}')
  log "磁盘可用空间: ${free_gb}GB"
  if (( free_gb < MIN_FREE_GB )); then
    die "可用空间不足 ${MIN_FREE_GB}GB（当前 ${free_gb}GB），请先清理磁盘再继续"
  fi
}

stage_deps() {
  log "阶段 1/5：安装依赖"
  command -v brew >/dev/null || die "未安装 Homebrew，见 https://brew.sh"
  local missing=()
  for pkg in "${BREW_REQUIRED[@]}"; do
    [[ -e "$(brew --prefix)/opt/$pkg" ]] || missing+=("$pkg")
  done
  if (( ${#missing[@]} )); then
    log "安装缺失依赖: ${missing[*]}"
    brew install "${missing[@]}"
  else
    log "依赖已齐全，跳过"
  fi
  local v
  v=$(cmake --version | head -1 | awk '{print $3}')
  case "$v" in 4.*) warn "cmake $v 高于项目声明上限(3.22)，若 configure 失败请改用 3.31: pip3 install cmake==3.31.6";; esac
  if brew services list 2>/dev/null | grep -q "mysql.*stopped"; then
    log "启动 MySQL"
    brew services start mysql
  fi
}

clone_one() {
  local url="$1" dest="$2" branch="$3"
  if [[ -d "$dest/.git" ]]; then
    log "已存在，跳过克隆: $dest"
  else
    log "克隆 $url ($branch)"
    git clone "$url" --branch "$branch" "$dest"
  fi
  # 保证本地开发分支存在（上游分支保持只读）
  if ! git -C "$dest" show-ref --verify --quiet refs/heads/dev; then
    git -C "$dest" branch dev "origin/$branch" 2>/dev/null || git -C "$dest" branch dev
    log "已创建开发分支 dev"
  fi
}

stage_clone() {
  log "阶段 2/5：获取代码"
  proxy_env
  check_disk
  clone_one "$CORE_REPO" "$CORE" "$CORE_BRANCH"
  mkdir -p "$CORE/modules"
  clone_one "$MOD_REPO" "$MOD" "$MOD_BRANCH"
}

stage_config() {
  log "阶段 3/5：写入构建配置"
  mkdir -p "$CORE/conf"
  cat > "$CORE/conf/config.cmake" <<'EOF'
# 本项目自定义构建选项（覆盖 conf/dist/config.cmake）
set(TOOLS_BUILD "all")        # 地图/DB 提取工具（必需）
EOF
  log "conf/config.cmake 已就绪 (TOOLS_BUILD=all)"
}

stage_build() {
  log "阶段 4/5：编译（首次约 15~30 分钟）"
  cd "$CORE"
  ./acore.sh compiler build
  ls env/dist/bin/worldserver env/dist/bin/authserver >/dev/null \
    && log "编译产物已生成: env/dist/bin/"
}

stage_db() {
  log "阶段 5/5：初始化数据库"
  cd "$CORE"
  ./acore.sh setup-db
  log "数据库初始化完成（acore_playerbots 会在首次启动时自动创建）"
}

# ── 入口 ──────────────────────────────────────────────
stages=("$@")
(( ${#stages[@]} )) || stages=(deps clone config build db)

for s in "${stages[@]}"; do
  case "$s" in
    deps)   stage_deps   ;;
    clone)  stage_clone  ;;
    config) stage_config ;;
    build)  stage_build  ;;
    db)     stage_db     ;;
    *) die "未知阶段: $s （可选: deps clone config build db）" ;;
  esac
done

log "全部完成。剩余手工步骤见 docs/02 第 6~8 步："
echo "  1) 提取客户端数据（需 enUS 3.3.5a 客户端）"
echo "  2) 生成并修改 conf/worldserver.conf、authserver.conf、playerbots.conf"
echo "  3) ./acore.sh run-authserver 与 run-worldserver 启动"
