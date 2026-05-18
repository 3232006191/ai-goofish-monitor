import { ref, onMounted } from 'vue'
import type { CompareHistoryEntry, PaijitangCompareItem } from '@/types/compare'
import * as compareApi from '@/api/priceCompare'

export function usePriceCompare() {
  const history = ref<CompareHistoryEntry[]>([])
  const results = ref<PaijitangCompareItem[]>([])
  const selectedKeyword = ref<string>('')
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const isCached = ref(false)
  const resultCount = ref(0)

  async function fetchHistory() {
    try {
      const data = await compareApi.getCompareHistory()
      history.value = data.entries || []
    } catch (e) {
      history.value = []
    }
  }

  async function searchComparison(keyword: string, force = false) {
    if (!keyword.trim()) return
    isLoading.value = true
    error.value = null
    selectedKeyword.value = keyword
    try {
      const data = await compareApi.searchCompare(keyword, force)
      results.value = data.results || []
      isCached.value = data.cached
      resultCount.value = data.result_count
      await fetchHistory()
    } catch (e) {
      error.value = (e as Error).message || '比价查询失败'
      results.value = []
    } finally {
      isLoading.value = false
    }
  }

  async function triggerComparison(keyword: string) {
    try {
      await compareApi.triggerCompare(keyword)
      await fetchHistory()
    } catch (e) {
      error.value = (e as Error).message || '触发比价失败'
    }
  }

  async function loadCached(keyword: string) {
    isLoading.value = true
    error.value = null
    selectedKeyword.value = keyword
    try {
      const data = await compareApi.getCachedCompare(keyword)
      results.value = data.results || []
      isCached.value = true
      resultCount.value = data.result_count
    } catch (e) {
      error.value = (e as Error).message || '加载缓存失败'
      results.value = []
    } finally {
      isLoading.value = false
    }
  }

  async function deleteCache(keyword: string) {
    try {
      await compareApi.deleteCompareCache(keyword)
      if (selectedKeyword.value === keyword) {
        results.value = []
        resultCount.value = 0
      }
      await fetchHistory()
    } catch (e) {
      error.value = (e as Error).message || '删除缓存失败'
    }
  }

  onMounted(() => {
    fetchHistory()
  })

  return {
    history,
    results,
    selectedKeyword,
    isLoading,
    error,
    isCached,
    resultCount,
    searchComparison,
    triggerComparison,
    loadCached,
    deleteCache,
    fetchHistory,
  }
}