# Devin CLI 接入灵枢

纪律注入方式：**全局规则** `~/.config/devin/AGENTS.md`（每会话注入）+ **hooks**（硬性触发，可选但推荐）。
Devin 无官方 harness 适配目录的先例，本目录按仓库的 per-harness 惯例组织。

## 三步接入

```bash
git clone https://github.com/FuRongJun-1999/dsh-memory.git && cd dsh-memory
# 1. 记忆根（随意选，下面记作 $HOME/.lingshu/cogmap）
mkdir -p ~/.lingshu/cogmap
# 2. 注册 MCP（user scope 全局生效）
devin mcp add -s user lingshu -- python3 -m md_cg.mcp_server
# 3. 在 ~/.config/devin/mcp_config.json 给 lingshu.env 补三项：
#    PYTHONPATH=<本仓库路径>  MDCG_ROOT=<记忆根>  MDCG_TOKEN=<令牌>
```

签发最小权限写入令牌（可选；不签发则只读 guest）：

```bash
python3 -m md_cg.tokens issue --role recorder --actor devin --clearance internal
```

## 规则与 hooks

| 文件 | 装到哪 | 作用 |
|---|---|---|
| `AGENTS.md` | `~/.config/devin/AGENTS.md`（全局规则） | 会话起始 route 查记忆 / 收尾 CCG 六要素归档 / 判定语义 |
| `hooks/lingshu_hooks.py` | 任意位置（脚本内自动定位仓库根，或用 `LINGSHU_REPO` 指定） | 四钩子脚本：session-start 召回摘要 / post-tool 记账 / stop-check 收尾提醒 / post-compact 重路由提醒 |
| `hooks.config.example.json` | 合并进 `~/.config/devin/config.json` 的 `"hooks"` 键 | 钩子注册样例（把 `<REPO>` 换成实际路径） |
| `mcp_config.example.json` | `~/.config/devin/mcp_config.json` | MCP 注册样例 |

## 与 DSH 端的差异

- **无 session hook**：自动转录不可用，靠「规则纪律 + Stop 钩子兜底」驱动归档。
- **无跨会话隔离**：`session5_resolve` 读 DSH 会话文件，Devin 无此机制——所有会话共享一张认知图。
- **工具面完整**：`cg` / `stg` / `mdcg_*` 全部可用（kernel 面默认暴露 `cg`、`stg` 两基元）。
- **钩子语义**：Stop 钩子在「有实质改动但零归档」时拦一次（靠 `stop_hook_active` 防循环，每次收尾最多提醒一回）；阈值与 mutating 工具集见脚本顶部常量。
