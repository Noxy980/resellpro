/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: { sans: ['Inter', 'system-ui', 'sans-serif'] },
      colors: {
        profit: '#10b981',
        danger: '#ef4444',
        warn: '#f59e0b',
      },
    },
  },
  plugins: [],
}
