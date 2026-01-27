/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{vue,js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                // 自定义 Heimdall 风格颜色
                'heimdall-dark': '#0f172a',
                'heimdall-panel': '#1e293b',
                'heimdall-accent': '#3b82f6',
            }
        },
    },
    plugins: [],
}
