import { http } from '@/lib/http'
import type { CompareResult, CompareHistoryEntry } from '@/types/compare'

export async function searchCompare(keyword: string, force = false, limit = 20): Promise<CompareResult> {
  const params = new URLSearchParams({ keyword, force: String(force), limit: String(limit) })
  return await http(`/api/compare/search?${params}`)
}

export async function getCachedCompare(keyword: string): Promise<CompareResult> {
  return await http(`/api/compare/cached/${encodeURIComponent(keyword)}`)
}

export async function triggerCompare(keyword: string): Promise<{ message: string; keyword: string }> {
  const params = new URLSearchParams({ keyword })
  return await http(`/api/compare/trigger?${params}`, { method: 'POST' })
}

export async function batchCompare(keywords: string[], limit = 20): Promise<{ compared: number; results: Array<{ keyword: string; result_count: number; error: string | null }> }> {
  const params = new URLSearchParams({ limit: String(limit) })
  return await http(`/api/compare/auto-compare?${params}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(keywords),
  })
}

export async function getCompareHistory(): Promise<{ entries: CompareHistoryEntry[] }> {
  return await http('/api/compare/history')
}

export async function deleteCompareCache(keyword: string): Promise<{ message: string }> {
  return await http(`/api/compare/cache/${encodeURIComponent(keyword)}`, { method: 'DELETE' })
}