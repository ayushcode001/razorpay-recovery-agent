/** @type {import('tailwindcss').Config} */
// Design system: Stitch asset 10029575973333261191
// "Razorpay Recovery Agent" — Light mode, Inter, Tonal Spot, Primary #2563EB
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#2748E0',
          hover: '#1E3AB8',
          dark: '#1E3AB8',
          light: '#EBF0FF',
          50: '#F0F4FF',
          100: '#DBEAFE',
          600: '#2748E0',
          700: '#1E3AB8',
        },
        navy: {
          DEFAULT: '#111827',
          light: '#1F2937',
          muted: '#374151',
        },
        surface: {
          DEFAULT: '#FFFFFF',
          muted: '#F5F6F8',
          subtle: '#F9FAFB',
          border: '#E5E7EB',
          'border-dark': '#D1D5DB',
        },
        muted: {
          DEFAULT: '#6B7280',
          light: '#9CA3AF',
          lighter: '#E5E7EB',
        },
        success: {
          DEFAULT: '#3A8A5E',
          light: '#EAF5EF',
          text: '#2E6E4B',
        },
        warning: {
          DEFAULT: '#B8862E',
          light: '#FDF7EA',
          text: '#946B24',
        },
        danger: {
          DEFAULT: '#C4483C',
          light: '#FBECEB',
          text: '#9E3A30',
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
        xs: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
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
