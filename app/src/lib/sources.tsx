import { GitHubIcon } from "../components/icons";

export type SourceMeta = {
  labelKey: string;
  shortLabel: string;
  icon: React.ReactNode;
  color: string;
  bg: string;
};

export const SOURCE_ORDER = [
  "hackernews",
  "github_trending",
  "producthunt",
  "juejin",
  "zhihu",
  "36kr",
  "infoq",
];

export const SOURCE_META: Record<string, SourceMeta> = {
  all: {
    labelKey: "today.allSources",
    shortLabel: "All",
    icon: null,
    color: "text-accent-violet",
    bg: "bg-accent-violet/10",
  },
  hackernews: {
    labelKey: "today.hnTitle",
    shortLabel: "Hacker News",
    icon: <span className="text-sm">🔥</span>,
    color: "text-[#ff6600]",
    bg: "bg-[#ff6600]/10",
  },
  github_trending: {
    labelKey: "today.ghTitle",
    shortLabel: "GitHub",
    icon: <GitHubIcon className="h-4 w-4" />,
    color: "text-accent-emerald",
    bg: "bg-accent-emerald/10",
  },
  producthunt: {
    labelKey: "today.phTitle",
    shortLabel: "Product Hunt",
    icon: <span className="text-sm">🚀</span>,
    color: "text-[#da552f]",
    bg: "bg-[#da552f]/10",
  },
  juejin: {
    labelKey: "today.juejinTitle",
    shortLabel: "掘金",
    icon: <span className="text-sm">📘</span>,
    color: "text-[#1e80ff]",
    bg: "bg-[#1e80ff]/10",
  },
  zhihu: {
    labelKey: "today.zhihuTitle",
    shortLabel: "知乎",
    icon: <span className="text-sm">💬</span>,
    color: "text-[#0066ff]",
    bg: "bg-[#0066ff]/10",
  },
  "36kr": {
    labelKey: "today.krTitle",
    shortLabel: "36氪",
    icon: <span className="text-sm">📰</span>,
    color: "text-[#0f66ff]",
    bg: "bg-[#0f66ff]/10",
  },
  infoq: {
    labelKey: "today.infoqTitle",
    shortLabel: "InfoQ",
    icon: <span className="text-sm">📡</span>,
    color: "text-[#ef4444]",
    bg: "bg-[#ef4444]/10",
  },
};

export function getSourceMeta(source: string): SourceMeta {
  return (
    SOURCE_META[source] ?? {
      labelKey: "",
      shortLabel: source,
      icon: <span className="text-sm">📎</span>,
      color: "text-text-secondary",
      bg: "bg-surface-hover",
    }
  );
}
