// OG 图构建期字体（本地自托管，不依赖 Google Fonts 网络——国内网络
// 下 next/og 对中文字形的自动回退字体抓取会超时导致 build 失败）。
// 注意：satori 不支持 woff2（Unsupported OpenType signature wOF2），用 .woff。
import { readFileSync } from "node:fs";
import { join } from "node:path";

const rubikFile = (weight: 400 | 700) =>
  join(process.cwd(), "node_modules", "@fontsource/rubik", "files", `rubik-latin-${weight}-normal.woff`);

const notoSansScFile = (weight: 400 | 700) =>
  join(process.cwd(), "node_modules", "@fontsource/noto-sans-sc", "files",
    `noto-sans-sc-chinese-simplified-${weight}-normal.woff`);

// 模块级读取一次（构建期每个 OG 页共享），供 ImageResponse fonts 使用
export const ogFonts = [
  {
    name: "Rubik",
    data: readFileSync(rubikFile(700)),
    weight: 700 as const,
    style: "normal" as const,
  },
  {
    name: "NotoSansSC",
    data: readFileSync(notoSansScFile(700)),
    weight: 700 as const,
    style: "normal" as const,
  },
];

// 文本容器统一字体栈：拉丁走 Rubik，中文走 Noto Sans SC
export const OG_FONT_STACK = "Rubik, NotoSansSC, sans-serif";
