<template>
  <div class="h-full flex flex-col p-6 space-y-6">
      <h2 class="text-2xl font-bold mb-4 text-gray-900 dark:text-white">{{ $t('settings.title') }}</h2>

      <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 transition-colors">
          <p class="text-gray-600 dark:text-gray-400">{{ $t('settings.comingSoon') }}</p>
          <p class="text-sm mt-4 text-gray-500">
              {{ $t('settings.env') }}: {{ $t('settings.production') }}<br>
              {{ $t('settings.version') }}: 2.0.0 (Vue + FastAPI)<br>
              {{ $t('settings.db') }}: PostgreSQL<br>
              {{ $t('settings.cache') }}: Redis
          </p>
      </div>
  </div>
</template>
