import { notFound } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, ExternalLink, MessageSquare, Star, ArrowUp, Calendar } from "lucide-react";
import { getSourceMeta } from "../../../lib/sources";
import digestData from "../../../data/digest.json";
import type { Digest, FeedItem } from "../../../types";

const digest = digestData as Digest;
const itemMap = new Map(digest.daily.items.map((i) => [i.id, i]));

export async function generateStaticParams() {
  return digest.daily.items.map((item) => ({ id: item.id }));
}

export default async function ItemPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const item: FeedItem | undefined = itemMap.get(id);
  if (!item) return notFound();

  const meta = getSourceMeta(item.source);
  const summary = item.summary_zh || item.summary_en || item.description;
  let domain = "";
  try {
    domain = new URL(item.url).hostname.replace("www.", "");
  } catch {}

  return (
    <article className="max-w-3xl mx-auto space-y-8">
      <div className="flex items-center gap-3 text-sm text-text-muted">
        <Link
          href="/"
          className="inline-flex items-center gap-1.5 hover:text-text-primary transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          返回今日
        </Link>
      </div>

      <header className="space-y-5">
        <div className="flex items-center gap-2 flex-wrap">
          <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold border ${meta.bg} ${meta.color} border-current/15`}>
            {meta.icon}
            {meta.shortLabel}
          </span>
          {item.score > 0 && (
            <span className="inline-flex items-center gap-1 text-xs font-semibold text-text-muted tabular-nums bg-surface-hover px-2 py-1 rounded-md">
              {item.source === "github_trending" ? (
                <Star className="h-3 w-3 fill-amber-400 text-amber-400" />
              ) : (
                <ArrowUp className="h-3 w-3 text-[#ff6600]" />
              )}
              {item.score.toLocaleString()}
            </span>
          )}
          {item.comments > 0 && (
            <span className="inline-flex items-center gap-1 text-xs text-text-dim bg-surface-hover px-2 py-1 rounded-md">
              <MessageSquare className="h-3 w-3" />
              {item.comments.toLocaleString()}
            </span>
          )}
          {domain && (
            <span className="text-xs text-text-dim bg-surface-hover px-2 py-1 rounded-md">
              {domain}
            </span>
          )}
        </div>

        <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold text-text-primary leading-tight">
          {item.title}
        </h1>

        <div className="flex items-center gap-4 text-sm text-text-dim flex-wrap">
          {item.author && <span>by {item.author}</span>}
          {item.first_seen && (
            <span className="inline-flex items-center gap-1">
              <Calendar className="h-3.5 w-3.5" />
              首次上榜 {item.first_seen}
            </span>
          )}
        </div>
      </header>

      {summary && (
        <div className="bg-surface-card border border-surface-border rounded-xl p-5 sm:p-6">
          <h2 className="text-sm font-semibold text-text-muted mb-3 uppercase tracking-wide">摘要</h2>
          <p className="text-base text-text-secondary leading-relaxed whitespace-pre-line">{summary}</p>
        </div>
      )}

      <div className="flex flex-col sm:flex-row gap-3">
        <a
          href={item.url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center justify-center gap-2 px-5 py-3 rounded-xl bg-accent-violet text-white font-semibold hover:bg-accent-violet/90 transition-colors"
        >
          <ExternalLink className="h-4 w-4" />
          阅读原文
        </a>
        {item.first_seen && (
          <Link
            href={`/history/${item.first_seen}/`}
            className="inline-flex items-center justify-center gap-2 px-5 py-3 rounded-xl bg-surface-hover text-text-secondary font-semibold hover:bg-surface-elevated transition-colors"
          >
            <Calendar className="h-4 w-4" />
            查看 {item.first_seen} 归档
          </Link>
        )}
      </div>
    </article>
  );
}
