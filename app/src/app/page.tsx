import { Digest } from "@/types";
import { FeedList } from "@/components/FeedCard";
import digestData from "@/data/digest.json";

export default function Home() {
  const digest = digestData as Digest;
  const hnItems = digest.daily.items.filter((i) => i.source === "hackernews");
  const ghItems = digest.daily.items.filter((i) => i.source === "github_trending");

  return (
    <div className="space-y-8">
      {/* Hero */}
      <section className="text-center py-6">
        <h1 className="text-3xl font-bold mb-2">
          ⚡ DevPulse 每日速报
        </h1>
        <p className="text-gray-400">
          {digest.daily.date} · 来自 {digest.sources.join(" + ")} · 共 {digest.total_items} 条
        </p>
        <p className="text-xs text-gray-600 mt-1">
          更新于 {new Date(digest.generated_at).toLocaleString("zh-CN")}
        </p>
      </section>

      {/* Two columns: HN + GitHub */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Hacker News */}
        <section>
          <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
            <span className="text-orange-400">🔥</span> Hacker News 热门
            <span className="text-sm font-normal text-gray-500">({hnItems.length})</span>
          </h2>
          <FeedList items={hnItems} />
        </section>

        {/* GitHub Trending */}
        <section>
          <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
            <span className="text-green-400">📦</span> GitHub Trending
            <span className="text-sm font-normal text-gray-500">({ghItems.length})</span>
          </h2>
          <FeedList items={ghItems} />
        </section>
      </div>

      {/* Weekly summary link */}
      <section className="text-center py-8 border-t border-gray-800">
        <a
          href="/weekly/"
          className="inline-flex items-center gap-2 px-6 py-3 rounded-lg bg-blue-600 hover:bg-blue-500 transition-colors font-medium"
        >
          📊 查看周报 →
        </a>
      </section>
    </div>
  );
}
