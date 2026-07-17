import { notFound } from "next/navigation";
import digestData from "../../../data/digest.json";
import { ItemClient } from "../../../components/ItemClient";
import type { Digest } from "../../../types";

const digest = digestData as Digest;
const itemMap = new Map(digest.daily.items.map((i) => [i.id, i]));

export async function generateStaticParams() {
  return digest.daily.items.map((item) => ({ id: item.id }));
}

export default async function ItemPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const item = itemMap.get(id);
  if (!item) return notFound();

  return <ItemClient item={item} />;
}
