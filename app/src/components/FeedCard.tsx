"use client";

import { useState } from "react";
import { FeedItem } from "../types";
import { useTranslation } from "../lib/i18n";
import { cn } from "../lib/utils";
import { ExternalLink, MessageSquare, Star, ArrowUp, Share2, Link as LinkIcon } from "lucide-react";

function SourceBadge({ source }: { source: string }) {
  const cfg: Record<string, { label: string; cls: string }> = {
    hackernews: { label: "HN", cls: "bg-[#ff6600]/8 text-[#ff6600] border-[#ff6600]/15" },
    github_trending: { label: "GitHub", cls: "bg-accent-emerald/8 text-accent-emerald border-accent-emerald/15" },
    producthunt: { label: "PH", cls: "bg-[#da552f]/8 text-[#da552f] border-[#da552f]/15" },
    juejin: { label: "掘金", cls: "bg-[#1e80ff]/8 text-[#1e80ff] border-[#1e80ff]/15" },
    zhihu: { label: "知乎", cls: "bg-[#0066ff]/8 text-[#0066ff] border-[#0066ff]/15" },
  };
  const c = cfg[source] || { label: source, cls: "bg-muted text-muted-foreground border-border" };
  return (
    <span className={cn("inline-flex items-center text-[11px] font-semibold px-2 py-0.5 rounded-md border", c.cls)}>
      {c.label}
    </span>
  );
}

function ScorePill({ score, source }: { score: number; source: string }) {
  if (score === 0) return null;
  const isGH = source === "github_trending";
  const arrowColor = source === "juejin" ? "text-[#1e80ff]"
    : source === "zhihu" ? "text-[#0066ff]"
    : "text-[#ff6600]";
  return (
    <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-text-muted tabular-nums bg-surface-hover px-2 py-0.5 rounded-md">
      {isGH ? <Star className="h-3 w-3 fill-amber-400 text-amber-400" /> : <ArrowUp className={`h-3 w-3 ${arrowColor}`} />}
      {score.toLocaleString()}
      {isGH && <span className="text-text-dim font-normal">/d</span>}
    </span>
  );
}

function SummaryBlock({ zh, en }: { zh: string; en: string }) {
  const { locale } = useTranslation();
  if (!zh && !en) return null;
  const text = locale === "en" ? (en || zh) : (zh || en);
  // Check if it's old pipe-separated format
  const points = text.split(/\s*\|\s*/).filter(Boolean);
  if (points.length > 1) {
    // Legacy format with key points
    return (
      <ul className="mt-2 space-y-1.5">
        {points.map((p, i) => (
          <li key={i} className="flex items-start gap-2 text-sm text-text-secondary leading-relaxed">
            <span className="mt-1.5 w-1 h-1 rounded-full bg-accent-violet/60 shrink-0" />
            <span>{p.trim()}</span>
          </li>
        ))}
      </ul>
    );
  }
  // New narrative style
  return <p className="text-sm text-text-secondary mt-2 leading-relaxed">{text}</p>;
}

function ShareButtons({ item, locale }: { item: FeedItem; locale: string }) {
  const [copied, setCopied] = useState(false);

  const tweetText = encodeURIComponent(
    `${item.title} — DevFocus\n${locale === "zh" ? "via DevFocus 开发者聚焦" : ""}`
  );
  const shareUrl = encodeURIComponent(item.url);

  const copyLink = async () => {
    try {
      await navigator.clipboard.writeText(item.url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {}
  };

  return (
    <span className="inline-flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity ml-auto">
      {/* X/Twitter */}
      <a
        href={`https://twitter.com/intent/tweet?text=${tweetText}&url=${shareUrl}`}
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex items-center justify-center h-6 w-6 rounded-md text-text-dim hover:text-text-primary hover:bg-surface-hover transition-all"
        title="Share on X / Twitter"
        aria-label="Share on X / Twitter"
      >
        <Share2 className="h-3 w-3" />
      </a>
      {/* Copy link */}
      <button
        onClick={copyLink}
        className="relative inline-flex items-center justify-center h-6 w-6 rounded-md text-text-dim hover:text-text-primary hover:bg-surface-hover transition-all"
        title={copied ? "Copied!" : "Copy link"}
        aria-label="Copy link"
      >
        {copied ? (
          <span className="text-[10px] font-semibold text-accent-emerald">✓</span>
        ) : (
          <LinkIcon className="h-3 w-3" />
        )}
      </button>
    </span>
  );
}

export function FeedCard({ item, rank }: { item: FeedItem; rank?: number }) {
  const { t, locale } = useTranslation();
  let domain = "";
  try { domain = new URL(item.url).hostname.replace("www.", ""); } catch {}

  return (
    <article
      className="group relative bg-surface-card rounded-xl border border-surface-border
        hover:border-accent-violet/30 hover:shadow-md
        transition-all duration-200 overflow-hidden"
    >
      {/* Rank bar */}
      {rank !== undefined && rank <= 3 && (
        <div className={cn(
          "absolute left-0 top-0 bottom-0 w-1.5 rounded-l-xl",
          rank === 1 && "bg-gradient-to-b from-amber-400 to-amber-300",
          rank === 2 && "bg-gradient-to-b from-gray-400 to-gray-300",
          rank === 3 && "bg-gradient-to-b from-amber-600 to-amber-500",
        )} />
      )}

      <div className="flex items-start gap-3 sm:gap-4 md:gap-5 p-3 sm:p-4 md:p-5">
        {/* Rank number */}
        {rank !== undefined && (
          <div className={cn(
            "flex items-center justify-center min-w-[2rem] h-8 rounded-lg text-sm font-bold tabular-nums",
            rank <= 3
              ? "bg-accent-violet/10 text-accent-violet"
              : "bg-surface-hover text-text-dim"
          )}>
            {rank}
          </div>
        )}

        <div className="flex-1 min-w-0">
          {/* Title */}
          <h3 className="font-semibold text-[14px] sm:text-[15px] text-text-primary leading-snug group-hover:text-accent-violet transition-colors">
            <a
              href={item.url}
              target="_blank"
              rel="noopener noreferrer"
              className="hover:underline decoration-accent-violet/30 underline-offset-2"
            >
              {item.title}
              <ExternalLink className="inline-block h-3.5 w-3.5 ml-1.5 opacity-0 group-hover:opacity-50 transition-opacity -translate-y-px" />
            </a>
          </h3>

          {/* Meta row */}
          <div className="flex items-center gap-2 mt-1.5 flex-wrap">
            <SourceBadge source={item.source} />
            <ScorePill score={item.score} source={item.source} />
            {item.comments > 0 && (
              <span className="inline-flex items-center gap-1 text-[11px] text-text-dim">
                <MessageSquare className="h-3 w-3" />
                {item.comments.toLocaleString()}
              </span>
            )}
            {domain && (
              <span className="text-[11px] text-text-dim px-1.5 py-0.5 rounded bg-surface-hover">
                {domain}
              </span>
            )}
            {item.author && (
              <span className="text-[11px] text-text-dim">
                {t("common.by")} {item.author}
              </span>
            )}
            {item.first_seen && (
              <span className="text-[11px] text-text-dim px-1.5 py-0.5 rounded bg-surface-hover" title={t("common.firstSeen") || "首次上榜"}>
                📅 {item.first_seen}
              </span>
            )}
            <ShareButtons item={item} locale={locale} />
          </div>

          {/* Summary — sentence-by-sentence */}
          <SummaryBlock zh={item.summary_zh || ""} en={item.summary_en || ""} />
        </div>
      </div>
    </article>
  );
}

export function FeedList({ items, showRank = true, rankOffset = 0 }: { items: FeedItem[]; showRank?: boolean; rankOffset?: number }) {
  return (
    <div className="space-y-2 sm:space-y-2.5">
      {items.map((item, i) => (
        <FeedCard key={item.id} item={item} rank={showRank ? rankOffset + i + 1 : undefined} />
      ))}
    </div>
  );
}
