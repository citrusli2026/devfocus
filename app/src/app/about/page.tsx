"use client";

import { useTranslation } from "@/lib/i18n";
import { Globe, Flame, Cpu, Code2, Zap, BarChart3 } from "lucide-react";
import { GitHubIcon } from "@/components/icons";
import digestData from "@/data/digest.json";
import type { Digest } from "@/types";

export default function About() {
  const { t } = useTranslation();
  const digest = digestData as unknown as Digest;

  return (
    <div className="max-w-2xl mx-auto py-6 space-y-12">
      <section
        className="text-center py-10 -mx-4 sm:-mx-6 px-4"
        style={{
          background: "radial-gradient(ellipse at 50% 0%, rgba(106,95,193,0.10) 0%, transparent 60%)",
        }}
      >
        <div className="inline-flex items-center justify-center h-14 w-14 rounded-2xl bg-gradient-to-br from-accent-violet to-accent-coral shadow-lg shadow-accent-violet/20 mb-5">
          <Zap className="h-7 w-7 text-white" />
        </div>
        <h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-text-primary mb-4">
          {t("about.title")}
        </h1>
        <p className="text-text-secondary leading-relaxed max-w-lg mx-auto">
          {t("about.desc")}
        </p>

        <div className="mt-8 flex justify-center gap-4 flex-wrap">
          <div className="px-5 py-3 rounded-xl bg-surface-card border border-surface-border shadow-sm">
            <div className="text-2xl font-bold text-accent-violet tabular-nums">{digest.daily.count}</div>
            <div className="text-xs text-text-dim mt-0.5">{t("about.statDaily")}</div>
          </div>
          <div className="px-5 py-3 rounded-xl bg-surface-card border border-surface-border shadow-sm">
            <div className="text-2xl font-bold text-accent-emerald tabular-nums">{digest.sources.length}</div>
            <div className="text-xs text-text-dim mt-0.5">{t("about.statSources")}</div>
          </div>
          <div className="px-5 py-3 rounded-xl bg-surface-card border border-surface-border shadow-sm">
            <div className="text-2xl font-bold text-accent-amber tabular-nums">2</div>
            <div className="text-xs text-text-dim mt-0.5">{t("about.statLangs")}</div>
          </div>
        </div>
      </section>

      <Section icon={<Globe className="h-5 w-5" />} title={t("about.sources")} color="text-accent-violet" bg="bg-accent-violet/10">
        <div className="space-y-3">
          <SourceCard icon={<Flame className="h-5 w-5 text-[#ff6600]" />} label="Hacker News" desc={t("about.hnDesc")} bg="bg-[#ff6600]/8" />
          <SourceCard icon={<GitHubIcon className="h-5 w-5 text-accent-emerald" />} label="GitHub Trending" desc={t("about.ghDesc")} bg="bg-accent-emerald/8" />
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
