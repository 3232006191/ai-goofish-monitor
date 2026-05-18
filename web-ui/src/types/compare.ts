// 拍机堂比价相关类型定义

export interface PaijitangCompareItem {
  title: string;
  price: number;
  price_display: string;
  condition: string;
  link: string;
  images: string[];
  source: string;
  search_keyword: string;
  search_time: string;
}

export interface CompareResult {
  keyword: string;
  results: PaijitangCompareItem[];
  cached: boolean;
  result_count: number;
  search_time: string;
  error?: string;
}

export interface CompareHistoryEntry {
  keyword: string;
  result_count: number;
  updated_at: string;
  file: string;
}

export interface CompareSummary {
  avg_price: number | null;
  min_price: number | null;
  max_price: number | null;
  median_price: number | null;
  sample_count: number;
}

// 从比价结果计算汇总统计
export function summarizeCompareResults(items: PaijitangCompareItem[]): CompareSummary {
  const prices = items.map(i => i.price).filter(p => p > 0);
  if (prices.length === 0) {
    return { avg_price: null, min_price: null, max_price: null, median_price: null, sample_count: 0 };
  }
  const sorted = [...prices].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  const median = sorted.length % 2 === 0
    ? (sorted[mid - 1]! + sorted[mid]!) / 2
    : sorted[mid]!;
  return {
    avg_price: Math.round((prices.reduce((a, b) => a + b, 0) / prices.length) * 100) / 100,
    min_price: sorted[0]!,
    max_price: sorted[sorted.length - 1]!,
    median_price: Math.round(median * 100) / 100,
    sample_count: prices.length,
  };
}