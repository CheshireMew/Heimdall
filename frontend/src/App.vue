<template>
  <div class="min-h-screen bg-gray-900 text-white flex">
    <!-- Sidebar (Optimized) -->
    <aside class="w-56 bg-gray-800 border-r border-gray-700 flex-shrink-0">
      <div class="p-5">
        <h1 class="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-teal-400">
          Heimdall
        </h1>
        <p class="text-xs text-gray-500 mt-1">AI Crypto Assistant</p>
      </div>
      
      <nav class="mt-4 px-3 space-y-1">
        <router-link to="/" class="block px-3 py-2 rounded-lg hover:bg-gray-700 transition flex items-center text-sm" active-class="bg-blue-600">
          <ChartBarSquareIcon class="w-5 h-5 mr-2.5" /> 实时分析
        </router-link>
        
        <div class="px-3 py-2 text-xs text-gray-500 font-bold uppercase mt-3">Tools</div>
        
        <router-link to="/backtest" class="block px-3 py-2 rounded-lg hover:bg-gray-700 transition flex items-center text-sm" active-class="bg-blue-600">
          <BeakerIcon class="w-5 h-5 mr-2.5" /> 回测中心
        </router-link>
        <router-link to="/tools/compare" class="block px-3 py-2 rounded-lg hover:bg-gray-700 transition flex items-center text-sm" active-class="bg-blue-600">
          <ScaleIcon class="w-5 h-5 mr-2.5" /> 币种对比
        </router-link>
        <router-link to="/tools/dca" class="block px-3 py-2 rounded-lg hover:bg-gray-700 transition flex items-center text-sm" active-class="bg-blue-600">
          <BanknotesIcon class="w-5 h-5 mr-2.5" /> DCA模拟
        </router-link>
        
        <div class="px-3 py-2 text-xs text-gray-500 font-bold uppercase mt-3">System</div>
        
        <router-link to="/settings" class="block px-3 py-2 rounded-lg hover:bg-gray-700 transition flex items-center text-sm" active-class="bg-blue-600">
          <CogIcon class="w-5 h-5 mr-2.5" /> 配置中心
        </router-link>
      </nav>
    </aside>

    <!-- Main Content -->
    <main class="flex-1 overflow-auto">
      <router-view></router-view>
    </main>
  </div>
</template>

<script setup>
import { 
  ChartBarSquareIcon, 
  BeakerIcon, 
  ScaleIcon, 
  BanknotesIcon, 
  CogIcon 
} from '@heroicons/vue/24/outline'
</script>
