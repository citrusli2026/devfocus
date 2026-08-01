export interface FeedItem {
  id: string;
  title: string;
  url: string;
  description: string;
  source: string;
  score: number;
  comments: number;
  author: string;
  time: string;
  tags: string[];
  summary_zh?: string;
  summary_en?: string;
  first_seen?: string;
  domain?: string;
  quality_score?: number;
  related_ids?: string[];
}

export interface DigestSection {
  date?: string;
  start?: string;
  end?: string;
  items: FeedItem[];
  count: number;
}

export interface Digest {
  generated_at: string;
  daily: DigestSection;
  monthly: DigestSection;
  sources: string[];
  total_items: number;
}

export interface TrendTopic {
  keyword: string;
  count: number;
  trend: "rising" | "falling" | "stable" | "new";
  heat_by_date: Record<string, number>;
  sample_titles: string[];
  sources: string[];
}

export interface TrendsData {
  generated_at: string;
  period: string;
  dates: string[];
  topics: TrendTopic[];
  source_activity: Record<string, Record<string, number>>;
}

export interface HeatPoint {
  date: string;
  score: number;
}
