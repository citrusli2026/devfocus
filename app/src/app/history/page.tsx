import { promises as fs } from "fs";
import path from "path";
import { HistoryIndexClient } from "../../components/HistoryIndexClient";

const HISTORY_DIR = path.resolve(process.cwd(), "..", "data", "5-history");

export default async function HistoryIndexPage() {
  const files = await fs.readdir(HISTORY_DIR).catch(() => []);
  const dates = files
    .filter((f) => f.endsWith(".json"))
    .map((f) => f.replace(".json", ""))
    .sort()
    .reverse();

  return <HistoryIndexClient dates={dates} />;
}
