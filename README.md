# DevFocus — 开发者聚焦

每天自动从 8 个数据源收集开发者最值得看的内容，附带中英双语摘要。不用自己到处刷，一站看完。

## 数据来源

- **Hacker News** — 全球最活跃的技术社区，每日热门话题
- **GitHub Trending** — 每日/每周/每月热门开源项目
- **Product Hunt** — 每日热门新产品（需 `PH_TOKEN`）
- **掘金 / 知乎 / 36氪 / InfoQ / V2EX** — 中文技术社区热榜

## 功能

- 每日日榜（每源 Top 10，跨源按源内归一化分排序）+ 月榜 + 周榜
- 每篇文章有中英双语摘要（DeepSeek LLM，带输入指纹防重复扣费）
- 话题趋势热力图（30 天窗口）、全站搜索（最近 30 天索引）、标签/域名聚合页
- 历史归档（30 天快照）、RSS 订阅、中英双语一键切换、亮/暗主题
- 构建期数据注入 + 运行时搜索索引，静态导出零 API

## 项目结构

```
data/            Python 数据管线（python3 标准库，最小依赖）
  1-fetch/       抓取脚本（每源一个，含重试、反爬降级、失败保留旧缓存）
  2-raw/         抓取产出（只读缓存，gitignore）
  3-process/     处理管线（aggregate 聚合 → summarize 摘要 → enrich 打标签
                 → stats/trends/search-index 构建；_shared.py 共享工具）
  4-final/       前端消费的 JSON（提交到仓库）
  5-history/     每日历史快照（30 天滚动）
  scripts/       generate_rss / validate_data / backfill 等辅助脚本
  pipeline.py    一键编排入口

app/             Next.js 前端（静态导出，Tailwind v4，自托管字体）
```

## 快速开始

```bash
# 1. 拉取数据（离线重算：--skip-fetch --skip-summarize；预览计划：--dry-run）
cd data && python3 pipeline.py

# 2. 启动前端
cd app && npm run dev

# 3. 构建静态站（不依赖 Google Fonts 网络）
cd app && npm run build
```

## 环境变量

| 变量 | 用途 |
|------|------|
| `DEEPSEEK_API_KEY` / `OPENAI_API_KEY` | 摘要 LLM（可选，缺省走模板降级） |
| `PH_TOKEN`（或 `data/.ph_token`） | Product Hunt GraphQL |
| `NEXT_PUBLIC_SUBSCRIBE_URL` | 邮件订阅后端（可选，静态站建议 Formspree 等） |

## 测试

```bash
cd data/3-process && python3 -m unittest test_enrich.py   # 单测
cd data && python3 scripts/validate_data.py               # 数据校验
cd app && npm run lint && npx tsc --noEmit                # 前端静态检查
cd app && npm run test:e2e                                # Playwright E2E
```

## 部署

静态导出到 `app/out/`，可部署到 Vercel、GitHub Pages、Cloudflare Pages 等。
每日 00:00 UTC 由 GitHub Actions（`.github/workflows/daily.yml`）自动抓取、
生成、构建并提交数据。

## License

MIT
