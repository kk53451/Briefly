import { MD3LightTheme, MD3DarkTheme, configureFonts } from 'react-native-paper';
import { Colors, CategoryColors } from './colors';
import { Typography, FontFamilies, FontSizes, FontWeights } from './typography';
import { Spacing, Padding, Margin, BorderRadius, Shadows, Dimensions } from './spacing';

// Font configuration for React Native Paper
const fontConfig = {
  default: {
    regular: {
      fontFamily: FontFamilies.body,
      fontWeight: '400' as const,
    },
    medium: {
      fontFamily: FontFamilies.bodyMedium,
      fontWeight: '500' as const,
    },
    light: {
      fontFamily: FontFamilies.body,
      fontWeight: '300' as const,
    },
    thin: {
      fontFamily: FontFamilies.body,
      fontWeight: '100' as const,
    },
  },
};

// Light theme
export const lightTheme = {
  ...MD3LightTheme,
  fonts: configureFonts({ config: fontConfig }),
  colors: {
    ...MD3LightTheme.colors,
    primary: Colors.light.primary,
    primaryContainer: Colors.light.secondary,
    secondary: Colors.light.primaryAccent,
    background: Colors.light.background,
    surface: Colors.light.surface,
    surfaceVariant: Colors.light.elevated,
    onPrimary: '#FFFFFF',
    onBackground: Colors.light.textPrimary,
    onSurface: Colors.light.textSecondary,
    outline: Colors.light.border,
    error: '#EF4444',
    // Custom colors
    textPrimary: Colors.light.textPrimary,
    textSecondary: Colors.light.textSecondary,
    textTertiary: Colors.light.textTertiary,
    playing: Colors.light.playing,
    live: Colors.light.live,
  },
};

// Dark theme
export const darkTheme = {
  ...MD3DarkTheme,
  fonts: configureFonts({ config: fontConfig }),
  colors: {
    ...MD3DarkTheme.colors,
    primary: Colors.dark.primary,
    primaryContainer: Colors.dark.secondary,
    secondary: Colors.dark.primaryAccent,
    background: Colors.dark.background,
    surface: Colors.dark.surface,
    surfaceVariant: Colors.dark.elevated,
    onPrimary: '#FFFFFF',
    onBackground: Colors.dark.textPrimary,
    onSurface: Colors.dark.textSecondary,
    outline: Colors.dark.border,
    error: '#EF4444',
    // Custom colors
    textPrimary: Colors.dark.textPrimary,
    textSecondary: Colors.dark.textSecondary,
    textTertiary: Colors.dark.textTertiary,
    playing: Colors.dark.playing,
    live: Colors.dark.live,
  },
};

// Export all theme components
export {
  Colors,
  CategoryColors,
  Typography,
  FontFamilies,
  FontSizes,
  FontWeights,
  Spacing,
  Padding,
  Margin,
  BorderRadius,
  Shadows,
  Dimensions,
};

// Theme type for TypeScript
export type AppTheme = typeof lightTheme;

// Extend the react-native-paper theme type
declare global {
  namespace ReactNativePaper {
    interface ThemeColors {
      textPrimary: string;
      textSecondary: string;
      textTertiary: string;
      playing: string;
      live: string;
    }
  }
}