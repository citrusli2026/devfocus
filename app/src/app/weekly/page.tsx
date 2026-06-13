import { Digest } from "@/types";
import { FeedList } from "@/components/FeedCard";
import digestData from "@/data/digest.json";

export default function Weekly() {
  const digest = digestData as Digest;

  return (
    <div className="space-y-8">
      <section className="text-center py-6">
        <h1 className="text-3xl font-bold mb-2">📊 DevPulse 周报</h1>
        <p className="text-gray-400">
          {digest.weekly.start} ~ {digest.weekly.end} · 共 {digest.weekly.count} 条
        </p>
      </section>

      <section>
        <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
          <span className="text-purple-400">📈</span> 本周热门
        </h2>
        <FeedList items={digest.weekly.items} />
      </section>
    </div>
  );
}
