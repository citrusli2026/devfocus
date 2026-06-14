# CLAUDE.md

## 项目概览

DevFocus（开发者聚焦）— 收集开发者关注的信息，整理成日报、周报、月报和年报。

架构参考 LLMCompare：`data/` Python 管线抓取处理数据 → `app/` Next.js 静态站展示。

## 目录结构

```
data/
  0-refer/    人工维护的参考表
  1-fetch/    抓取脚本（每个数据源一个）
  2-raw/      抓取产出（只读缓存）
  3-process/  处理管线（聚合、去重、打标签）
  4-final/    前端消费的 JSON
  pipeline.py 一键编排入口
  scripts/    辅助脚本

app/          Next.js 前端（静态导出）
```

## 数据源

第一批：
- Hacker News Top Stories（官方 API，无需 auth）
- GitHub Trending（HTML 解析）
- Product Hunt（后续接入）

## 常用命令

```bash
# 数据管线
cd data && python3 pipeline.py           # 全量跑
cd data && python3 pipeline.py --skip-fetch  # 跳过抓取

# 前端
cd app && npm run dev        # 开发
cd app && npm run build      # 构建
cd app && npm run test:e2e   # E2E 测试
```

## 关键约定

- 数据管线用 python3 标准库为主，最小依赖
- 前端 Next.js + Tailwind CSS + shadcn/ui
- 静态导出（output: export）
- 所有数据文件 JSON 格式
