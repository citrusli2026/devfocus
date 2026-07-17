import { Suspense } from "react";
import { ArrowLeft, Search } from "lucide-react";
import Link from "next/link";
import feedData from "../../data/feed.json";
import { SearchClient, SearchIndexItem } from "../../components/SearchClient";

type FeedData = {
  generated_at: string;
  items: {
    id: string;
    title: string;
    url: string;
    description: string;
    source: string;
    score: number;
    comments: number;
    time: string;
    tags: string[];
  }[];
  by_date: Record<string, unknown>;
};

const feed = feedData as unknown as FeedData;

function extractDate(time: string): string {
  try {
    return new Date(time).toISOString().slice(0, 10);
  } catch {
    return "";
  }
}

export default function SearchPage() {
  const items: SearchIndexItem[] = feed.items.map((item) => ({
    id: item.id,
    title: item.title,
    url: item.url,
    description: item.description,
    source: item.source,
    score: item.score,
    comments: item.comments,
    date: extractDate(item.time),
    tags: item.tags ?? [],
  }));

  const sources = Array.from(new Set(items.map((i) => i.source))).sort();
  const dates = Object.keys(feed.by_date).sort().reverse();
  const tags = Array.from(new Set(items.flatMap((i) => i.tags))).filter(Boolean).sort();

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center gap-3 text-sm text-text-muted">
        <Link
          href="/"
          className="inline-flex items-center gap-1.5 hover:text-text-primary transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          返回今日
        </Link>
      </div>

      <section className="text-center py-4">
        <div className="inline-flex items-center gap-2 mb-4">
          <span className="inline-flex items-center gap-1.5 px-4 py-1.5 rounded-full bg-accent-violet/10 text-accent-violet text-xs font-semibold border border-accent-violet/20">
            <Search className="h-3.5 w-3.5" />
            全站搜索
          </span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-text-primary">
          搜索内容
        </h1>
        <p className="mt-2 text-text-secondary">
          在 {items.length.toLocaleString()} 条历史内容中查找
        </p>
      </section>

      <Suspense fallback={<div className="py-12 text-center text-text-muted">加载搜索...</div>}>
        <SearchClient items={items} sources={sources} dates={dates} tags={tags} />
      </Suspense>
    </div>
  );
}
