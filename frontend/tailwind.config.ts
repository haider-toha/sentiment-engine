import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Warm, minimal palette - preserved
        background: '#FAFAF9',
        surface: '#F5F5F4',
        'surface-elevated': '#FFFFFF',
        border: '#E7E5E4',
        'border-subtle': '#F0EEEC',
        
        // Text colors
        foreground: '#1C1917',
        'text-secondary': '#78716C',
        'text-muted': '#A8A29E',
        
        // Sentiment colors - soft, not harsh
        positive: '#6B8E6B',
        neutral: '#B8A898',
        negative: '#C4837A',
        
        // Accent
        accent: '#525252',
        
        // Source colors
        'source-reddit': '#FF4500',
        'source-hn': '#FF6600',
        'source-mastodon': '#6364FF',
        'source-rss': '#6B8E6B',
      },
      fontFamily: {
        sans: [
          'var(--font-inter)',
          'Inter',
          '-apple-system',
          'BlinkMacSystemFont',
          'Segoe UI',
          'Roboto',
          'sans-serif',
        ],
        mono: [
          'var(--font-mono)',
          'DM Mono',
          'SF Mono',
          'Consolas',
          'monospace',
        ],
      },
      fontSize: {
        '2xs': ['0.625rem', { lineHeight: '0.875rem', letterSpacing: '0.02em' }],
        'xs': ['0.75rem', { lineHeight: '1rem', letterSpacing: '0.01em' }],
        'sm': ['0.8125rem', { lineHeight: '1.25rem', letterSpacing: '0' }],
        'base': ['0.9375rem', { lineHeight: '1.5rem', letterSpacing: '-0.01em' }],
        'lg': ['1.0625rem', { lineHeight: '1.625rem', letterSpacing: '-0.01em' }],
        'xl': ['1.1875rem', { lineHeight: '1.75rem', letterSpacing: '-0.015em' }],
        '2xl': ['1.375rem', { lineHeight: '1.875rem', letterSpacing: '-0.02em' }],
        '3xl': ['1.75rem', { lineHeight: '2.125rem', letterSpacing: '-0.02em' }],
        '4xl': ['2.125rem', { lineHeight: '2.5rem', letterSpacing: '-0.025em' }],
      },
      letterSpacing: {
        'tighter': '-0.03em',
        'tight': '-0.02em',
        'normal': '-0.01em',
        'wide': '0.01em',
        'wider': '0.05em',
        'widest': '0.1em',
      },
      borderRadius: {
        DEFAULT: '6px',
        'sm': '4px',
        'md': '8px',
        'lg': '10px',
        'xl': '12px',
        '2xl': '16px',
      },
      boxShadow: {
        'xs': '0 1px 2px rgba(28, 25, 23, 0.03)',
        'soft': '0 1px 3px rgba(28, 25, 23, 0.04), 0 1px 2px rgba(28, 25, 23, 0.02)',
        'medium': '0 4px 12px rgba(28, 25, 23, 0.05), 0 2px 4px rgba(28, 25, 23, 0.03)',
        'lg': '0 10px 40px rgba(28, 25, 23, 0.08), 0 4px 12px rgba(28, 25, 23, 0.04)',
        'inner-soft': 'inset 0 1px 2px rgba(28, 25, 23, 0.04)',
        'glow-positive': '0 0 20px rgba(107, 142, 107, 0.12)',
        'glow-negative': '0 0 20px rgba(196, 131, 122, 0.12)',
        'glow-neutral': '0 0 20px rgba(184, 168, 152, 0.12)',
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-out',
        'fade-in-up': 'fadeInUp 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
        'slide-up': 'slideUp 0.3s ease-out',
        'slide-in-right': 'slideInRight 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        'scale-in': 'scaleIn 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
        'spin-slow': 'spin 20s linear infinite',
        'pulse-soft': 'pulseSoft 2s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        fadeInUp: {
          '0%': { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideInRight: {
          '0%': { opacity: '0', transform: 'translateX(16px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        scaleIn: {
          '0%': { opacity: '0', transform: 'scale(0.96)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
        pulseSoft: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.6' },
        },
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
        '128': '32rem',
      },
      transitionTimingFunction: {
        'smooth': 'cubic-bezier(0.4, 0, 0.2, 1)',
      },
    },
  },
  plugins: [],
}

export default config
