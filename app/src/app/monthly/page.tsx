"use client";

import { PeriodClient } from "../../components/PeriodClient";
import { buildPeriodItems } from "../../lib/period";
import { useTranslation } from "../../lib/i18n";

export default function MonthlyPage() {
  const { t } = useTranslation();
  const items = buildPeriodItems(30, 50);
  return (
    <PeriodClient
      title={t("period.monthlyTitle")}
      subtitle={t("period.monthlySubtitle")}
      items={items}
    />
  );
}
