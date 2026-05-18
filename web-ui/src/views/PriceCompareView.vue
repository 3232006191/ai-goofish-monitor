<script setup lang="ts">
import { ref, computed } from 'vue'
import { usePriceCompare } from '@/composables/usePriceCompare'
import { summarizeCompareResults } from '@/types/compare'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardFooter } from '@/components/ui/card'
import Badge from '@/components/ui/badge/Badge.vue'
import { toast } from '@/components/ui/toast'
import {
  Search,
  RefreshCw,
  ExternalLink,
  TrendingUp,
  TrendingDown,
  DollarSign,
  Trash2,
  Clock,
  Package,
  Loader2,
} from 'lucide-vue-next'

const {
  history,
  results,
  selectedKeyword,
  isLoading,
  error,
  isCached,
  resultCount,
  searchComparison,
  loadCached,
  deleteCache,
} = usePriceCompare()

const searchInput = ref('')
const isRefreshing = ref(false)

const summary = computed(() => summarizeCompareResults(results.value))

const sortedByPrice = computed(() => {
  return [...results.value].sort((a, b) => a.price - b.price)
})

async function handleSearch() {
  const kw = searchInput.value.trim()
  if (!kw) {
    toast({ title: '请输入搜索关键词', variant: 'destructive' })
    return
  }
  await searchComparison(kw)
}

async function handleRefresh() {
  if (!selectedKeyword.value) return
  isRefreshing.value = true
  await searchComparison(selectedKeyword.value, true)
  isRefreshing.value = false
}

function handleHistoryClick(entry: { keyword: string }) {
  searchInput.value = entry.keyword
  loadCached(entry.keyword)
}

function openLink(url: string) {
  if (url) window.open(url, '_blank', 'noopener')
}

async function handleDeleteCache(keyword: string) {
  await deleteCache(keyword)
  toast({ title: '已删除比价缓存' })
}

function formatTime(iso: string) {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleString('zh-CN', {
    month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit',
  })
}
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold text-gray-800 mb-6">
      拍机堂比价
    </h1>

    <!-- Search Bar -->
    <div class="mb-6">
      <div class="flex gap-2">
        <div class="relative flex-1">
          <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <Input
            v-model="searchInput"
            placeholder="输入设备型号搜索拍机堂价格，例如：iPhone 15 Pro"
            class="pl-10 h-11 text-base"
            @keyup.enter="handleSearch"
          />
        </div>
        <Button @click="handleSearch" :disabled="isLoading" class="h-11 px-6">
          <Search class="w-4 h-4 mr-2" />
          搜索比价
        </Button>
      </div>
      <p class="text-xs text-slate-400 mt-2">
        输入设备型号关键词，系统会搜索拍机堂同款商品价格进行对比。已查询过的关键词会缓存，无需重复搜索。
      </p>
    </div>

    <div class="flex gap-6">
      <!-- Left: History Sidebar -->
      <div class="w-56 flex-shrink-0">
        <div class="rounded-xl border border-slate-200/60 bg-white/60 p-3">
          <p class="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">比价记录</p>
          <div v-if="history.length === 0" class="text-xs text-slate-400 py-4 text-center">
            暂无比价记录
          </div>
          <div v-else class="space-y-1 max-h-[60vh] overflow-y-auto">
            <button
              v-for="entry in history"
              :key="entry.keyword"
              type="button"
              class="w-full text-left px-2.5 py-2 rounded-lg text-xs transition-colors"
              :class="selectedKeyword === entry.keyword ? 'bg-primary/10 text-primary font-semibold' : 'text-slate-600 hover:bg-slate-50'"
              @click="handleHistoryClick(entry)"
            >
              <div class="truncate">{{ entry.keyword }}</div>
              <div class="flex items-center gap-2 mt-0.5 text-[10px] text-slate-400">
                <span>{{ entry.result_count }} 条结果</span>
                <span>·</span>
                <span>{{ formatTime(entry.updated_at) }}</span>
              </div>
            </button>
          </div>
        </div>
      </div>

      <!-- Right: Main Content -->
      <div class="flex-1 min-w-0">
        <!-- Error Alert -->
        <div v-if="error" class="bg-rose-50 border border-rose-200 rounded-xl p-4 mb-4">
          <p class="text-sm text-rose-700">{{ error }}</p>
        </div>

        <!-- No Results State -->
        <div v-if="!selectedKeyword && results.length === 0 && !isLoading" class="text-center py-20">
          <div class="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-slate-100 mb-4">
            <DollarSign class="w-10 h-10 text-slate-300" />
          </div>
          <p class="text-slate-500 text-lg font-medium mb-2">输入型号开始比价</p>
          <p class="text-slate-400 text-sm">对比闲鱼与拍机堂的同款商品价格，找到最优渠道</p>
        </div>

        <!-- Loading -->
        <div v-if="isLoading" class="flex items-center justify-center py-16">
          <Loader2 class="w-6 h-6 text-primary animate-spin mr-3" />
          <span class="text-slate-500">正在搜索拍机堂...</span>
        </div>

        <!-- Results -->
        <div v-if="!isLoading && selectedKeyword && (results.length > 0 || isCached)">
          <!-- Summary Cards -->
          <div class="grid grid-cols-4 gap-3 mb-4">
            <Card class="border-none shadow-sm bg-white/70">
              <CardContent class="p-3">
                <div class="flex items-center gap-1.5 text-[10px] font-medium text-slate-400 mb-1">
                  <Package class="w-3 h-3" /> 找到商品
                </div>
                <div class="text-xl font-bold text-slate-800">{{ resultCount }}</div>
              </CardContent>
            </Card>
            <Card class="border-none shadow-sm bg-white/70">
              <CardContent class="p-3">
                <div class="flex items-center gap-1.5 text-[10px] font-medium text-slate-400 mb-1">
                  <DollarSign class="w-3 h-3" /> 均价
                </div>
                <div class="text-xl font-bold text-emerald-600">¥{{ summary.avg_price ?? '—' }}</div>
              </CardContent>
            </Card>
            <Card class="border-none shadow-sm bg-white/70">
              <CardContent class="p-3">
                <div class="flex items-center gap-1.5 text-[10px] font-medium text-slate-400 mb-1">
                  <TrendingDown class="w-3 h-3" /> 最低价
                </div>
                <div class="text-xl font-bold text-rose-600">¥{{ summary.min_price ?? '—' }}</div>
              </CardContent>
            </Card>
            <Card class="border-none shadow-sm bg-white/70">
              <CardContent class="p-3">
                <div class="flex items-center gap-1.5 text-[10px] font-medium text-slate-400 mb-1">
                  <TrendingUp class="w-3 h-3" /> 最高价
                </div>
                <div class="text-xl font-bold text-amber-600">¥{{ summary.max_price ?? '—' }}</div>
              </CardContent>
            </Card>
          </div>

          <!-- Action Bar -->
          <div class="flex items-center justify-between mb-4">
            <div class="flex items-center gap-2">
              <Badge v-if="isCached" variant="secondary" class="text-[10px]">
                <Clock class="w-3 h-3 mr-1" /> 缓存数据
              </Badge>
              <span class="text-xs text-slate-400">
                关键词「{{ selectedKeyword }}」· {{ resultCount }} 条结果
              </span>
            </div>
            <div class="flex gap-2">
              <Button variant="outline" size="sm" @click="handleRefresh" :disabled="isRefreshing">
                <RefreshCw class="w-3.5 h-3.5 mr-1.5" :class="{ 'animate-spin': isRefreshing }" />
                刷新数据
              </Button>
              <Button variant="outline" size="sm" @click="handleDeleteCache(selectedKeyword)" class="text-rose-500 hover:text-rose-600">
                <Trash2 class="w-3.5 h-3.5" />
              </Button>
            </div>
          </div>

          <!-- Price Comparison Cards -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
            <Card
              v-for="(item, idx) in sortedByPrice"
              :key="idx"
              class="border-slate-100 shadow-sm hover:shadow-md transition-shadow cursor-pointer bg-white/60"
              @click="openLink(item.link)"
            >
              <CardHeader class="p-3 pb-1">
                <div class="flex items-start justify-between gap-2">
                  <div class="flex items-start gap-3 flex-1 min-w-0">
                    <div class="w-14 h-14 rounded-lg bg-slate-100 flex-shrink-0 overflow-hidden">
                      <img
                        v-if="item.images.length > 0"
                        :src="item.images[0]"
                        class="w-full h-full object-cover"
                        loading="lazy"
                      />
                      <div v-else class="w-full h-full flex items-center justify-center">
                        <Package class="w-6 h-6 text-slate-300" />
                      </div>
                    </div>
                    <div class="flex-1 min-w-0">
                      <p class="text-sm font-medium text-slate-800 line-clamp-2 leading-snug">
                        {{ item.title }}
                      </p>
                      <div class="flex items-center gap-2 mt-1">
                        <Badge variant="outline" class="text-[10px] px-1.5 py-0">
                          {{ item.condition }}
                        </Badge>
                        <span class="text-[10px] text-slate-400">{{ item.source }}</span>
                      </div>
                    </div>
                  </div>
                  <div class="text-right flex-shrink-0">
                    <p class="text-lg font-bold text-rose-600">{{ item.price_display }}</p>
                  </div>
                </div>
              </CardHeader>
              <CardFooter class="px-3 py-2 border-t border-slate-50 flex justify-between items-center text-[10px]">
                <span class="text-slate-400 flex items-center gap-1">
                  <Clock class="w-3 h-3" /> {{ formatTime(item.search_time) }}
                </span>
                <span class="text-primary font-semibold flex items-center gap-1">
                  查看详情 <ExternalLink class="w-3 h-3" />
                </span>
              </CardFooter>
            </Card>
          </div>

          <!-- Empty Result for this keyword -->
          <div v-if="results.length === 0 && !isCached" class="text-center py-12">
            <div class="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-amber-50 mb-3">
              <Search class="w-8 h-8 text-amber-300" />
            </div>
            <p class="text-slate-500 font-medium">拍机堂未找到匹配商品</p>
            <p class="text-sm text-slate-400 mt-1">换个关键词试试？</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>