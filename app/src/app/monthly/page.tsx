import { PeriodClient } from "../../components/PeriodClient";
import { buildPeriodItems } from "../../lib/period";

export default function MonthlyPage() {
  const items = buildPeriodItems(30, 50);
  return <PeriodClient period="monthly" items={items} />;
}
