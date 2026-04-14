<template>
  <div class="h-full flex flex-col p-6 space-y-4">
    <!-- Configuration -->
    <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 transition-colors">
      <h2 class="text-xl font-bold mb-4 flex items-center text-gray-900 dark:text-white">
        <BanknotesIcon class="w-6 h-6 mr-2 text-green-600 dark:text-green-400" />
        {{ $t('dca.config') }}
      </h2>
      
      <div class="grid grid-cols-1 md:grid-cols-6 gap-4 items-end">
        <div>
          <label class="block text-gray-500 dark:text-gray-400 text-xs font-bold mb-1">{{ $t('dca.pair') }}</label>
          <SymbolSearchBox v-model="config.symbol" placeholder="Search symbol" />
        </div>
        <div>
          <AppDateField
            v-model="config.start_date"
            :label="$t('dca.startDate')"
            input-class="w-full bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-gray-900 dark:text-white outline-none transition-colors"
            label-class="block text-gray-500 dark:text-gray-400 text-xs font-bold mb-1"
          />
        </div>
        <div>
          <label class="block text-gray-500 dark:text-gray-400 text-xs font-bold mb-1">{{ $t('dca.investTime') }}</label>
          <select v-model="config.investment_time" class="w-full bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-gray-900 dark:text-white outline-none transition-colors">
            <option value="00:00">00:00</option>
            <option value="02:00">02:00</option>
            <option value="04:00">04:00</option>
            <option value="06:00">06:00</option>
            <option value="08:00">08:00</option>
            <option value="10:00">10:00</option>
            <option value="12:00">12:00</option>
            <option value="14:00">14:00</option>
            <option value="16:00">16:00</option>
            <option value="18:00">18:00</option>
            <option value="20:00">20:00</option>
            <option value="22:00">22:00</option>
            <option value="23:00">23:00</option>
          </select>
        </div>
        
        <!-- Strategy Selector -->
        <div>
           <label class="block text-gray-500 dark:text-gray-400 text-xs font-bold mb-1">{{ $t('dca.strategy') }}</label>
           <select v-model="config.strategy" class="w-full bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-gray-900 dark:text-white outline-none transition-colors">
             <option value="standard">{{ $t('dca.strategies.standard') }}</option>
             <option value="ema_deviation">{{ $t('dca.strategies.ema20') }}</option>
             <option value="rsi_dynamic">{{ $t('dca.strategies.rsi') }}</option>
             <option v-if="!isIndexSelected" value="ahr999">{{ $t('dca.strategies.ahr999') }}</option>
             <option v-if="!isIndexSelected" value="fear_greed">{{ $t('dca.strategies.fg') }}</option>
             <option value="value_averaging">{{ $t('dca.strategies.va') }}</option>
           </select>
        </div>

        <div>
           <label class="block text-gray-500 dark:text-gray-400 text-xs font-bold mb-1">{{ $t('dca.timezone') }}</label>
           <AppTimezoneSelect />
        </div>

        <div>
          <label class="block text-gray-500 dark:text-gray-400 text-xs font-bold mb-1">
              {{ config.strategy === 'value_averaging' ? $t('dca.dailyTarget', { currency: displayCurrency }) : $t('dca.dailyBase', { currency: displayCurrency }) }}
          </label>
          <input v-model.number="displayAmount" type="number" class="w-full bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-gray-900 dark:text-white outline-none transition-colors" />
        </div>

        <!-- Strategy Params (Conditional) -->
        <div v-if="config.strategy !== 'standard' && config.strategy !== 'value_averaging'">
           <label class="block text-gray-500 dark:text-gray-400 text-xs font-bold mb-1 flex justify-between">
              <span>{{ $t('dca.strength') }}</span>
              <span class="text-gray-500 font-normal">
                  {{
                      config.strategy === 'ema_deviation' ? `${$t('dca.recommended')}: 2.0 - 5.0` :
                      config.strategy === 'rsi_dynamic' ? `${$t('dca.recommended')}: 1.0 - 3.0` :
                      config.strategy === 'ahr999' ? `${$t('dca.recommended')}: 0.5 - 2.0` :
                      config.strategy === 'fear_greed' ? `${$t('dca.recommended')}: 1.0 - 3.0` : ''
                  }}
              </span>
           </label>
           <input v-model.number="config.strategy_params.multiplier" type="number" step="0.1" class="w-full bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-gray-900 dark:text-white outline-none transition-colors" />
        </div>
        
        <button @click="runSimulation" :disabled="loading" class="bg-gradient-to-r from-green-600 to-teal-600 hover:opacity-90 text-white px-6 py-2 rounded-lg font-bold transition flex items-center justify-center disabled:opacity-50 col-span-1 md:col-span-2 shadow-md">
          <span v-if="loading" class="mr-2 animate-spin">⟳</span>
          {{ $t('dca.calculate') }}
        </button>
      </div>
    </div>

    <!-- Market Indicators Card -->
    <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4 transition-colors">
       <h3 class="text-sm font-bold mb-3 flex items-center text-gray-900 dark:text-white">
         <ChartBarIcon class="w-5 h-5 mr-1.5 text-blue-500 dark:text-blue-400" />
         {{ $t('dca.market') }}
       </h3>
       
       <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <!-- 当前币价 -->
          <div class="text-center">
             <div class="text-gray-500 dark:text-gray-400 text-xs uppercase mb-1">{{ $t('dca.currentPrice') }}</div>
             <div class="text-2xl font-bold text-blue-600 dark:text-blue-400">{{ result ? formatMoney(result.current_price, result.pricing_currency || 'USDT') : '--' }}</div>
             <div v-if="result?.pricing_symbol" class="text-xs text-gray-500 mt-0.5">{{ result.pricing_symbol }}</div>
          </div>
          
          <!-- RSI -->
          <div class="text-center">
             <div class="text-gray-500 dark:text-gray-400 text-xs uppercase mb-1">{{ $t('dca.rsi14') }}</div>
             <div class="text-2xl font-bold text-purple-600 dark:text-purple-400">{{ marketData.rsi || '--' }}</div>
          </div>
          
          <!-- 恐惧贪婪指数 -->
          <div class="text-center">
             <div class="text-gray-500 dark:text-gray-400 text-xs uppercase mb-1">{{ $t('dca.fgIndex') }}</div>
             <div class="text-2xl font-bold" :class="sentimentClass">
               {{ marketData.sentiment || '--' }}
             </div>
             <div class="text-xs text-gray-500 mt-0.5">{{ marketData.sentimentLabel || '' }}</div>
          </div>
       </div>
    </div>

    <!-- Results - 统一的资产概览 (Always visible) -->
    <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4 transition-colors">
       <h3 class="text-sm font-bold mb-3 pb-2 border-b border-gray-200 dark:border-gray-700 flex items-center text-gray-900 dark:text-white">
         <WalletIcon class="w-5 h-5 mr-1.5 text-yellow-500 dark:text-yellow-400" />
         {{ $t('dca.asset') }}
       </h3>
       
       <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          <!-- 1. 平均成本 -->
          <div class="text-center">
             <div class="text-gray-500 dark:text-gray-400 text-xs uppercase mb-1">{{ $t('dca.avgCost') }}</div>
             <div class="text-xl font-bold text-yellow-600 dark:text-yellow-400">{{ result ? formatMoney(result.average_cost, result.pricing_currency || 'USDT') : '--' }}</div>
          </div>
          
          <!-- 2. ROI -->
          <div class="text-center">
             <div class="text-gray-500 dark:text-gray-400 text-xs uppercase mb-1">{{ $t('dca.roi') }}</div>
             <div class="text-xl font-bold" :class="isPositiveRoi ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'">
               {{ result ? (result.roi || 0).toFixed(2) : '--' }}%
             </div>
          </div>
          
          <!-- 3. 总投入 -->
          <div class="text-center">
             <div class="text-gray-500 dark:text-gray-400 text-xs uppercase mb-1">{{ $t('dca.totalInvested') }}</div>
             <div class="text-xl font-bold text-gray-900 dark:text-white">{{ result ? formatMoney(result.total_invested, result.pricing_currency || 'USDT') : '--' }}</div>
          </div>
          
          <!-- 4. 当前价值 -->
          <div class="text-center">
             <div class="text-gray-500 dark:text-gray-400 text-xs uppercase mb-1">{{ $t('dca.currentValue') }}</div>
             <div class="text-xl font-bold text-gray-900 dark:text-white">{{ result ? formatMoney(result.final_value, result.pricing_currency || 'USDT') : '--' }}</div>
          </div>
          
          <!-- 5. 持仓数量 -->
          <div class="text-center">
             <div class="text-gray-500 dark:text-gray-400 text-xs uppercase mb-1">{{ $t('dca.holdings') }}</div>
             <div class="text-xl font-bold text-gray-900 dark:text-white">{{ result ? (result.total_coins || 0).toFixed(6) : '--' }}</div>
          </div>
          
          <!-- 6. 定投天数 -->
          <div class="text-center">
             <div class="text-gray-500 dark:text-gray-400 text-xs uppercase mb-1">{{ $t('dca.dcaDays') }}</div>
             <div class="text-xl font-bold text-gray-700 dark:text-gray-300">{{ result ? (result.total_days || 0) : '--' }}</div>
          </div>
       </div>
    </div>

    <!-- Charts Area - 3 Charts Layout (Always visible) -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <!-- 1. ROI Trend Chart -->
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-3 transition-colors">
            <h3 class="text-xs font-bold mb-2 text-gray-500 dark:text-gray-400">{{ $t('dca.roiTrend') }}</h3>
            <div class="h-72">
                <canvas ref="roiChartCanvas"></canvas>
            </div>
        </div>
        
        <!-- 2. Price vs Avg Cost Chart -->
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-3 transition-colors">
            <h3 class="text-xs font-bold mb-2 text-gray-500 dark:text-gray-400">{{ $t('dca.priceVsCost') }}</h3>
            <div class="h-72">
                <canvas ref="priceChartCanvas"></canvas>
            </div>
        </div>
        
        <!-- 3. Daily Investment Amount Chart -->
        <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-3 transition-colors">
            <h3 class="text-xs font-bold mb-2 text-gray-500 dark:text-gray-400">{{ $t('dca.dailyAmount') }}</h3>
            <div class="h-72">
                <canvas ref="investmentChartCanvas"></canvas>
            </div>
        </div>
    </div>

  </div>
</template>

<script setup>
import { BanknotesIcon, ChartBarIcon, WalletIcon } from '@heroicons/vue/24/outline'
import AppDateField from '@/components/AppDateField.vue'
import AppTimezoneSelect from '@/components/AppTimezoneSelect.vue'
import SymbolSearchBox from '@/components/SymbolSearchBox.vue'
import { useDcaPage } from '@/modules/tools'

const {
  config,
  displayAmount,
  loading,
  result,
  marketData,
  roiChartCanvas,
  priceChartCanvas,
  investmentChartCanvas,
  runSimulation,
  isPositiveRoi,
  isIndexSelected,
  sentimentClass,
  displayCurrency,
  formatMoney,
} = useDcaPage()
</script>
