import Link from "next/link";
import { promises as fs } from "fs";
import path from "path";
import { Calendar, ArrowLeft } from "lucide-react";

const HISTORY_DIR = path.resolve(process.cwd(), "..", "data", "5-history");

export default async function HistoryIndexPage() {
  const files = await fs.readdir(HISTORY_DIR).catch(() => []);
  const dates = files
    .filter((f) => f.endsWith(".json"))
    .map((f) => f.replace(".json", ""))
    .sort()
    .reverse();

  return (
    <div className="space-y-8 max-w-3xl mx-auto">
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
            <Calendar className="h-3.5 w-3.5" />
            历史归档
          </span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-text-primary">
          往期精选
        </h1>
        <p className="mt-2 text-text-secondary">共 {dates.length} 天归档</p>
      </section>

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
        {dates.map((date) => (
          <Link
            key={date}
            href={`/history/${date}/`}
            className="flex flex-col items-center justify-center gap-1 p-4 rounded-xl bg-surface-card border border-surface-border hover:border-accent-violet/30 hover:shadow-sm transition-all"
          >
            <span className="text-sm font-semibold text-text-primary">{date}</span>
            <span className="text-xs text-text-dim">查看当日</span>
          </Link>
        ))}
      </div>
    </div>
  );
}
