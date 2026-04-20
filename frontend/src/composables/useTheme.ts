import { ref, watchEffect, type Ref } from 'vue'
import { getLocalStorage } from '@/utils/storage'

type Theme = 'light' | 'dark'

const readStoredTheme = (): Theme => {
    const storage = getLocalStorage()
    if (storage === null) return 'dark'
    const stored = storage.getItem('theme')
    return stored === 'light' ? 'light' : 'dark'
}

const theme: Ref<Theme> = ref(readStoredTheme())

watchEffect(() => {
    if (typeof window === 'undefined') return
    const root = window.document.documentElement
    root.classList.remove('light', 'dark')
    root.classList.add(theme.value)
    getLocalStorage()?.setItem('theme', theme.value)
})

export function useTheme() {
    const toggleTheme = () => {
        theme.value = theme.value === 'dark' ? 'light' : 'dark'
    }

    return {
        theme,
        toggleTheme
    }
}
