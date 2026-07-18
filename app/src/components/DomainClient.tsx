"use client";

import Link from "next/link";
import { ArrowLeft, Calendar, ExternalLink, Globe } from "lucide-react";
import { useTranslation } from "../lib/i18n";
import { getSourceMeta } from "../lib/sources";

export type DomainItem = {
  id: string;
  title: string;
  url: string;
  description: string;
  source: string;
  date: string;
  hasDetail: boolean;
};

export function DomainClient({ domain, items }: { domain: string; items: DomainItem[] }) {
  const { t } = useTranslation();

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center gap-3 text-sm text-text-muted">
        <Link
          href="/"
          className="inline-flex items-center gap-1.5 hover:text-text-primary transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          {t("search.backToToday")}
        </Link>
      </div>

      <section className="text-center py-4">
        <div className="inline-flex items-center gap-2 mb-4">
          <span className="inline-flex items-center gap-1.5 px-4 py-1.5 rounded-full bg-accent-emerald/10 text-accent-emerald text-xs font-semibold border border-accent-emerald/20">
            <Globe className="h-3.5 w-3.5" />
            {t("domain.badge")}
          </span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-text-primary break-all">
          {domain}
        </h1>
        <p className="mt-2 text-text-secondary">{t("domain.subtitle", { count: items.length })}</p>
      </section>

      <div className="space-y-3">
        {items.map((item) => {
          const meta = getSourceMeta(item.source);
          const titleLink = item.hasDetail ? `/item/${item.id}/` : item.url;
          return (
            <article
              key={item.id}
              className="group p-4 rounded-xl bg-surface-card border border-surface-border hover:border-accent-violet/30 hover:shadow-sm transition-all"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <h3 className="font-semibold text-text-primary group-hover:text-accent-violet transition-colors break-words">
                    {item.hasDetail ? (
                      <Link href={titleLink} className="hover:underline underline-offset-2">
                        {item.title}
                      </Link>
                    ) : (
                      <a
                        href={titleLink}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="hover:underline underline-offset-2"
                      >
                        {item.title}
                      </a>
                    )}
                  </h3>
                  <p className="mt-1 text-sm text-text-secondary line-clamp-2">{item.description}</p>
                  <div className="mt-2 flex items-center gap-2 flex-wrap text-xs text-text-dim">
                    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md border ${meta.bg} ${meta.color} border-current/10`}>
                      {meta.icon}
                      {meta.shortLabel}
                    </span>
                    <span className="inline-flex items-center gap-1">
                      <Calendar className="h-3 w-3" />
                      {item.date}
                    </span>
                  </div>
                </div>
                <a
                  href={item.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-text-dim hover:text-text-primary p-2 shrink-0"
                  title={t("search.openOriginal")}
                >
                  <ExternalLink className="h-4 w-4" />
                </a>
              </div>
            </article>
          );
        })}
      </div>

      {items.length === 0 && (
        <div className="text-center py-16 text-text-muted">
          <p className="text-lg">{t("domain.emptyTitle")}</p>
          <p className="text-sm mt-1">{t("domain.emptyHint")}</p>
        </div>
      )}
    </div>
  );
}
