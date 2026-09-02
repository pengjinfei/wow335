# 环境搭建手册（macOS / Apple Silicon）

> 目标：从零到"服务器跑起来 + 客户端能登录"。
> 按顺序执行；每步都有验证点，出错先停在原地排查。
> 自动化版本见 `scripts/setup-macos.sh`（先通读本手册再用脚本）。

## 0. 前置检查

```bash
# 磁盘：至少 20GB 可用
df -h ~

# 工具链
git --version && cmake --version && clang --version | head -1
xcode-select -p        # 无输出则: xcode-select --install

# 网络：GitHub 需要代理（本机代理端口 7897，按实际改）
export https_proxy=http://127.0.0.1:7897 http_proxy=http://127.0.0.1:7897
curl -sI https://github.com -o /dev/null -w "%{http_code}\n"   # 期望 200
```

## 1. 安装依赖

官方清单（来自 `apps/installer/includes/os_configs/osx.sh`）：

```bash
brew install openssl@3 readline boost bash-completion curl unzip \
             mysql ccache expect tmux screen jq cmake
```

**本机当前状态（2026-09-02 盘点）**：
已有 ✅：openssl@3、readline、jq、cmake、bash、boost、ccache；
缺失 ❌：bash-completion、curl、unzip、expect、tmux、screen（均可选）。

**MySQL 注意**：不要用 `brew install mysql`（9.x）。本机实测 9.3.0 会因
protobuf 依赖被单独升级而启动即崩；且上游以 8.x 为主。使用 **mysql@8.4**：

```bash
brew install mysql@8.4
export PATH="/opt/homebrew/opt/mysql@8.4/bin:$PATH"   # 编译和日常都要带上
/opt/homebrew/opt/mysql@8.4/support-files/mysql.server start
mysql -uroot -e "SELECT VERSION();"   # 验证：8.4.x
```

## 2. 获取代码

工作区：`~/IdeaProjects/github/wow335`（本管理库）。上游仓库克隆为子目录，
各自是独立 git 仓库（已在 `.gitignore` 中排除）。

```bash
cd ~/IdeaProjects/github/wow335
export https_proxy=http://127.0.0.1:7897 http_proxy=http://127.0.0.1:7897

# 核心 fork：必须用 Playerbot 分支（master 编不了）
git clone https://github.com/mod-playerbots/azerothcore-wotlk.git \
          --branch Playerbot
cd azerothcore-wotlk

# 机器人模块：克隆进 modules/
cd modules
git clone https://github.com/mod-playerbots/mod-playerbots.git \
          --branch master
cd ..

# 建立自己的开发分支（上游分支保持只读，见 docs/03）
git switch -c dev
cd modules/mod-playerbots && git switch -c dev && cd ../..
```

验证点：`ls modules/mod-playerbots/src/Ai/Raid/ICC/` 能看到
`ICCActions_LK.cpp` 等文件。

## 3. 配置构建选项

创建 `conf/config.cmake`（cmake 本地覆盖，必须做——默认不编提取工具）：

```bash
cat > conf/config.cmake <<'EOF'
# 本项目自定义构建选项（覆盖 conf/dist/config.cmake 的默认值）
set(TOOLS_BUILD "all")        # 地图/DB 提取工具（必需）
EOF
```

## 4. 编译

**Apple Silicon 必读**：`apps/compiler/includes/functions.sh` 的 `comp_configure`
对 macOS 硬编码了 **Intel Homebrew 路径**（`/usr/local/opt/openssl@3/...`），
在 M 系列芯片上指向不存在的文件，且优先级高于自动探测，导致
`Could NOT find OpenSSL`。修复：用 `CCUSTOMOPTIONS` 覆盖（它追加在硬编码
参数之后，后写生效）：

```bash
export PATH="/opt/homebrew/opt/mysql@8.4/bin:$PATH"
HB=$(brew --prefix)
export CCUSTOMOPTIONS="\
 -DMYSQL_ADD_INCLUDE_PATH=$HB/opt/mysql@8.4/include/mysql \
 -DMYSQL_LIBRARY=$HB/opt/mysql@8.4/lib/libmysqlclient.dylib \
 -DREADLINE_INCLUDE_DIR=$HB/opt/readline/include \
 -DREADLINE_LIBRARY=$HB/opt/readline/lib/libreadline.dylib \
 -DOPENSSL_ROOT_DIR=$HB/opt/openssl@3 \
 -DOPENSSL_INCLUDE_DIR=$HB/opt/openssl@3/include \
 -DOPENSSL_SSL_LIBRARIES=$HB/opt/openssl@3/lib/libssl.dylib \
 -DOPENSSL_CRYPTO_LIBRARIES=$HB/opt/openssl@3/lib/libcrypto.dylib"
./acore.sh compiler build
```

- 首次全量约 **15~30 分钟**（M 系列，开 PCH + ccache）；
- 产物在 `env/dist/bin/`；磁盘占用约 8~12GB（`var/build/`）。
- **configure 失败后务必先 `rm -rf var/build/obj`**：CMakeCache 会把
  `OPENSSL_*-NOTFOUND` 之类的空值缓存住，之后怎么改环境变量都不生效。

**手动编译备用路径**（dashboard 出错时用）：

```bash
mkdir -p var/build/obj && cd var/build/obj
cmake ../../../ -G "Unix Makefiles"
make -j8          # 16GB 内存用 -j8，32GB 用 -j10~12
```

验证点：

```bash
ls env/dist/bin/
# 期望: worldserver authserver mapextractor vmap4extractor
#       vmap4assembler mmaps_generator
```

## 5. 数据库

```bash
./acore.sh setup-db
```

做了三件事：创建 `acore` 用户 → 建 `acore_auth/characters/world` 三个库 →
导入 base SQL。`acore_playerbots` 库会在首次启动时自动创建。

验证点：

```bash
mysql -uacore -pacore -e "SHOW DATABASES;" | grep acore
# 期望: acore_auth acore_characters acore_world
```

## 6. 客户端数据提取

前提：拿到 **3.3.5a（build 12340）enUS** 客户端
（本机客户端在 Windows 上：先在 Windows 用提取工具提取
`dbc/maps/vmaps/mmaps` 后拷回，避免搬运 30GB 客户端文件）。

```bash
# 假设客户端文件在 ~/wow-client，产出数据目录为 ~/wow335/data
./apps/extractor/extractor.sh
# 交互式脚本：依次回答客户端路径与输出路径
```

- maps/vmaps 分钟级；**mmaps 1~3 小时**，可后台；
- 产出四个目录：`dbc/ maps/ vmaps/ mmaps/`（另有可选 `cameras/`）。

## 7. 服务器配置

复制并修改配置：

```bash
cd azerothcore-wotlk   # 工作区子目录
# dist 模板在 src/server/apps/... 下，构建后也会在 env/dist/etc/
cp src/server/apps/authserver/authserver.conf.dist   conf/authserver.conf
cp src/server/apps/worldserver/worldserver.conf.dist conf/worldserver.conf
cp modules/mod-playerbots/conf/playerbots.conf.dist  conf/playerbots.conf
```

`conf/worldserver.conf` 必改项：

```ini
DataDir = "~/wow335/data"    # §6 的产出目录
BindIP  = "0.0.0.0"          # 允许 Windows 客户端从局域网连入
# MySQL 三项保持默认（127.0.0.1 / acore / acore）
```

`conf/authserver.conf`：`BindIP = "0.0.0.0"`。

防火墙放行（系统设置 → 网络 → 防火墙，或关闭防火墙测试）：
**3724**（auth）、**8085**（world）。

## 8. 启动与验证

```bash
./acore.sh run-authserver     # 终端 1
./acore.sh run-worldserver    # 终端 2（首次启动自动应用模块 SQL）
```

验证清单：

- [ ] worldserver 控制台出现 `World initialized` 且无 DB 错误；
- [ ] 控制台创建管理员账号：
  ```
  account create admin admin
  account set gmlevel admin 3 -1
  ```
- [ ] Windows 客户端 `realmlist.wtf` 改为 `set realmlist <Mac局域网IP>`；
- [ ] `acore_auth.realmlist` 表地址同步改为该 IP：
  ```sql
  UPDATE acore_auth.realmlist SET address='<Mac局域网IP>';
  ```
- [ ] 客户端登录、建角色、进游戏；
- [ ] 控制台/游戏内 `#playerbot bot addclass` 能召出机器人（进入第二阶段）。

## 9. 日常开发循环

```bash
# 改 modules/mod-playerbots 代码后：
cd azerothcore-wotlk && ./acore.sh compiler compile   # 仅编译，不重跑 cmake
# 重启 worldserver（模块是静态链接，改代码必须重启）
```

增量编译（只改模块）约 1~2 分钟。配合 `ccache`（`./acore.sh compiler
ccacheShowStats` 看命中率）。

## 常见问题

| 症状 | 处理 |
|---|---|
| cmake configure 报版本/策略错误 | 本机 cmake 4.3 超出项目声明范围：`pip3 install cmake==3.31.6` 后重试 |
| `mysql.h` / libmysqlclient 找不到 | 用 §4 备用路径手动 cmake，显式传 `-DMYSQL_ADD_INCLUDE_PATH` 等（完整参数见 `docs/01` §4.2） |
| 链接时找不到 openssl | 设置 `export OPENSSL_ROOT_DIR=$(brew --prefix openssl@3)` 再编 |
| 启动报 `Database ... not found` | 重跑 `./acore.sh setup-db`；检查 `conf/*.conf` 的 DB 账号 |
| 客户端"验证版本失败/无法连接" | realmlist 与 `acore_auth.realmlist` 两处都要是 Mac 的局域网 IP；防火墙放行 3724/8085 |
| bot 不会放技能 | DBC 不是 enUS，重新用英文客户端提取 |
| bot 走路卡地形/跳崖 | mmaps 未提取完整，重新跑 `mmaps_generator` |
