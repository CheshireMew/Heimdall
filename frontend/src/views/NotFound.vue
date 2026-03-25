<template>
  <div class="h-full flex flex-col items-center justify-center p-6 text-center">
    <div class="text-6xl font-bold text-gray-300 dark:text-gray-600 mb-4">404</div>
    <p class="text-gray-500 dark:text-gray-400 mb-6">{{ $t ? $t('notFound.message') : 'Page not found' }}</p>
    <router-link
      to="/"
      class="bg-blue-600 hover:bg-blue-500 text-white px-6 py-2 rounded-lg font-bold transition"
    >
      {{ $t ? $t('notFound.back') : 'Back to Dashboard' }}
    </router-link>
  </div>
</template>
