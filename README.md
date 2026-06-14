# DevFocus — 开发者聚焦

每天自动从 Hacker News 和 GitHub 收集最值得看的内容，附带中文摘要。不用自己到处刷，一站看完。

## 数据来源

- **Hacker News** — 全球最活跃的技术社区，每日热门话题
- **GitHub Trending** — 每日热门开源项目，发现新工具和框架

## 功能

- 每日精选 20 条（HN 10 + GitHub 10）
- 每篇文章有中英文摘要
- 中英双语界面，一键切换
- 亮色 lavender 主题
- 移动端适配

## 项目结构

```
data/          Python 数据管线
  1-fetch/     抓取脚本（HN + GitHub，含重试和 API 降级）
  2-raw/       原始数据缓存
  3-process/   聚合 + 摘要生成
  4-final/     前端消费的 JSON
  5-history/   历史快照（按日期累计）
  pipeline.py  一键编排

app/           Next.js 前端（静态导出）
```

## 快速开始

```bash
# 1. 拉取数据
cd data && python3.11 pipeline.py

# 2. 启动前端
cd app && npm run dev

# 3. 构建静态站
cd app && npm run build
```

## 部署

静态导出到 `app/out/`，可部署到 Vercel、GitHub Pages、Cloudflare Pages 等。

域名：devfocus.dev

## License

MIT
