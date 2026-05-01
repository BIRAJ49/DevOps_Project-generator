/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        slate: {
          950: '#020617',
        },
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui'],
        mono: ['IBM Plex Mono', 'ui-monospace'],
      },
      boxShadow: {
        glow: '0 0 0 1px rgba(99,102,241,0.4), 0 0 40px rgba(99,102,241,0.18)',
      },
    },
  },
  plugins: [],
};
