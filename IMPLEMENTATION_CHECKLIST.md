# Implementation Checklist

> 规则：每条「动词 + 屏幕/文件 + 行为」+ 验收 + 证据三件套。
> 没填证据不准打 `[x]` —— Stop hook 会自动审计、拦截。

## 模板（复制下面一段开始一条新条目）

```markdown
- [ ] <动词 + 屏幕/文件 + 行为>
      验收: <可观察的标准>
      证据: <填截图路径 / file:line / 测试名>
```

---

## Active

- [ ] 发布前：确认项目名可用性 + README 放示例周报截图 + 建 demo 仓库（handoff D5/D7，非 MVP 阻塞项）
      验收: GitHub 上创建 template repo，Actions 实际跑通建 Issue
      证据: <填 repo URL>

## Done

- [x] 实现 reviewdigest/site.py 静态仪表盘生成器（index + 每期周报页 + 评分趋势 SVG）
      验收: 从 digests/*.md + state/state.json 生成 _site/；无周报时渲染空态；深色模式可读
      证据: tests/test_site.py 5 个测试全绿；本地 headless 浏览器截图验证（index 趋势图三国线 + 周报页完整渲染，console 无错误）

- [x] 实现 site/setup.html 配置向导（搜 app 名出 id、选国家/语言、生成 yaml）
      验收: 纯静态无依赖；iTunes 搜索跨域可用（CORS 或 JSONP）；生成的 yaml 可直接粘贴使用
      证据: iTunes search API CORS 实测通过（Access-Control-Allow-Origin 回显）；headless 浏览器实测搜 "overcast" 出 5 结果、点击后 YAML 生成 id 888422857 带名字注释

- [x] 修改 main.py + .gitignore 让周报 markdown 历史入库（digests/ 提交进仓库）
      验收: 非 dry-run 每次运行都落一份 digests/digest-日期.md；.gitignore 不再忽略
      证据: reviewdigest/main.py save_digest_file（github-issue 输出也落盘）；.gitignore 改为忽略 _site/

- [x] 修改 .github/workflows/digest.yml 加 Pages 构建与部署 job
      验收: digest job 提交 digests/+state/；site job 上传 artifact 并 deploy-pages；未开 Pages 时不阻塞周报
      证据: .github/workflows/digest.yml（deploy-pages job 带 continue-on-error）；yaml.safe_load 校验通过

- [x] 更新 README（启用 Pages 的一步设置 + 仪表盘/向导截图位）
      验收: 用户照 README 能开出仪表盘
      证据: README.md "Bonus: your review dashboard" 段（Settings → Pages → GitHub Actions 一步 + 未启用不影响周报说明）

- [x] Dogfood: 用已有 TikTok 周报本地构建站点并在浏览器验证
      验收: index 可见趋势图与周报列表，周报页渲染正确
      证据: headless 浏览器三页截图验证（dash_index / dash_digest / dash_setup），修复 app 名显示与重复 meta 两处后复验通过

- [x] Dogfood: 真实 app 端到端跑通一份周报（LLM 模式）
      验收: 产出的周报 markdown 人读质量过关，评论翻译正确
      证据: digests/digest-2026-07-12.md（TikTok 237 条，claude-opus-4-8）；3/3 引用抽查与原始评论逐字吻合，DE 评论正确翻译并保留国家标

- [x] 验证评论数据层并写 docs/research-data-layer.md（D1 最大风险）
      验收: 真实 app id 多国抓取实测有结论，RSS 死活有定论，选定方案写入文档
      证据: docs/research-data-layer.md（RSS 实测全空已死；amp-api 需 JWT 弃用；采用 apps.apple.com/api 无鉴权代理，us/gb/de/jp/au 实测通过，sort=recent 返回当天评论）

- [x] 实现 reviewdigest/config.py 加载并校验 reviewdigest.yaml
      验收: 缺 app id / 非法 country 报人话错误；countries 支持列表与 all
      证据: tests/test_config.py 7 个测试全绿（test_missing_apps_is_human_error / test_bad_country_named_in_error / test_countries_major_expands 等）

- [x] 实现 reviewdigest/fetch.py 抓取多国家最新评论（分页+去重窗口+429 退避）
      验收: 真实 app id 抓到近 N 天多国评论；请求带 UA 与间隔；429 自动重试
      证据: reviewdigest/fetch.py:113 (fetch_new_reviews) + tests/test_fetch.py 6 个测试；实跑 Spotify 4 国 400 条、Overcast 5 国 16 条，429 自动退避恢复（见会话日志 2026-07-10）

- [x] 实现 reviewdigest/state.py 去重状态与评分快照持久化到 state/state.json
      验收: 二次运行同样评论不重复出现；评分历史追加快照
      证据: tests/test_state.py 4 个测试；实跑 Overcast 第二轮 5 国全部 0 new（dedup 生效），state.json seen keys {us:14, gb:1, de:1} + 评分快照

- [x] 实现 reviewdigest/llm.py 裸 REST 调 Anthropic / OpenAI 兼容端点
      验收: 无 SDK 依赖；key 从环境变量读；请求失败有重试与人话报错
      证据: reviewdigest/llm.py:30 (complete) / :46 (_post_with_retry 指数退避) / :24 无 key 人话报错；请求形状对照 claude-api 参考核验（x-api-key + anthropic-version 2023-06-01）

- [x] 实现 reviewdigest/digest.py 聚类摘要 prompt（差评主题/崩溃/功能请求/值得回复）
      验收: prompt 含真实评论与诚实计数约束；超量时负面优先采样
      证据: tests/test_digest.py 4 个测试（test_analyze_prompt_contains_reviews_and_honest_counts / test_select_for_llm_prioritizes_negatives_when_over_cap）

- [x] 实现 reviewdigest/render.py 周报 markdown 渲染（统计头 + LLM 正文 + 评分趋势）
      验收: 0 评论 / 无 LLM key（raw 模式）/ 正常三种情况都渲染合法 markdown
      证据: tests/test_render.py 5 个测试（test_stats_no_reviews / test_raw_reviews_groups_by_rating_worst_first / test_stats_normal 含 WoW delta）

- [x] 实现 reviewdigest/main.py CLI（--dry-run / --no-llm / --output）与 GitHub Issue 投递
      验收: dry-run 输出到 stdout/文件；Action 里能建 Issue（REST + GITHUB_TOKEN）
      证据: reviewdigest/main.py:150 (create_github_issue REST) / :186 (CLI args)；实跑 --no-llm 输出 stdout 与 file 两种模式成功（digest-2026-07-11.md）

- [x] 编写 .github/workflows/digest.yml（cron + 手动触发 + state 回写 commit）
      验收: workflow 语法合法（yaml 校验通过），权限最小化
      证据: .github/workflows/digest.yml:9-11 (permissions: contents/issues write only)；python yaml.safe_load 校验通过

- [x] 编写 reviewdigest.yaml 示例配置 + README.md（英文，5 分钟上手路径）
      验收: README 含 Use this template → secrets → 首份周报全路径；成本估算已给区间（精确数字待 LLM 实跑后校准）
      证据: README.md（"Get your first digest in 5 minutes" 四步 + 配置参考表 + Caveats）

- [x] 编写 tests/ 单元测试（fetch 解析、state 去重、render 三态）
      验收: python -m pytest 全绿
      证据: 26 passed（tests/test_fetch.py 6 + test_state.py 4 + test_render.py 5 + test_config.py 7 + test_digest.py 4），2026-07-10

- [x] Dogfood: 真实 app 端到端跑通（raw 模式，无 LLM）
      验收: 多国抓取→去重→渲染→输出文件全链路可用
      证据: Overcast (888422857) 5 国实跑两轮：第一轮 16 条新评论产出 digest-2026-07-11.md，第二轮全 0（去重生效）
