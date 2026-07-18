import type { Metadata } from "next";
import { PeriodClient } from "../../components/PeriodClient";
import { buildMetadata } from "../../lib/metadata";
import { buildPeriodItems } from "../../lib/period";

export const metadata: Metadata = buildMetadata({
  title: "本周热门 | DevFocus",
  description: "DevFocus 本周热门技术资讯精选：AI、GitHub、开源项目、开发者讨论一周聚合。",
  path: "/weekly/",
});

export default function WeeklyPage() {
  const items = buildPeriodItems(7, 30);
  return <PeriodClient period="weekly" items={items} />;
}
