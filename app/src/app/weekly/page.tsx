import { PeriodClient } from "../../components/PeriodClient";
import { buildPeriodItems } from "../../lib/period";

export default function WeeklyPage() {
  const items = buildPeriodItems(7, 30);
  return <PeriodClient period="weekly" items={items} />;
}
