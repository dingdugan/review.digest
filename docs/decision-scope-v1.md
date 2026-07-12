---
status: active
updated: 2026-07-10
---

# Decision: V1 范围（红军演习结论快照）

> 来源：2026-07-10 idea 筛选 + 10 位 OPC 创始人 persona 红军演习 session（HANDOFF-reviewdigest.md）。
> reviewdigest 以 72 分在 10 个候选 idea 中排第一。

## 一句话

开源的 **App Store 评论周报 GitHub Action**：fork 模板仓库、填 app id，每周自动抓取多国家 storefront 评论，LLM 聚类成周报，以 GitHub Issue 送达。零服务器成本。

## 红军攻击 → 产品决策

| 攻击 | 回应（= 产品决策） |
|---|---|
| AppFollow/Appfigures 已存在 | 它们 ~$199/月，开源缺口真实存在，这正是切入点 |
| Apple iOS 18.4 有官方评论摘要 | 那是给消费者看的商店页摘要，不是给开发者的运营周报，不冲突 |
| 独立 app 单国评论太少，聚类没意义 | **多国家 storefront + 多 app 聚合**化解 |
| Google Play API 门槛高 | **V1 砍掉 Google Play**，iOS-only |
| 独立开发者不想部署服务 | 形态定为 **GitHub Action 模板仓库**：fork → 改配置 → 完事 |

## V1 明确不做

Google Play、~~网页 UI~~、数据库、评论回复功能、~~历史趋势图表~~。
（邮件 / Telegram 输出留给社区 PR，V1 只做 GitHub Issue。）

> **2026-07-12 修订**：用户拍板加入 GUI —— 形态为 **GitHub Pages 静态仪表盘（历史周报 + 评分趋势图）+ 静态配置向导页**。
> 仍然零服务器（Pages 由同一个 Action 发布），不推翻「fork 即用」架构；被划掉的两项随之解禁。
> 本地桌面 GUI 与托管 SaaS 两个方向被评估后否决（形成第二产品形态 / 推翻零服务器立身之本）。

## 竞争格局（2026-07-10 搜索）

- 商业品：AppFollow、Appfigures、Sensor Tower（$199/月级）
- Apple 官方消费者侧摘要：https://machinelearning.apple.com/research/app-store-review
- 痛点佐证：https://dev.to/nexgendata/bulk-apple-app-store-google-play-review-monitoring-2026-guide-1ab8
- 未找到占主导的开源 GitHub Action 形态产品 ← 空位

## 开放问题（不阻塞开发）

1. 项目名 reviewdigest 为占位名，发布前查 GitHub/npm 可用性
2. dogfood：用户自己的 app 未上架，开发期用公开热门 app id 测试
3. README 英文主打（国际传播）
