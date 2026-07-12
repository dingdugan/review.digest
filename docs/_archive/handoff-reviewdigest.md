---
status: superseded
updated: 2026-07-12
---

> **已完成使命**：项目已开工，权威源现为 [CLAUDE.md](../../CLAUDE.md) + [IMPLEMENTATION_CHECKLIST.md](../../IMPLEMENTATION_CHECKLIST.md) + docs/ 下的 decision/research 文档。本文件是 2026-07-10 的开工 handoff，仅作历史回查。

# HANDOFF: reviewdigest（暂定名）

> 写于 2026-07-10，来自 idea 筛选 + 红军演习 session。本文档自包含，新 session 直接读这一份即可开工。

## 一句话

开源的 **App Store 评论周报 GitHub Action**：独立开发者 fork 模板仓库、填 app id，每周自动抓取多国家 storefront 的评论，LLM 聚类成「差评主题 / 崩溃反馈 / 功能请求」周报，以 GitHub Issue 形式送达。零服务器成本。

## 决策来龙去脉（为什么是它）

1. 一次性生成了 10 个「AI coding 一周可完成、解决真实需求、适合开源传播」的候选 idea。
2. 用 10 位真实 OPC 创始人（Pieter Levels / Jon Yongfook / Sindre Sorhus / Simon Willison 等）的公开方法论做 persona 红军攻击，并对每个赛道做了实时竞品搜索（2026-07-10）。
3. 多数 idea 被竞品调查击穿（如 LLM 用量看板败给 ccusage 4800★，macOS 听写败给 VoiceInk 等一片红海）。
4. **reviewdigest 以 72 分排第一**：红军没能打死它，反而打出了更清晰的形态。
5. 落选但可回收的备选：chatgrep（62，跨工具 AI 会话语义搜索+提炼）、depwatch（60，Dependabot PR 解说 bot）、mockfill（58，OpenAPI 真实感 mock）。

## 红军攻击结论（已内化为产品约束）

| 攻击 | 回应（= 产品决策） |
|---|---|
| AppFollow/Appfigures 已存在（Yongfook） | 它们 ~$199/月，开源缺口真实存在，这正是切入点 |
| Apple iOS 18.4 有官方评论摘要 | 那是给消费者看的商店页摘要，不是给开发者的运营周报，不冲突 |
| 独立 app 单国评论太少，聚类没意义（Levels） | 用**多国家 storefront + 多 app 聚合**化解——单国 3 条评论不值得看，30 个 storefront 加起来就看不过来了 |
| Google Play API 门槛高（开发者验证、服务账号） | **V1 砍掉 Google Play**，iOS-only |
| 独立开发者不想部署服务 | 形态定为 **GitHub Action 模板仓库**：fork → 改配置 → 完事。fork 数即传播数 |

## 已验证的竞争格局（2026-07-10 搜索）

- 商业品：AppFollow、Appfigures、Sensor Tower（贵，$199/月级）
- Apple 官方：iOS 18.4 起商店页有 LLM 评论摘要（面向消费者）— https://machinelearning.apple.com/research/app-store-review
- 现状文章证实痛点：独立开发者「每周一手动复制评论进表格」— https://dev.to/nexgendata/bulk-apple-app-store-google-play-review-monitoring-2026-guide-1ab8
- Indie Hackers 有人做过一次性的「500 条评论 AI 分析」工具，但**没有找到占主导的开源 GitHub Action 形态产品** ← 这是空位，开工前值得再花 10 分钟搜一次确认（搜 "app store review digest github action"）

## MVP 规格（一周 scope）

**形态**：GitHub template repository（`Use this template` 一键复制）

**配置**（仓库里一个 `reviewdigest.yaml`）：
- `apps:` app id 列表（支持多 app）
- `countries:` storefront 列表，或 `all`
- `schedule:` cron（默认每周一）
- `llm:` provider + model（API key 走 repo secret）
- `output:` github-issue（默认）；邮件/Telegram 留给社区 PR

**流水线**（一个 GitHub Actions workflow）：
1. 抓取评论。首选 iTunes customer reviews RSS 端点（每国返回最近约 500 条，无需鉴权）。`[TBD: 该 RSS 端点 2026 年现状需 day-1 实测验证；若已失效，fallback 到 App Store Connect API（需 API key，门槛升高但仍可行）]`
2. 与上期已见评论去重（状态存 repo 内的 JSON 文件，commit 回去——零外部存储）
3. LLM 聚类 + 摘要：新增差评主题、崩溃/bug 反馈、功能请求、值得回复的评论 top N、评分趋势
4. 产出 GitHub Issue，多语言评论翻译成配置的语言

**明确不做（V1）**：Google Play、网页 UI、数据库、评论回复功能、历史趋势图表。

## 一周计划

- D1：验证 RSS 端点（拿几个真实热门 app id 实测多国抓取），确定数据层方案 ← **最大技术风险，最先做**
- D2：抓取 + 去重 + 状态持久化
- D3：LLM 聚类摘要 prompt + Issue 渲染模板（这是产品品味所在，多花心思）
- D4：打包成 template repo，配置体验打磨（fork 后 5 分钟内跑通第一份周报）
- D5：README（英文主打）+ 示例周报截图 + demo 仓库
- D6：自测 dogfood + 边界情况（0 评论、纯外语评论、rate limit）
- D7：发布——Show HN / X / 少数派 / V2EX，README 里放「用 xx 分钟生成你的第一份周报」

## 开工时必须遵守的工程约定（来自用户全局 CLAUDE.md）

1. 新项目用骨架模板起手：`cp -r ~/.claude/templates/project-skeleton/. <project>/`，然后改 CLAUDE.md 顶部（项目名/stack/描述/docs index）
2. `IMPLEMENTATION_CHECKLIST.md` 是唯一 backlog，coding 前声明本次做哪几条，做完勾选并与代码同 commit
3. docs/ 扁平 + 前缀命名（spec- / decision- / research-），头部 frontmatter 带 status + updated
4. 建议第一份文档：`docs/decision-scope-v1.md`（把本 handoff 的红军结论快照进去）

## 待用户拍板的开放问题

1. **项目名**：reviewdigest 是占位名，开工前查一下 GitHub/npm 可用性
2. **dogfood 对象**：用户自己的 app 尚未上架（Apple Developer Individual 账号已注册）。V1 开发期先用公开热门 app 的 id 测试，上架后切自己的
3. **LLM 默认 provider**：建议默认 Anthropic + 允许配置，写 README 时给出每周成本估算（需实测 token 量后再写，不要拍脑袋）
4. **语言策略**：README 英文主打（国际传播）还是中英双语

## 背景补充

- 用户是 AI PM，另有 portfolio 项目 push.eval（LLM eval framework，位于 /Users/bytedance/Codes/push.eval）。reviewdigest 与其互补：一个是 eval 框架叙事，一个是「自己 app 的运营工具」dogfood 叙事
- 打分维度是「开源传播价值」；本项目同时服务用户即将上架的 app 的实际运营需求
