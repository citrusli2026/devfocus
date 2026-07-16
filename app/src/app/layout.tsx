import type { Metadata } from "next";
import { Analytics } from "@vercel/analytics/next";
import { LanguageProvider } from "../components/language-provider";
import { Navbar } from "../components/navbar";
import { Footer } from "../components/footer";
import "./globals.css";

const SITE_URL = "https://www.devfocus.cc";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: "DevFocus - 开发者聚焦",
    template: "%s - DevFocus",
  },
  description: "开发者关注的 AI 热榜、GitHub 趋势、技术新闻、36氪、知乎科技，每日自动整理的一站式技术资讯聚合站",
  keywords: ["开发者资讯", "AI 热榜", "GitHub 趋势", "技术新闻", "Hacker News", "开源项目", "每日精选", "程序员日报"],
  authors: [{ name: "DevFocus" }],
  creator: "DevFocus",
  publisher: "DevFocus",
  robots: { index: true, follow: true },
  alternates: {
    canonical: SITE_URL,
  },
  openGraph: {
    type: "website",
    locale: "zh_CN",
    alternateLocale: "en_US",
    siteName: "DevFocus",
    title: "DevFocus - 开发者聚焦",
    description: "每日自动整理的开发者资讯：AI 热榜、GitHub 趋势、技术新闻，一站式看完",
    url: SITE_URL,
    images: [{ url: `${SITE_URL}/og.png`, width: 1200, height: 630, alt: "DevFocus" }],
  },
  twitter: {
    card: "summary_large_image",
    title: "DevFocus - 开发者聚焦",
    description: "每日自动整理的开发者资讯：AI 热榜、GitHub 趋势、技术新闻",
    images: [`${SITE_URL}/og.png`],
  },
};

const themeScript = `(function(){try{document.documentElement.classList.add("light");}catch(e){}})();`;
const localeScript = `(function(){try{var l=localStorage.getItem("devfocus-locale");document.documentElement.lang=l==="en"?"en":"zh-CN";}catch(e){}})();`;
const jsonLd = {
  "@context": "https://schema.org",
  "@type": "WebSite",
  name: "DevFocus - 开发者聚焦",
  alternateName: "DevFocus - Developer Focus",
  url: SITE_URL,
  description: "每日自动整理的开发者资讯聚合站：AI 热榜、GitHub 趋势、技术新闻",
  inLanguage: ["zh-CN", "en"],
  potentialAction: {
    "@type": "SearchAction",
    target: {
      "@type": "EntryPoint",
      urlTemplate: `${SITE_URL}/search?q={search_term_string}`,
    },
    "query-input": "required name=search_term_string",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN" className="h-full antialiased" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
        <script dangerouslySetInnerHTML={{ __html: localeScript }} />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Rubik:wght@400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="h-full" style={{ background: "var(--surface-base)" }}>
        <LanguageProvider>
          <a
            href="#main-content"
            className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-[100] focus:px-4 focus:py-2 focus:bg-accent-violet focus:text-white focus:rounded-lg focus:shadow-lg"
          >
            跳到主要内容 / Skip to main content
          </a>
          <div className="flex flex-col min-h-full">
            <Navbar />
            <main id="main-content"
              className="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6"
              style={{ background: "radial-gradient(ellipse at 50% 0%, rgba(106,95,193,0.12) 0%, transparent 70%)" }}
            >
              <div className="py-8">
                {children}
              </div>
            </main>
            <Footer />
          </div>
        </LanguageProvider>
        <Analytics />
      </body>
    </html>
  );
}
