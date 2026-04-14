<template>
  <div class="space-y-6">
    <!-- Summary Cards -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
      <!-- Card 1: Countdown -->
      <div class="relative overflow-hidden bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6 group transition-all hover:scale-[1.02]">
        <div class="absolute inset-0 bg-gradient-to-br from-blue-500/10 to-purple-500/10 opacity-0 group-hover:opacity-100 transition-opacity"></div>
        <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400">{{ $t('halving.nextHalving') }}</h3>
        <p class="mt-2 text-3xl font-bold text-gray-900 dark:text-white">{{ nextHalvingDate }}</p>
        <div class="mt-2 flex items-center text-sm font-medium text-blue-600 dark:text-blue-400">
          <ClockIcon class="w-4 h-4 mr-1" />
          <span>{{ daysToHalving }} {{ $t('halving.daysLeft') }}</span>
        </div>
      </div>

      <!-- Card 2: Price -->
      <div class="relative overflow-hidden bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6 group transition-all hover:scale-[1.02]">
        <div class="absolute inset-0 bg-gradient-to-br from-green-500/10 to-emerald-500/10 opacity-0 group-hover:opacity-100 transition-opacity"></div>
        <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400">{{ $t('halving.currentPrice') }}</h3>
        <p class="mt-2 text-3xl font-bold text-gray-900 dark:text-white">
          {{ formatPrice(currentPrice) }}
        </p>
        <p class="mt-1 text-xs text-gray-500">BTC/USDT</p>
      </div>

      <!-- Card 3: Cycle Progress -->
      <div class="md:col-span-2 relative overflow-hidden bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6">
        <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-4">{{ $t('halving.cycleProgress') }}</h3>
        <div class="relative pt-1">
          <div class="flex mb-2 items-center justify-between">
            <div class="text-xs font-semibold inline-block py-1 px-2 uppercase rounded-full text-blue-600 bg-blue-200 dark:bg-blue-900 dark:text-blue-300">
              {{ $t('halving.inProgress') }}
            </div>
            <div class="text-right">
              <span class="text-xs font-semibold inline-block text-blue-600 dark:text-blue-400">
                {{ cycleProgress }}%
              </span>
            </div>
          </div>
          <div class="overflow-hidden h-3 mb-4 text-xs flex rounded-full bg-gray-200 dark:bg-gray-700">
            <div :style="{ width: cycleProgress + '%' }" class="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center bg-gradient-to-r from-blue-500 to-purple-600 transition-all duration-1000 ease-out"></div>
          </div>
          <div class="flex justify-between text-xs text-gray-400">
            <span>2024-04-20</span>
            <span>Est. 2028-04-17</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Main Chart -->
    <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6 border border-gray-100 dark:border-gray-700">
      <div class="flex flex-col sm:flex-row justify-between items-center mb-6">
        <div>
           <h2 class="text-xl font-bold text-gray-900 dark:text-white flex items-center">
             <ChartBarIcon class="w-6 h-6 mr-2 text-blue-500" />
             {{ $t('halving.chartTitle') }}
           </h2>
           <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
             {{ $t('halving.chartDesc') }}
             <span class="inline-flex items-center ml-2 space-x-2">
                <span class="w-3 h-3 rounded-sm bg-green-500/20 border border-green-500/50"></span>
                <span class="text-xs">{{ $t('halving.accumulation') }}</span>
                <span class="w-3 h-3 rounded-sm bg-orange-500/20 border border-orange-500/50"></span>
                <span class="text-xs">{{ $t('halving.bullRun') }}</span>
             </span>
           </p>
        </div>

        <div class="flex items-center space-x-4 mt-4 sm:mt-0">
           <!-- Scale Toggle -->
           <div class="flex bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
               <button 
                  @click="scaleType = 'logarithmic'" 
                  class="px-3 py-1 text-xs font-medium rounded-md transition-all"
                  :class="scaleType === 'logarithmic' ? 'bg-white dark:bg-gray-600 shadow text-blue-600 dark:text-blue-300' : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'"
               >
                  {{ $t('halving.log') }}
               </button>
               <button 
                  @click="scaleType = 'linear'" 
                  class="px-3 py-1 text-xs font-medium rounded-md transition-all"
                  :class="scaleType === 'linear' ? 'bg-white dark:bg-gray-600 shadow text-blue-600 dark:text-blue-300' : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'"
               >
                  {{ $t('halving.linear') }}
               </button>
           </div>

           <!-- Phases Toggle -->
           <label class="inline-flex items-center cursor-pointer">
              <input type="checkbox" v-model="showPhases" class="sr-only peer">
              <div class="relative w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
              <span class="ms-3 text-sm font-medium text-gray-900 dark:text-gray-300">{{ $t('halving.phases') }}</span>
            </label>
        </div>
      </div>
      
      <div class="relative h-[600px] w-full bg-gray-50 dark:bg-[#0B1120] rounded-xl p-2 border border-gray-100 dark:border-gray-800">
        <canvas ref="chartCanvas"></canvas>
        <div v-if="loading" class="absolute inset-0 flex items-center justify-center bg-gray-50/80 dark:bg-gray-900/80 backdrop-blur-sm rounded-xl">
          <div class="flex flex-col items-center">
             <div class="animate-spin rounded-full h-12 w-12 border-4 border-blue-500 border-t-transparent"></div>
             <span class="mt-3 text-sm text-gray-500 font-medium">{{ $t('halving.loading') }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ClockIcon, ChartBarIcon } from '@heroicons/vue/24/outline'
import { useHalvingPage } from '@/modules/market'

const {
  loading,
  chartCanvas,
  currentPrice,
  showPhases,
  scaleType,
  nextHalvingDate,
  daysToHalving,
  cycleProgress,
  formatPrice,
} = useHalvingPage()
</script>
