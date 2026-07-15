# 参与贡献

[English](CONTRIBUTING.md) | 简体中文

感谢你帮独立开发者把评论监控这件事变成免费的。

## 开发环境

```bash
git clone https://github.com/dingdugan/review.digest
cd review.digest
pip install -r requirements.txt
python -m pytest tests/ -q          # 32 个测试,应当全绿
python -m reviewdigest --dry-run --no-llm   # 用真实 App Store 数据冒烟
```

无 SDK、无构建步骤:Python 3.11+、`requests`、`PyYAML`、`Markdown`。

## 代码地图

| 职责 | 文件 | 说明 |
|---|---|---|
| 评论抓取 | `reviewdigest/fetch.py` | Apple web API 客户端 —— 分页、退避、去重窗口 |
| 配置与校验 | `reviewdigest/config.py` | `reviewdigest.yaml` 的全部选项 |
| 去重 / 评分历史 | `reviewdigest/state.py` | JSON 存 `state/`,由 workflow 回写仓库 |
| LLM 调用 | `reviewdigest/llm.py` | 裸 REST,Anthropic + OpenAI 兼容 |
| 分析 prompt | `reviewdigest/digest.py` | 产品品味所在 |
| 周报 markdown | `reviewdigest/render.py` | 统计头 + 各小节 |
| 编排 / 投递 | `reviewdigest/main.py` | CLI + 建 GitHub Issue |
| 仪表盘 | `reviewdigest/site.py` + `site/` | 静态 HTML、内联 SVG 图表、无 JS 框架 |

## 最想要的贡献

- **新输出渠道**:邮件、Telegram、Slack —— 在 `main.py` 投递步骤加分支(保持零服务器:webhook/SMTP 走 secrets)
- **Google Play 支持**:第二个抓取后端;需要官方 Android Publisher API(服务账号)
- **Prompt 改进**:更好的聚类、更准的「值得回复」—— 用 `--dry-run` 对真实 app 测试
- **更多周报语言的实测**:prompt 会翻译引用;发现某语言效果差请开 issue

## 基本守则

- 零服务器就是零服务器:不引入数据库、不引入托管组件,状态存仓库里
- LLM 调用不引 SDK —— 裸 REST 让每个 fork 都容易审计
- 密钥只走环境变量 / repo secrets,绝不进代码或配置
- 每个 PR:`python -m pytest tests/ -q` 全绿,新行为配新测试
- 诚实输出是产品功能:prompt 绝不允许编造计数或引用

## 发版(维护者)

仓库本身就是产品 —— 合进 `main` 就等于发布给之后每一次 "Use this template"。模板卫生很重要:真实 app 配置、周报、state 数据一律不进 `main`。
