import { ref, watchEffect, type Ref } from 'vue'

type Theme = 'light' | 'dark'

const theme: Ref<Theme> = ref((localStorage.getItem('theme') as Theme) || 'dark')

watchEffect(() => {
    const root = window.document.documentElement
    root.classList.remove('light', 'dark')
    root.classList.add(theme.value)
    localStorage.setItem('theme', theme.value)
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
