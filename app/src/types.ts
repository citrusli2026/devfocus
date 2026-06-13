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
  weekly: DigestSection;
  sources: string[];
  total_items: number;
}

export interface Feed {
  generated_at: string;
  items: FeedItem[];
  by_date: Record<string, FeedItem[]>;
}
