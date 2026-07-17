"use client";

import { PeriodClient } from "../../components/PeriodClient";
import { buildPeriodItems } from "../../lib/period";
import { useTranslation } from "../../lib/i18n";

export default function WeeklyPage() {
  const { t } = useTranslation();
  const items = buildPeriodItems(7, 30);
  return (
    <PeriodClient
      title={t("period.weeklyTitle")}
      subtitle={t("period.weeklySubtitle")}
      items={items}
    />
  );
}
