<template>
  <div class="relative">
    <button
      type="button"
      class="symbol-trigger"
      :class="triggerClass"
      @click="openSearch"
    >
      <span class="truncate" :class="displayText ? 'text-gray-900 dark:text-white' : 'text-gray-400 dark:text-gray-500'">
        {{ displayText || placeholderText }}
      </span>
      <MagnifyingGlassIcon class="h-4 w-4 shrink-0 text-gray-400" />
    </button>

    <Teleport to="body">
      <div v-if="open" class="fixed inset-0 z-50 bg-black/30 p-3 backdrop-blur-sm sm:p-6" @click.self="closeSearch">
        <section class="mx-auto flex max-h-[88vh] w-full max-w-5xl flex-col overflow-hidden rounded-lg bg-white shadow-2xl dark:bg-gray-900">
          <div class="flex items-center justify-between border-b border-gray-200 px-5 py-4 dark:border-gray-700">
            <h2 class="text-lg font-semibold text-gray-950 dark:text-white">{{ t('symbolSearch.title') }}</h2>
            <button type="button" class="rounded-lg p-2 text-gray-500 transition hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800" @click="closeSearch">
              <XMarkIcon class="h-5 w-5" />
            </button>
          </div>

          <div class="border-b border-gray-200 p-4 dark:border-gray-700">
            <div class="flex items-center rounded-lg border border-gray-300 bg-white px-3 dark:border-gray-600 dark:bg-gray-950">
              <MagnifyingGlassIcon class="h-5 w-5 shrink-0 text-gray-400" />
              <input
                ref="searchInput"
                v-model.trim="query"
                type="text"
                class="h-12 min-w-0 flex-1 bg-transparent px-3 text-base text-gray-950 outline-none dark:text-white"
                :placeholder="placeholderText"
                @keydown.enter.prevent="selectFirst"
                @keydown.esc.prevent="closeSearch"
              />
              <button
                v-if="query"
                type="button"
                class="rounded-lg p-1 text-gray-400 transition hover:bg-gray-100 hover:text-gray-600 dark:hover:bg-gray-800"
                @click="query = ''"
              >
                <XMarkIcon class="h-4 w-4" />
              </button>
            </div>

            <div class="mt-4 flex flex-wrap gap-2">
              <button
                v-for="tab in visibleTabs"
                :key="tab.value"
                type="button"
                class="rounded-lg px-3 py-1.5 text-sm font-medium transition"
                :class="activeClass === tab.value ? 'bg-gray-900 text-white dark:bg-white dark:text-gray-950' : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-200 dark:hover:bg-gray-700'"
                @click="activeClass = tab.value"
              >
                {{ tab.label }}
              </button>
            </div>
          </div>

          <div class="min-h-0 flex-1 overflow-y-auto">
            <button
              v-for="item in filteredSymbols"
              :key="item.symbol"
              type="button"
              class="grid w-full grid-cols-[minmax(6rem,10rem)_minmax(0,1fr)_5rem_6rem] items-center gap-3 border-b border-gray-100 px-5 py-3 text-left transition hover:bg-gray-50 dark:border-gray-800 dark:hover:bg-gray-800/70"
              :class="[
                isSelected(item) ? 'bg-blue-50 dark:bg-blue-950/30' : '',
                isDisabled(item) ? 'cursor-not-allowed opacity-45 hover:bg-transparent dark:hover:bg-transparent' : '',
              ]"
              @click="choose(item)"
            >
              <span class="font-semibold text-blue-600 dark:text-blue-300">{{ item.symbol }}</span>
              <span class="min-w-0 truncate text-gray-900 dark:text-white">{{ item.name }}</span>
              <span class="text-sm text-gray-500 dark:text-gray-400">{{ marketLabel(item) }}</span>
              <span class="justify-self-end rounded-lg bg-gray-100 px-2 py-1 text-xs font-medium text-gray-600 dark:bg-gray-800 dark:text-gray-300">
                {{ isDisabled(item) ? disabledText : classLabel(item.asset_class) }}
              </span>
            </button>

            <div v-if="!filteredSymbols.length" class="px-5 py-10 text-center text-sm text-gray-500 dark:text-gray-400">
              {{ t('symbolSearch.noMatches') }}
            </div>
          </div>
        </section>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { MagnifyingGlassIcon, XMarkIcon } from '@heroicons/vue/24/outline'
import { toBaseSymbol, useSymbolCatalog } from '@/modules/market'
import type { MarketSymbolSearchItem } from '@/types'

const props = withDefaults(defineProps<{
  modelValue: string | string[]
  multiple?: boolean
  allowedClasses?: string[]
  outputMode?: 'symbol' | 'base'
  placeholder?: string
  triggerClass?: string
  disabledLabel?: string
}>(), {
  multiple: false,
  allowedClasses: () => ['crypto', 'index'],
  outputMode: 'symbol',
  placeholder: '',
  triggerClass: '',
  disabledLabel: '',
})

const emit = defineEmits<{
  'update:modelValue': [value: string | string[]]
  select: [item: MarketSymbolSearchItem]
}>()

const { t } = useI18n()
const { symbols, loadSymbols } = useSymbolCatalog()
const open = ref(false)
const query = ref('')
const searchInput = ref<HTMLInputElement | null>(null)
const activeClass = ref('all')

const placeholderText = computed(() => props.placeholder || t('symbolSearch.placeholder'))
const disabledText = computed(() => props.disabledLabel || t('symbolSearch.disabled'))
const tabs = computed(() => [
  { value: 'all', label: t('symbolSearch.tabs.all') },
  { value: 'crypto', label: t('symbolSearch.tabs.crypto') },
  { value: 'index', label: t('symbolSearch.tabs.index') },
  { value: 'cash', label: t('symbolSearch.tabs.cash') },
])

const visibleTabs = computed(() => tabs.value.filter((tab) => tab.value === 'all' || props.allowedClasses.includes(tab.value)))

const normalizedSelected = computed(() => {
  const value = props.modelValue
  return Array.isArray(value) ? value : String(value || '').split(',').map((item) => item.trim()).filter(Boolean)
})

const displayText = computed(() => {
  if (props.multiple) return normalizedSelected.value.join(', ')
  return String(props.modelValue || '')
})

const candidates = computed(() => symbols.value)

const filteredSymbols = computed(() => {
  const needle = query.value.toUpperCase()
  return candidates.value
    .filter((item) => activeClass.value === 'all' || item.asset_class === activeClass.value)
    .filter((item) => {
      if (!needle) return true
      return `${item.symbol} ${item.name} ${item.market} ${item.exchange || ''} ${(item.aliases || []).join(' ')}`.toUpperCase().includes(needle)
    })
    .slice(0, 80)
})

const outputValue = (item: MarketSymbolSearchItem) => props.outputMode === 'base' ? toBaseSymbol(item.symbol) : item.symbol

const openSearch = async () => {
  open.value = true
  await loadSymbols()
  await nextTick()
  searchInput.value?.focus()
}

const closeSearch = () => {
  open.value = false
  query.value = ''
}

const choose = (item: MarketSymbolSearchItem) => {
  if (isDisabled(item)) return
  const value = outputValue(item)
  if (props.multiple) {
    const current = normalizedSelected.value
    emit('update:modelValue', current.includes(value)
      ? current.filter((item) => item !== value)
      : [...current, value])
  } else {
    emit('update:modelValue', value)
    closeSearch()
  }
  emit('select', item)
}

const selectFirst = () => {
  const first = filteredSymbols.value[0]
  if (first) choose(first)
}

const isSelected = (item: MarketSymbolSearchItem) => normalizedSelected.value.includes(outputValue(item))
const isDisabled = (item: MarketSymbolSearchItem) => !props.allowedClasses.includes(item.asset_class)
const classLabel = (value: string) => {
  if (value === 'crypto') return t('symbolSearch.tabs.crypto')
  if (value === 'index') return t('symbolSearch.tabs.index')
  if (value === 'cash') return t('symbolSearch.tabs.cash')
  return value
}
const marketLabel = (item: MarketSymbolSearchItem) => item.exchange || item.market

onMounted(() => {
  loadSymbols()
})
</script>

<style scoped>
.symbol-trigger {
  @apply flex h-10 w-full items-center justify-between gap-2 rounded-lg border border-gray-300 bg-gray-50 px-3 text-left text-sm outline-none transition hover:border-blue-400 focus:border-blue-500 dark:border-gray-600 dark:bg-gray-900;
}
</style>
