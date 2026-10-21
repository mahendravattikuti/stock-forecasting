/**
 * Design Tokens for Stock Market Forecasting System
 * Centralized styling constants for consistent design
 */

export const TOKENS = {
  // ==================== COLORS ====================
  colors: {
    // Primary Brand Colors
    primary: {
      50: '#eff6ff',
      100: '#dbeafe',
      200: '#bfdbfe',
      300: '#93c5fd',
      400: '#60a5fa',
      500: '#3b82f6', // Primary blue
      600: '#2563eb',
      700: '#1d4ed8',
      800: '#1e40af',
      900: '#1e3a8a',
    },

    // Success (Green)
    success: {
      50: '#f0fdf4',
      100: '#dcfce7',
      200: '#bbf7d0',
      300: '#86efac',
      400: '#4ade80',
      500: '#22c55e',
      600: '#16a34a',
      700: '#15803d',
      800: '#166534',
      900: '#145231',
    },

    // Warning (Amber/Yellow)
    warning: {
      50: '#fffbeb',
      100: '#fef3c7',
      200: '#fde68a',
      300: '#fcd34d',
      400: '#fbbf24',
      500: '#f59e0b',
      600: '#d97706',
      700: '#b45309',
      800: '#92400e',
      900: '#78350f',
    },

    // Danger (Red)
    danger: {
      50: '#fef2f2',
      100: '#fee2e2',
      200: '#fecaca',
      300: '#fca5a5',
      400: '#f87171',
      500: '#ef4444',
      600: '#dc2626',
      700: '#b91c1c',
      800: '#991b1b',
      900: '#7f1d1d',
    },

    // Neutral (Gray - for UI elements)
    neutral: {
      50: '#f9fafb',
      100: '#f3f4f6',
      200: '#e5e7eb',
      300: '#d1d5db',
      400: '#9ca3af',
      500: '#6b7280',
      600: '#4b5563',
      700: '#374151',
      800: '#1f2937',
      900: '#111827',
    },

    // Dark theme background
    dark: {
      50: '#f9fafb',
      100: '#f3f4f6',
      200: '#e5e7eb',
      300: '#d1d5db',
      400: '#9ca3af',
      500: '#6b7280',
      600: '#4b5563',
      700: '#374151',
      800: '#1f2937',
      900: '#111827',
      950: '#030712', // Very dark for gradients
    },

    // Semantic colors
    text: {
      primary: '#1f2937', // Dark gray for main text
      secondary: '#6b7280', // Medium gray for secondary text
      muted: '#9ca3af', // Light gray for muted text
      light: '#f9fafb', // White-ish for light backgrounds
    },

    // Financial colors
    positive: '#22c55e', // Green for up/buy
    negative: '#ef4444', // Red for down/sell
    neutral: '#f59e0b', // Amber for neutral/hold
  },

  // ==================== TYPOGRAPHY ====================
  typography: {
    // Font families
    fontFamily: {
      sans: [
        '-apple-system',
        'BlinkMacSystemFont',
        'Segoe UI',
        'Roboto',
        'Helvetica Neue',
        'Arial',
        'sans-serif',
      ].join(', '),
      mono: [
        'Menlo',
        'Monaco',
        'Consolas',
        'Liberation Mono',
        'Courier New',
        'monospace',
      ].join(', '),
    },

    // Font sizes
    fontSize: {
      xs: '0.75rem', // 12px
      sm: '0.875rem', // 14px
      base: '1rem', // 16px
      lg: '1.125rem', // 18px
      xl: '1.25rem', // 20px
      '2xl': '1.5rem', // 24px
      '3xl': '1.875rem', // 30px
      '4xl': '2.25rem', // 36px
      '5xl': '3rem', // 48px
    },

    // Font weights
    fontWeight: {
      thin: 100,
      extralight: 200,
      light: 300,
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
      extrabold: 800,
      black: 900,
    },

    // Line heights
    lineHeight: {
      none: 1,
      tight: 1.25,
      snug: 1.375,
      normal: 1.5,
      relaxed: 1.625,
      loose: 2,
    },

    // Letter spacing
    letterSpacing: {
      tighter: '-0.05em',
      tight: '-0.025em',
      normal: '0em',
      wide: '0.025em',
      wider: '0.05em',
      widest: '0.1em',
    },
  },

  // ==================== SPACING ====================
  spacing: {
    0: '0px',
    1: '0.25rem', // 4px
    2: '0.5rem', // 8px
    3: '0.75rem', // 12px
    4: '1rem', // 16px
    5: '1.25rem', // 20px
    6: '1.5rem', // 24px
    8: '2rem', // 32px
    10: '2.5rem', // 40px
    12: '3rem', // 48px
    16: '4rem', // 64px
    20: '5rem', // 80px
    24: '6rem', // 96px
  },

  // ==================== SHADOWS ====================
  shadows: {
    none: 'none',
    xs: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    sm: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
    base: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    md: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
    lg: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
    xl: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
    inner: 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.06)',
  },

  // ==================== BORDER RADIUS ====================
  borderRadius: {
    none: '0px',
    xs: '0.125rem', // 2px
    sm: '0.25rem', // 4px
    base: '0.375rem', // 6px
    md: '0.5rem', // 8px
    lg: '0.75rem', // 12px
    xl: '1rem', // 16px
    '2xl': '1.5rem', // 24px
    '3xl': '2rem', // 32px
    full: '9999px', // Fully rounded
  },

  // ==================== BREAKPOINTS (Responsive) ====================
  breakpoints: {
    xs: '320px',
    sm: '640px',
    md: '768px',
    lg: '1024px',
    xl: '1280px',
    '2xl': '1536px',
  },

  // ==================== TRANSITIONS ====================
  transitions: {
    fast: '150ms cubic-bezier(0.4, 0, 0.2, 1)',
    base: '250ms cubic-bezier(0.4, 0, 0.2, 1)',
    slow: '350ms cubic-bezier(0.4, 0, 0.2, 1)',
    slowest: '500ms cubic-bezier(0.4, 0, 0.2, 1)',
  },

  // ==================== Z-INDEX ====================
  zIndex: {
    hide: -1,
    base: 0,
    dropdown: 1000,
    sticky: 1020,
    fixed: 1030,
    modalBackdrop: 1040,
    modal: 1050,
    popover: 1060,
    tooltip: 1070,
  },

  // ==================== COMPONENT SIZES ====================
  components: {
    button: {
      height: {
        sm: '2rem', // 32px
        md: '2.5rem', // 40px
        lg: '3rem', // 48px
      },
      padding: {
        sm: '0.5rem 1rem',
        md: '0.75rem 1.5rem',
        lg: '1rem 2rem',
      },
    },

    input: {
      height: '2.5rem', // 40px
      borderRadius: '0.5rem',
      fontSize: '1rem',
      padding: '0.75rem 1rem',
    },

    card: {
      borderRadius: '0.75rem',
      padding: '1.5rem',
      backgroundColor: 'white',
    },

    modal: {
      borderRadius: '0.75rem',
      maxWidth: '32rem', // 512px
      padding: '1.5rem',
    },
  },

  // ==================== FINANCIAL COLORS ====================
  financial: {
    buy: '#22c55e', // Green
    sell: '#ef4444', // Red
    hold: '#f59e0b', // Amber
    bullish: '#10b981', // Teal
    bearish: '#f87171', // Light red
    neutral: '#8b5cf6', // Purple
  },
};

// ==================== EXPORT COLOR UTILITIES ====================
export const getFinancialColor = (signal) => {
  switch (signal?.toUpperCase()) {
    case 'BUY':
      return TOKENS.financial.buy;
    case 'SELL':
      return TOKENS.financial.sell;
    case 'HOLD':
      return TOKENS.financial.hold;
    default:
      return TOKENS.colors.neutral[500];
  }
};

export const getStatusColor = (status) => {
  switch (status?.toLowerCase()) {
    case 'success':
    case 'completed':
      return TOKENS.colors.success[500];
    case 'error':
    case 'failed':
      return TOKENS.colors.danger[500];
    case 'warning':
      return TOKENS.colors.warning[500];
    case 'pending':
    case 'in_progress':
      return TOKENS.colors.primary[500];
    default:
      return TOKENS.colors.neutral[500];
  }
};

// ==================== EXPORT RESPONSIVE HELPERS ====================
export const mediaQuery = {
  xs: `@media (min-width: ${TOKENS.breakpoints.xs})`,
  sm: `@media (min-width: ${TOKENS.breakpoints.sm})`,
  md: `@media (min-width: ${TOKENS.breakpoints.md})`,
  lg: `@media (min-width: ${TOKENS.breakpoints.lg})`,
  xl: `@media (min-width: ${TOKENS.breakpoints.xl})`,
  '2xl': `@media (min-width: ${TOKENS.breakpoints['2xl']})`,
};

export default TOKENS;
