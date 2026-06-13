# DevPulse — 开发者脉搏

自动收集开发者关注的信息，整理成日报、周报、月报和年报。

## 数据来源

- **Hacker News** — 全球最活跃的技术社区
- **GitHub Trending** — 每日热门开源项目
- 更多来源持续接入中...

## 项目结构

```
data/          Python 数据管线
  1-fetch/     抓取脚本
  2-raw/       原始数据缓存
  3-process/   聚合处理
  4-final/     前端消费的 JSON
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

## License

MIT
