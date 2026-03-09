/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['-apple-system', 'BlinkMacSystemFont', '"SF Pro Text"', '"PingFang SC"', '"Microsoft YaHei"', 'sans-serif'],
      },
      colors: {
        surface: {
          DEFAULT: '#ffffff',
          dark: '#1e1e1e',
        },
        sidebar: {
          DEFAULT: '#f9fafb',
          dark: '#171717',
        },
        border: {
          DEFAULT: '#e5e7eb',
          dark: '#2e2e2e',
        },
      },
    },
  },
  plugins: [],
}
