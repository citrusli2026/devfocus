import type { Metadata } from "next";
import { LanguageProvider } from "../components/language-provider";
import { Navbar } from "../components/navbar";
import { Footer } from "../components/footer";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL("https://www.devfocus.cc"),
  title: {
    default: "DevFocus - 开发者聚焦",
    template: "%s - DevFocus",
  },
  description: "开发者关注的 AI 热榜、GitHub 趋势、技术新闻，每日自动整理",
};

const themeScript = `(function(){try{document.documentElement.classList.add("light");}catch(e){}})();`;
const localeScript = `(function(){try{var l=localStorage.getItem("devfocus-locale");document.documentElement.lang=l==="en"?"en":"zh-CN";}catch(e){}})();`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN" className="h-full antialiased" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
        <script dangerouslySetInnerHTML={{ __html: localeScript }} />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Rubik:wght@400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="h-full" style={{ background: "var(--surface-base)" }}>
        <LanguageProvider>
          <div className="flex flex-col min-h-full">
            <Navbar />
            <main className="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 py-8">
              {children}
            </main>
            <Footer />
          </div>
        </LanguageProvider>
      </body>
    </html>
  );
}
