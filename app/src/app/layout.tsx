import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "DevPulse - 开发者脉搏",
  description: "开发者关注的 AI 热榜、GitHub 趋势、技术新闻，每日自动整理",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <body className="bg-gray-950 text-gray-100 min-h-screen">
        <nav className="border-b border-gray-800 bg-gray-950/80 backdrop-blur-sm sticky top-0 z-50">
          <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
            <a href="/" className="flex items-center gap-2 font-bold text-lg">
              <span className="text-2xl">⚡</span>
              <span>DevPulse</span>
            </a>
            <div className="flex items-center gap-6 text-sm">
              <a href="/" className="hover:text-blue-400 transition-colors">日报</a>
              <a href="/weekly/" className="hover:text-blue-400 transition-colors">周报</a>
              <a href="/about/" className="hover:text-blue-400 transition-colors">关于</a>
            </div>
          </div>
        </nav>
        <main className="max-w-6xl mx-auto px-4 py-6">
          {children}
        </main>
        <footer className="border-t border-gray-800 mt-12">
          <div className="max-w-6xl mx-auto px-4 py-6 text-sm text-gray-500 text-center">
            DevPulse — 自动收集，每日更新 · 数据来自 Hacker News · GitHub Trending
          </div>
        </footer>
      </body>
    </html>
  );
}
