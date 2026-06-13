import { FeedItem } from "@/types";

function SourceBadge({ source }: { source: string }) {
  const colors: Record<string, string> = {
    hackernews: "bg-orange-500/20 text-orange-400",
    github_trending: "bg-green-500/20 text-green-400",
  };
  const labels: Record<string, string> = {
    hackernews: "HN",
    github_trending: "GitHub",
  };
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full ${colors[source] || "bg-gray-500/20 text-gray-400"}`}>
      {labels[source] || source}
    </span>
  );
}

function ScoreDisplay({ score, source }: { score: number; source: string }) {
  if (score === 0) return null;
  const icon = source === "github_trending" ? "⭐" : "▲";
  const suffix = source === "github_trending" ? "/today" : "";
  return (
    <span className="text-xs text-gray-500">
      {icon} {score.toLocaleString()}{suffix}
    </span>
  );
}

export function FeedCard({ item, rank }: { item: FeedItem; rank?: number }) {
  const domain = item.url ? new URL(item.url).hostname.replace("www.", "") : "";

  return (
    <article className="group border border-gray-800 rounded-lg p-4 hover:border-gray-600 transition-colors bg-gray-900/50">
      <div className="flex items-start gap-3">
        {rank !== undefined && (
          <span className="text-2xl font-black text-gray-700 min-w-[2rem] text-right tabular-nums">
            {rank}
          </span>
        )}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <SourceBadge source={item.source} />
            <ScoreDisplay score={item.score} source={item.source} />
            {item.comments > 0 && (
              <span className="text-xs text-gray-500">💬 {item.comments}</span>
            )}
          </div>
          <h3 className="font-semibold text-gray-100 group-hover:text-blue-400 transition-colors leading-snug">
            <a href={item.url} target="_blank" rel="noopener noreferrer">
              {item.title}
            </a>
          </h3>
          {item.description && (
            <p className="text-sm text-gray-400 mt-1 line-clamp-2">{item.description}</p>
          )}
          <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
            {domain && <span>{domain}</span>}
            {item.author && <span>by {item.author}</span>}
          </div>
        </div>
      </div>
    </article>
  );
}

export function FeedList({ items, showRank = true }: { items: FeedItem[]; showRank?: boolean }) {
  return (
    <div className="space-y-3">
      {items.map((item, i) => (
        <FeedCard key={item.id} item={item} rank={showRank ? i + 1 : undefined} />
      ))}
    </div>
  );
}
