"use client";

import { Digest } from "../types";
import { FeedList } from "../components/FeedCard";
import { useTranslation } from "../lib/i18n";
import { TrendingUp, Flame, Newspaper, ArrowRight, Calendar } from "lucide-react";
import { GitHubIcon } from "../components/icons";
import digestData from "../data/digest.json";

export default function Home() {
  const { t } = useTranslation();
  const digest = digestData as Digest;
  const hnItems = digest.daily.items.filter((i) => i.source === "hackernews");
  const ghItems = digest.daily.items.filter((i) => i.source === "github_trending");
  const rdItems = digest.daily.items.filter((i) => i.source === "reddit");

  const sourceParts: string[] = [];
  if (hnItems.length > 0) sourceParts.push(`HN ${hnItems.length}`);
  if (ghItems.length > 0) sourceParts.push(`GitHub ${ghItems.length}`);
  if (rdItems.length > 0) sourceParts.push(`Reddit ${rdItems.length}`);

  return (
    <div className="space-y-10">
      {/* Hero */}
      <section className="text-center py-4 sm:py-8">
        <div className="inline-flex items-center gap-2 mb-5">
          <span className="inline-flex items-center gap-1.5 px-4 py-1.5 rounded-full bg-accent-lime/10 text-accent-lime text-xs font-semibold border border-accent-lime/20">
            <TrendingUp className="h-3.5 w-3.5" />
            {t("today.updatedAt")}
          </span>
        </div>

        <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight text-text-primary">
          ⚡ {t("today.title")}
        </h1>

        <p className="mt-4 text-sm sm:text-base md:text-lg text-text-secondary max-w-2xl mx-auto leading-relaxed">
          {digest.daily.date} · {sourceParts.join(" + ")} {t("today.items")}
        </p>
      </section>

      {/* Source sections */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-10">
        {hnItems.length > 0 && (
          <section>
            <SectionHeader
              icon={<Flame className="h-5 w-5" />}
              title={t("today.hnTitle")}
              count={hnItems.length}
              color="text-[#ff6600]"
              bg="bg-[#ff6600]/10"
            />
            <FeedList items={hnItems} />
          </section>
        )}

        {ghItems.length > 0 && (
          <section>
            <SectionHeader
              icon={<GitHubIcon className="h-5 w-5" />}
              title={t("today.ghTitle")}
              count={ghItems.length}
              color="text-accent-emerald"
              bg="bg-accent-emerald/10"
            />
            <FeedList items={ghItems} />
          </section>
        )}
      </div>

      {/* Reddit section — full width if present */}
      {rdItems.length > 0 && (
        <section>
          <SectionHeader
            icon={<Newspaper className="h-5 w-5" />}
            title={t("today.rdTitle")}
            count={rdItems.length}
            color="text-[#ff4500]"
            bg="bg-[#ff4500]/10"
          />
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <FeedList items={rdItems.slice(0, Math.ceil(rdItems.length / 2))} />
            <FeedList items={rdItems.slice(Math.ceil(rdItems.length / 2))} />
          </div>
        </section>
      )}

      {/* Empty state */}
      {hnItems.length === 0 && ghItems.length === 0 && rdItems.length === 0 && (
        <div className="text-center py-12 text-text-muted">
          <p className="text-lg">暂无数据，稍后再来</p>
        </div>
      )}
    </div>
  );
}

function SectionHeader({ icon, title, count, color, bg }: {
  icon: React.ReactNode; title: string; count: number; color: string; bg: string;
}) {
  return (
    <div className="flex items-center gap-3 mb-5">
      <div className={`flex items-center justify-center h-9 w-9 rounded-xl ${bg}`}>
        <span className={color}>{icon}</span>
      </div>
      <h2 className="text-lg sm:text-xl font-bold text-text-primary">{title}</h2>
      <span className="text-xs font-semibold text-text-dim bg-surface-hover px-2.5 py-1 rounded-lg tabular-nums">
        {count}
      </span>
    </div>
  );
}
