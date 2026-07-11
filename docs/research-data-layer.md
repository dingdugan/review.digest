---
status: active
updated: 2026-07-10
---

# Research: 评论数据层实测（D1 风险验证）

> 2026-07-10 实测。结论：**旧 iTunes RSS 已死，改用 apps.apple.com 无鉴权 web API。**

## ❌ iTunes customer reviews RSS（handoff 里的首选方案）——已失效

```
https://itunes.apple.com/{cc}/rss/customerreviews/page=1/id={id}/sortby=mostrecent/json
```

对 WhatsApp / Instagram / Spotify / Telegram / YouTube / ChatGPT 全部返回**空 feed**（约 870 字节，只有 feed 元数据无 entries）。XML 变体、无 page 参数变体、`?cc=` 变体同样为空。判定端点已被 Apple 掏空。

## ❌ amp-api-edge.apps.apple.com —— 需要 Bearer JWT

`https://amp-api-edge.apps.apple.com/v1/catalog/us/apps/{id}/reviews` 直接访问返回 401。
JWT 不再嵌在页面 meta 或 HTML 里（旧的 `web-experience-app/config/environment` meta tag 已移除），由 JS 运行时 `jwtProvider.getNonSearchJwt()` 注入，提取成本高且脆弱。**不采用。**

## ✅ apps.apple.com 第一方 API 代理 —— 采用（V1 数据层）

```
https://apps.apple.com/api/apps/v1/catalog/{country}/apps/{appId}/reviews
    ?platform=web        # 必填，缺了返回 400
    &sort=recent         # 按时间倒序（实测唯一生效的取值；mostrecent/newest 等均无效）
    &limit=20            # 实测上限 20，>20 返回空
    &offset=0            # 分页；响应里的 next 字段给出下一页相对路径
    &l=en-US             # 界面语言（不影响评论原文）
```

实测确认（2026-07-10，Spotify id=324684580）：
- **无需任何鉴权** —— 这是 App Store 网页版自己的第一方代理，页面 see-all=reviews 场景在用
- `sort=recent` 返回当天最新评论；默认排序是 most helpful（会返回几年前的）
- 多国家 storefront 生效：us / jp / de 均验证返回对应语言评论
- 响应结构：`{"next": "/v1/catalog/us/apps/{id}/reviews?l=en-US&offset=20", "data": [{"id", "type": "user-reviews", "attributes": {"date", "rating", "title", "review", "userName", "isEdited", "developerResponse"?}}]}`

### 注意事项

- **必须带浏览器 User-Agent**：默认 curl UA 会 429（实测）。带 Safari UA + 请求间隔 ≥1s 稳定
- 429 处理：指数退避重试
- 该端点非官方文档化，有变更风险 → fetch 层做成可替换 backend，README 里注明
- 评分总量/均分快照走官方 lookup API（稳定、文档化）：
  `https://itunes.apple.com/lookup?id={id}&country={cc}` → `averageUserRating`, `userRatingCount`

## Fallback 阶梯（若 web API 变更）

1. App Store Connect API `GET /v1/apps/{id}/customerReviews`（官方、稳定、需开发者自己的 ASC key，只能看自己的 app）——对目标用户（看自己 app）完全可行，配置门槛 +3 个 secret
2. RSS 端点若复活可加回作为零依赖 backend
