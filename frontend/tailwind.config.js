/** @type {import('tailwindcss').Config} */
// Design system: Stitch asset 10029575973333261191
// "Razorpay Recovery Agent" — Light mode, Inter, Tonal Spot, Primary #2563EB
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#2563EB',
          light: '#DBEAFE',
          dark: '#1D4ED8',
          50: '#EFF6FF',
          100: '#DBEAFE',
          600: '#2563EB',
          700: '#1D4ED8',
          800: '#1E40AF',
        },
        navy: {
          DEFAULT: '#0F172A',
          light: '#1E293B',
          muted: '#334155',
        },
        surface: {
          DEFAULT: '#FFFFFF',
          muted: '#F8FAFC',
          subtle: '#F1F5F9',
          border: '#E2E8F0',
          'border-dark': '#CBD5E1',
        },
        muted: {
          DEFAULT: '#64748B',
          light: '#94A3B8',
          lighter: '#CBD5E1',
        },
        amber: {
          DEFAULT: '#C9962A',
          light: '#F5E6C8',
          dark: '#A6781D',
          hover: '#D9AA40',
          glow: 'rgba(201, 150, 42, 0.35)',
          subtle: 'rgba(201, 150, 42, 0.12)',
        },
        dark: {
          bg: '#0C0C0E',
          section: '#0E0E11',
          surface: '#121215',
          card: 'rgba(255, 255, 255, 0.03)',
          border: 'rgba(255, 255, 255, 0.08)',
          'border-hover': 'rgba(201, 150, 42, 0.4)',
          cream: '#EDE8DC',
          muted: '#9A9585',
          subtle: '#666155',
        },
        success: {
          DEFAULT: '#16A34A',
          light: '#DCFCE7',
          text: '#15803D',
        },
        warning: {
          DEFAULT: '#D97706',
          light: '#FEF3C7',
          text: '#B45309',
        },
        danger: {
          DEFAULT: '#DC2626',
          light: '#FEE2E2',
          text: '#B91C1C',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      fontSize: {
        '2xs': ['11px', { lineHeight: '1.4' }],
        xs: ['12px', { lineHeight: '1.4' }],
        sm: ['13px', { lineHeight: '1.5' }],
        base: ['14px', { lineHeight: '1.5' }],
        md: ['16px', { lineHeight: '1.6' }],
        lg: ['18px', { lineHeight: '1.6' }],
        xl: ['20px', { lineHeight: '1.35' }],
        '2xl': ['24px', { lineHeight: '1.3', letterSpacing: '-0.01em' }],
        '3xl': ['30px', { lineHeight: '1.2', letterSpacing: '-0.015em' }],
        '4xl': ['36px', { lineHeight: '1.15', letterSpacing: '-0.015em' }],
        '5xl': ['48px', { lineHeight: '1.1', letterSpacing: '-0.02em' }],
      },
      borderRadius: {
        sm: '4px',
        DEFAULT: '6px',
        md: '8px',
        lg: '12px',
        xl: '16px',
      },
      boxShadow: {
        sm: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
        DEFAULT: '0 1px 3px 0 rgb(0 0 0 / 0.08), 0 1px 2px -1px rgb(0 0 0 / 0.05)',
        md: '0 4px 6px -1px rgb(0 0 0 / 0.07), 0 2px 4px -2px rgb(0 0 0 / 0.05)',
        lg: '0 10px 15px -3px rgb(0 0 0 / 0.07), 0 4px 6px -4px rgb(0 0 0 / 0.04)',
      },
      spacing: {
        18: '4.5rem',
        22: '5.5rem',
      },
    },
  },
  plugins: [],
}
