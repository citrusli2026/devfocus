"use client";

import { useTranslation } from "@/lib/i18n";
import { Globe, Flame, Cpu, Code2, Zap, Calendar, BarChart3, Layers, MessageSquare, FileText } from "lucide-react";
import { GitHubIcon } from "@/components/icons";
import digestData from "@/data/digest.json";
import statsData from "@/data/stats.json";
import type { Digest } from "@/types";

const stats = statsData as {
  generated_at: string;
  total_items: number;
  unique_items: number;
  days_covered: number;
  first_date: string;
  last_date: string;
  sources: string[];
  source_counts: Record<string, number>;
  daily_count: number;
  items_with_summary: number;
  total_summaries: number;
  items_with_comments: number;
  total_comments: number;
  top_domains: Record<string, number>;
  latest_update: string;
};

export default function About() {
  const { t, locale } = useTranslation();
  const digest = digestData as unknown as Digest;

  const maxSourceCount = Math.max(...Object.values(stats.source_counts), 1);

  const formatNumber = (n: number) => n.toLocaleString(locale === "zh" ? "zh-CN" : "en-US");

  return (
    <div className="max-w-2xl mx-auto py-6 space-y-12">
      <section className="text-center py-10 -mx-4 sm:-mx-6 px-4 hero-glow">
        <div className="inline-flex items-center justify-center h-14 w-14 rounded-2xl bg-gradient-to-br from-accent-violet to-accent-coral shadow-lg shadow-accent-violet/20 mb-5">
          <Zap className="h-7 w-7 text-white" />
        </div>
        <h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-text-primary mb-4">
          {t("about.title")}
        </h1>
        <p className="text-text-secondary leading-relaxed max-w-lg mx-auto">
          {t("about.desc")}
        </p>

        <div className="mt-8 grid grid-cols-2 sm:grid-cols-3 gap-3">
          <StatCard value={digest.daily.count} label={t("about.statDaily")} color="text-accent-violet" icon={<Layers className="h-4 w-4" />} />
          <StatCard value={stats.sources.length} label={t("about.statSources")} color="text-accent-emerald" icon={<Globe className="h-4 w-4" />} />
          <StatCard value={2} label={t("about.statLangs")} color="text-accent-amber" icon={<Code2 className="h-4 w-4" />} />
          <StatCard value={stats.total_items} label={t("about.statTotal")} color="text-accent-coral" icon={<BarChart3 className="h-4 w-4" />} />
          <StatCard value={stats.days_covered} label={t("about.statDays")} color="text-accent-blue" icon={<Calendar className="h-4 w-4" />} />
          <StatCard value={stats.total_summaries} label={t("about.statSummaries")} color="text-accent-cyan" icon={<FileText className="h-4 w-4" />} />
        </div>

        {/* Last updated */}
        <div className="mt-4 inline-flex items-center gap-1.5 text-xs text-text-dim">
          <Calendar className="h-3.5 w-3.5" />
          <span>{t("about.lastUpdated")}: {new Date(stats.latest_update || digest.generated_at).toLocaleString("zh-CN", { timeZone: "Asia/Shanghai", year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" })}</span>
        </div>
      </section>

      <Section icon={<BarChart3 className="h-5 w-5" />} title={t("about.dataCoverage")} color="text-accent-violet" bg="bg-accent-violet/10">
        <div className="space-y-6">
          {/* Source distribution */}
          <div>
            <h3 className="text-sm font-semibold text-text-secondary mb-3">{t("about.sourceDistribution")}</h3>
            <div className="space-y-2.5">
              {stats.sources.map((src) => {
                const count = stats.source_counts[src] ?? 0;
                const pct = (count / maxSourceCount) * 100;
                return (
                  <div key={src} className="space-y-1">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-medium text-text-primary capitalize">{src.replace("_", " ")}</span>
                      <span className="text-text-dim tabular-nums">{formatNumber(count)} {t("about.items")}</span>
                    </div>
                    <div className="h-2 w-full rounded-full bg-surface-hover overflow-hidden">
                      <div
                        className="h-full rounded-full bg-accent-violet/70"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Top domains */}
          <div>
            <h3 className="text-sm font-semibold text-text-secondary mb-3">{t("about.topDomains")}</h3>
            <div className="flex flex-wrap gap-2">
              {Object.entries(stats.top_domains).map(([domain, count]) => (
                <span
                  key={domain}
                  className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-surface-hover text-text-secondary text-xs font-medium border border-surface-border"
                >
                  <span className="text-text-dim">{domain}</span>
                  <span className="text-accent-violet tabular-nums">{formatNumber(count)}</span>
                </span>
              ))}
            </div>
          </div>

          {/* Comments stat */}
          <div className="flex items-center gap-3 p-3 rounded-xl bg-surface-hover border border-surface-border">
            <MessageSquare className="h-5 w-5 text-accent-coral" />
            <div>
              <div className="text-sm font-semibold text-text-primary">
                {formatNumber(stats.total_comments)}
              </div>
              <div className="text-xs text-text-muted">
                {formatNumber(stats.items_with_comments)} {t("about.items")} · {t("about.statComments")}
              </div>
            </div>
          </div>
        </div>
      </Section>

      <Section icon={<Globe className="h-5 w-5" />} title={t("about.sources")} color="text-accent-violet" bg="bg-accent-violet/10">
        <div className="space-y-3">
          <SourceCard icon={<Flame className="h-5 w-5 text-[#ff6600]" />} label="Hacker News" desc={t("about.hnDesc")} bg="bg-[#ff6600]/8" />
          <SourceCard icon={<GitHubIcon className="h-5 w-5 text-accent-emerald" />} label="GitHub Trending" desc={t("about.ghDesc")} bg="bg-accent-emerald/8" />
          <SourceCard icon={<span className="text-lg">🚀</span>} label="Product Hunt" desc={t("about.phDesc")} bg="bg-[#da552f]/8" />
          <SourceCard icon={<span className="text-lg">📘</span>} label="掘金" desc={t("about.juejinDesc")} bg="bg-[#1e80ff]/8" />
          <SourceCard icon={<span className="text-lg">💬</span>} label="知乎" desc={t("about.zhihuDesc")} bg="bg-[#0066ff]/8" />
        </div>
      </Section>

      <Section icon={<Cpu className="h-5 w-5" />} title={t("about.techStack")} color="text-accent-amber" bg="bg-accent-amber/10">
        <div className="flex flex-wrap gap-2">
          {["Python", "Next.js", "Tailwind CSS", "TypeScript", "Static Export"].map((tech) => (
            <span key={tech} className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-hover text-text-secondary text-sm font-medium border border-surface-border">
              <Code2 className="h-3.5 w-3.5 text-text-dim" />
              {tech}
            </span>
          ))}
        </div>
      </Section>
    </div>
  );
}

function StatCard({ value, label, color, icon }: { value: number; label: string; color: string; icon: React.ReactNode }) {
  const { locale } = useTranslation();
  return (
    <div className="px-4 py-3 rounded-xl bg-surface-card border border-surface-border shadow-sm">
      <div className={`text-2xl font-bold tabular-nums ${color}`}>
        {value.toLocaleString(locale === "zh" ? "zh-CN" : "en-US")}
      </div>
      <div className="text-xs text-text-dim mt-0.5 flex items-center gap-1">
        {icon}
        {label}
      </div>
    </div>
  );
}

function Section({ icon, title, color, bg, children }: {
  icon: React.ReactNode; title: string; color: string; bg: string; children: React.ReactNode;
}) {
  return (
    <section>
      <div className="flex items-center gap-3 mb-4">
        <div className={`flex items-center justify-center h-9 w-9 rounded-xl ${bg}`}>
          <span className={color}>{icon}</span>
        </div>
        <h2 className="text-lg font-bold text-text-primary">{title}</h2>
      </div>
      {children}
    </section>
  );
}

function SourceCard({ icon, label, desc, bg }: {
  icon: React.ReactNode; label: string; desc: string; bg: string;
}) {
  return (
    <div className="flex items-start gap-4 p-4 rounded-xl bg-surface-card border border-surface-border hover:border-accent-violet/20 hover:shadow-sm transition-all">
      <div className={`flex items-center justify-center h-10 w-10 rounded-xl ${bg} shrink-0`}>
        {icon}
      </div>
      <div>
        <div className="font-semibold text-text-primary">{label}</div>
        <div className="text-sm text-text-muted mt-0.5">{desc}</div>
      </div>
    </div>
  );
}
