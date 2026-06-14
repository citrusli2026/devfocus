"use client";

import { FeedItem } from "../types";
import { useTranslation } from "../lib/i18n";
import { cn } from "../lib/utils";
import { ExternalLink, MessageSquare, Star, ArrowUp } from "lucide-react";

function SourceBadge({ source }: { source: string }) {
  const cfg: Record<string, { label: string; cls: string }> = {
    hackernews: { label: "HN", cls: "bg-[#ff6600]/8 text-[#ff6600] border-[#ff6600]/15" },
    github_trending: { label: "GitHub", cls: "bg-accent-emerald/8 text-accent-emerald border-accent-emerald/15" },
    reddit: { label: "Reddit", cls: "bg-[#ff4500]/8 text-[#ff4500] border-[#ff4500]/15" },
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
  return (
    <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-text-muted tabular-nums bg-surface-hover px-2 py-0.5 rounded-md">
      {isGH ? <Star className="h-3 w-3 fill-amber-400 text-amber-400" /> : <ArrowUp className="h-3 w-3 text-[#ff6600]" />}
      {score.toLocaleString()}
      {isGH && <span className="text-text-dim font-normal">/d</span>}
    </span>
  );
}

export function FeedCard({ item, rank }: { item: FeedItem; rank?: number }) {
  const { t, locale } = useTranslation();
  let domain = "";
  try { domain = new URL(item.url).hostname.replace("www.", ""); } catch {}

  const summary = locale === "en" ? item.summary_en : item.summary_zh;

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
          {/* Meta row */}
          <div className="flex items-center gap-2 mb-2 flex-wrap">
            <SourceBadge source={item.source} />
            <ScorePill score={item.score} source={item.source} />
            {item.comments > 0 && (
              <span className="inline-flex items-center gap-1 text-[11px] text-text-dim">
                <MessageSquare className="h-3 w-3" />
                {item.comments.toLocaleString()}
              </span>
            )}
          </div>

          {/* Title */}
          <h3 className="font-semibold text-[15px] text-text-primary leading-snug group-hover:text-accent-violet transition-colors">
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

          {/* Summary — the key new feature */}
          {summary ? (
            <p className="text-sm text-text-secondary mt-1.5 leading-relaxed">
              {summary}
            </p>
          ) : item.description ? (
            <p className="text-sm text-text-muted mt-1.5 line-clamp-2 leading-relaxed">
              {item.description}
            </p>
          ) : null}

          {/* Footer */}
          <div className="flex items-center gap-3 mt-2.5 text-xs text-text-dim">
            {domain && (
              <span className="px-2 py-0.5 rounded-md bg-surface-hover text-text-muted font-medium text-[11px]">
                {domain}
              </span>
            )}
            {item.author && (
              <span className="flex items-center gap-1">
                <span className="text-text-dim">{t("common.by")}</span>
                <span className="text-text-muted font-medium">{item.author}</span>
              </span>
            )}
          </div>
        </div>
      </div>
    </article>
  );
}

export function FeedList({ items, showRank = true }: { items: FeedItem[]; showRank?: boolean }) {
  return (
    <div className="space-y-2.5">
      {items.map((item, i) => (
        <FeedCard key={item.id} item={item} rank={showRank ? i + 1 : undefined} />
      ))}
    </div>
  );
}
