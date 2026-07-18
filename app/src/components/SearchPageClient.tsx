"use client";

import { Suspense } from "react";
import { ArrowLeft, Search } from "lucide-react";
import Link from "next/link";
import { SearchClient } from "@/components/SearchClient";
import { useTranslation } from "@/lib/i18n";

export default function SearchPage() {
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
          <span className="inline-flex items-center gap-1.5 px-4 py-1.5 rounded-full bg-accent-violet/10 text-accent-violet text-xs font-semibold border border-accent-violet/20">
            <Search className="h-3.5 w-3.5" />
            {t("search.badge")}
          </span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-text-primary">
          {t("search.title")}
        </h1>
        <p className="mt-2 text-text-secondary">{t("search.subtitle")}</p>
      </section>

      <Suspense
        fallback={
          <div className="py-12 text-center text-text-muted">{t("search.loading")}</div>
        }
      >
        <SearchClient />
      </Suspense>
    </div>
  );
}
