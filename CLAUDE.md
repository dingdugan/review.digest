# reviewdigest

> 本项目继承 `~/.claude/CLAUDE.md`（Execution Discipline + Plan→Code→Ship 工作流）。下面只补充本项目特有的规则。

**产品**：开源的 App Store 评论周报 GitHub Action。独立开发者 fork 模板仓库、填 app id，每周自动抓取多国家 storefront 的评论，LLM 聚类成「差评主题 / 崩溃反馈 / 功能请求」周报，以 GitHub Issue 形式送达。零服务器成本。

**Stack**: Python 3.11+（stdlib + requests + pyyaml），GitHub Actions，LLM 走裸 REST（Anthropic / OpenAI 兼容），无 SDK 依赖。

**关键命令**:
- 本地跑一次（不发 Issue）: `python -m reviewdigest --dry-run`
- 测试: `python -m pytest tests/ -q`
- 数据层冒烟验证: `python -m reviewdigest --dry-run --no-llm`

## 文档约定（活文档）

所有项目文档放 `docs/`，**扁平 + 前缀**，不开子目录：

| 前缀 | 用途 |
| --- | --- |
| `spec-<feature>.md` | 功能规格 / PRD |
| `decision-<topic>.md` | 决策快照（选 X 不选 Y 的 why） |
| `research-<topic>.md` | 调研、外部参考 |
| `design-<feature>.md` | UI/交互稿、视觉规范 |
| `_archive/` | 过期/被取代的文档（不删，仍可回查） |

每份文档头部 frontmatter：`status: active|draft|superseded|done` + `updated: YYYY-MM-DD`。

## 强制规则（防止"聊半天没实现"）

### ① Checklist 条目自带验收证据

`IMPLEMENTATION_CHECKLIST.md` 每条「动词 + 文件 + 行为」+ 验收 + 证据三件套，没证据不打 `[x]`。

### ② Plan→Code 切换点必须"封板"

共识落成 checklist 条目后才动手写代码。

### ③ Code 结束输出对齐表

报告完成时输出 checklist 条目 × 改动 (file:line) × 证据 对齐表。

## docs index（每次新增文档同步更新）

- [decision-scope-v1.md](docs/decision-scope-v1.md) — V1 范围决策快照（红军演习结论：iOS-only、GitHub Action 形态、多国聚合）
- [research-data-layer.md](docs/research-data-layer.md) — 评论数据层实测（2026-07-10）：RSS 已死，改用 apps.apple.com 无鉴权 web API
- [_archive/handoff-reviewdigest.md](docs/_archive/handoff-reviewdigest.md) — 2026-07-10 开工 handoff（已被 CLAUDE.md + checklist 取代，历史回查用）

## 项目特定上下文

- **数据层**：`https://apps.apple.com/api/apps/v1/catalog/{country}/apps/{id}/reviews?platform=web&sort=recent&limit=20&offset=N`，无需 token，必须带浏览器 UA，请求间隔 ≥1s 否则 429。详见 research-data-layer.md
- **旧 iTunes RSS customerreviews 端点 2026-07 已确认失效**（返回空 feed），不要再尝试
- LLM 默认 `anthropic` + `claude-opus-4-8`（`claude-sonnet-5` 为省钱选项），key 走环境变量 / repo secret，绝不写进代码或配置
- 状态（去重 seen ids + 评分历史）存 `state/state.json`，Action 里 commit 回仓库，零外部存储
