# CLAUDE.md

## 项目概览

DevFocus（开发者聚焦）— 收集开发者关注的信息，整理成日报、周报、月报和年报。

架构：`data/` Python 管线抓取处理数据 → `app/` Next.js 静态站展示。

## 目录结构

```
data/
  1-fetch/    抓取脚本（每个数据源一个，失败保留旧缓存）
  2-raw/      抓取产出（只读缓存，gitignore）
  3-process/  处理管线（aggregate/summarize/enrich/build_stats/build_trends/
              build_search_index；_shared.py 共享工具）
  4-final/    前端消费的 JSON（提交到仓库）
  5-history/  每日历史快照（30 天滚动）
  pipeline.py 一键编排入口
  scripts/    辅助脚本（generate_rss/validate_data/check_history/backfill_history_summaries）

app/          Next.js 前端（静态导出）
```

## 数据源

当前 8 源：Hacker News、GitHub Trending、Product Hunt、掘金、知乎、36氪、InfoQ、V2EX。

## 常用命令

```bash
# 数据管线（--skip-fetch 跳过抓取，--skip-summarize 跳过 LLM，--dry-run 打印计划）
cd data && python3 pipeline.py

# 前端
cd app && npm run dev        # 开发
cd app && npm run build      # 构建（字体已自托管，不依赖 Google Fonts）
cd app && npm run test:e2e   # E2E 测试

# 校验
cd data && python3 scripts/validate_data.py
cd data && python3 scripts/check_history.py --days 30   # 快照连续性（有空洞发 warning）
cd data/3-process && python3 -m unittest discover -p "test_*.py"
```

## 关键约定

- 数据管线用 python3 标准库为主，最小依赖；跨脚本共享工具放 `3-process/_shared.py`
- 抓取失败一律保留旧缓存（新鲜空文件会绕过 aggregate 的缺席检测）
- 2-raw 不提交；4-final、5-history、app/src/data 提交（前端构建的数据源）
- 5-history 快照日期锚定到 cron 槽位（`_shared.resolve_target_date`），不是运行时日期：
  GitHub schedule 常延迟 2~4 小时，按运行时日期命名会跨零点吞掉一整天。
  改 `daily.yml` 的 cron 必须同步 `PIPELINE_SLOT_UTC_HOUR` 与 `DEFAULT_SLOT_UTC_HOUR`
- 前端 Next.js + Tailwind CSS v4 + shadcn/ui 风格；静态导出（output: export）
- 所有数据文件 JSON 格式；时间统一 ISO 字符串，域名统一小写去前缀 www.
