# DevFocus 前端

每日技术资讯聚合站的前端，Next.js App Router 静态导出（`output: export`），Tailwind CSS，自研中英双语 i18n。数据由 `../data` 的 Python 管线构建期生成到 `src/data/*.json`。

## 常用命令

```bash
npm run dev        # 开发服务器
npm run build      # 静态导出到 out/
npm start          # 用 http-server 预览 out/（端口 3000）
npm run lint       # ESLint
npm run test:e2e   # Playwright E2E（自动构建并用 http-server 起本地服务）
```

项目整体说明见仓库根目录 `../README.md`。
