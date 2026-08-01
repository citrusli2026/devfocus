import validTagsData from "@/data/valid-tags.json";

// 有效标签/域名清单：只给有独立聚合页（达到条目数阈值）的标签/域名渲染链接，
// 避免长尾标签点击 404。清单由 data/3-process/build_stats.py 生成，
// 阈值与归一化规则见 app/tag/[tag]/page.tsx 和 app/domain/[domain]/page.tsx。
const tagSet = new Set<string>(validTagsData.tags);
const domainSet = new Set<string>(validTagsData.domains);

// Keep in sync with normalizeTag in src/app/tag/[tag]/page.tsx
export const normalizeTagSlug = (tag: string) =>
  tag.toLowerCase().replace(/\s+/g, "-");

// Keep in sync with normalizeDomain in src/app/domain/[domain]/page.tsx
export const normalizeDomainSlug = (domain: string) =>
  domain.toLowerCase().replace(/^www\./, "");

export const isValidTag = (tag: string) => tagSet.has(normalizeTagSlug(tag));

export const isValidDomain = (domain: string) =>
  domainSet.has(normalizeDomainSlug(domain));
