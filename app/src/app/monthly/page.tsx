import type { Metadata } from "next";
import { PeriodClient } from "../../components/PeriodClient";
import { buildMetadata } from "../../lib/metadata";
import { buildPeriodItems } from "../../lib/period";

export const metadata: Metadata = buildMetadata({
  title: "本月热门 | DevFocus",
  description: "DevFocus 本月热门技术资讯精选：AI、GitHub、开源项目、开发者讨论月度聚合。",
  path: "/monthly/",
});

export default function MonthlyPage() {
  const items = buildPeriodItems(30, 50);
  return <PeriodClient period="monthly" items={items} />;
}
