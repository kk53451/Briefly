/**
 * Theme constants for Briefly mobile app
 * Primary color based on logo blue: #3B82F6
 */

export const Colors = {
  light: {
    primary: '#3B82F6',      // Logo blue
    primaryDark: '#2563EB',  // Darker blue for pressed states
    primaryLight: '#60A5FA', // Lighter blue for accents
    background: '#FFFFFF',
    backgroundSecondary: '#F8FAFC',
    surface: '#FFFFFF',
    text: '#0F172A',
    textSecondary: '#64748B',
    textTertiary: '#94A3B8',
    border: '#E2E8F0',
    error: '#EF4444',
    success: '#10B981',
    warning: '#F59E0B',
    card: '#FFFFFF',
    shadow: '#000000',
    placeholder: '#CBD5E1',
  },
  dark: {
    primary: '#60A5FA',      // Lighter blue for dark mode
    primaryDark: '#3B82F6',
    primaryLight: '#93C5FD',
    background: '#0F172A',
    backgroundSecondary: '#1E293B',
    surface: '#1E293B',
    text: '#F8FAFC',
    textSecondary: '#CBD5E1',
    textTertiary: '#94A3B8',
    border: '#334155',
    error: '#F87171',
    success: '#34D399',
    warning: '#FBBF24',
    card: '#1E293B',
    shadow: '#000000',
    placeholder: '#475569',
  },
};

export const Spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
};

export const BorderRadius = {
  sm: 4,
  md: 8,
  lg: 12,
  xl: 16,
  full: 9999,
};

export const Typography = {
  fontSize: {
    xs: 12,
    sm: 14,
    base: 16,
    lg: 18,
    xl: 20,
    xxl: 24,
    xxxl: 32,
  },
  fontWeight: {
    regular: '400' as const,
    medium: '500' as const,
    semibold: '600' as const,
    bold: '700' as const,
  },
  lineHeight: {
    tight: 1.25,
    normal: 1.5,
    relaxed: 1.75,
  },
};

export const Shadows = {
  sm: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  md: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  lg: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 8,
    elevation: 5,
  },
};
