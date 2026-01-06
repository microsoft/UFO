/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        galaxy: {
          dark: '#071A2B',
          darker: '#050816',
          midnight: '#020817',
          blue: '#0F7BFF',
          indigo: '#2E1A6B',
          purple: '#7b2cbf',
          pink: '#ff006e',
          teal: '#38BDF8',
          glow: '#21F0FF',
          gray: {
            100: '#e0e0e0',
            200: '#c0c0c0',
            300: '#a0a0a0',
            400: '#808092',
            500: '#606072',
            600: '#3a3a4a',
            700: '#2a2a38',
            800: '#1a1a24',
            900: '#12121a',
          },
        },
        status: {
          pending: '#94a3b8',
          running: '#38BDF8',
          success: '#34D399',
          warning: '#FBBF24',
          failed: '#F87171',
        },
      },
      fontFamily: {
        sans: ['Inter', 'IBM Plex Sans', 'system-ui', 'sans-serif'],
        heading: ['IBM Plex Sans', 'Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Menlo', 'monospace'],
      },
      boxShadow: {
        glow: '0 0 25px rgba(33, 240, 255, 0.35)',
        neon: '0 0 15px rgba(15, 123, 255, 0.45)',
        inset: 'inset 0 0 30px rgba(15, 123, 255, 0.12)',
      },
      backgroundImage: {
        'starfield': 'radial-gradient(circle at 10% 20%, rgba(33,240,255,0.18), transparent 45%), radial-gradient(circle at 80% 10%, rgba(147,51,234,0.22), transparent 50%), radial-gradient(circle at 50% 80%, rgba(14,116,144,0.3), transparent 55%)',
        'galaxy-panel': 'linear-gradient(145deg, rgba(14,23,42,0.85) 0%, rgba(25,10,45,0.88) 55%, rgba(7,26,43,0.92) 100%)',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'float': 'float 6s ease-in-out infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
        'pulse-glow': 'pulseGlow 2.2s ease-in-out infinite',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-18px)' },
        },
        glow: {
          '0%': { boxShadow: '0 0 6px rgba(15, 123, 255, 0.45)' },
          '100%': { boxShadow: '0 0 26px rgba(33, 240, 255, 0.75)' },
        },
        pulseGlow: {
          '0%, 100%': { opacity: 0.6 },
          '50%': { opacity: 1 },
        },
      },
    },
  },
  plugins: [],
}
