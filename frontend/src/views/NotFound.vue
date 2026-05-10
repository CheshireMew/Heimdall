<template>
  <div class="app-page flex flex-col items-center justify-center p-6 text-center">
    <div class="mb-4 text-6xl font-bold text-stone-300 dark:text-gray-600">404</div>
    <p class="mb-6 text-stone-500 dark:text-gray-400">{{ $t ? $t('notFound.message') : 'Page not found' }}</p>
    <router-link
      to="/"
      class="app-button-primary px-6 py-2"
    >
      {{ $t ? $t('notFound.back') : 'Back to Dashboard' }}
    </router-link>
  </div>
</template>
