import { Platform } from 'react-native';

export const FontFamilies = {
  // English fonts (premium)
  heading: 'Outfit-Bold', // or 'Outfit-ExtraBold'
  body: 'PlusJakartaSans-Regular',
  bodyMedium: 'PlusJakartaSans-Medium',
  bodySemiBold: 'PlusJakartaSans-SemiBold',
  mono: 'JetBrainsMono-Regular',

  // Korean fonts (Pretendard - premium)
  koreanHeading: 'Pretendard-Bold',
  koreanBody: 'Pretendard-Regular',
  koreanMedium: 'Pretendard-Medium',

  // System fallbacks (if custom fonts fail to load)
  systemFallback: Platform.select({
    ios: 'System',
    android: 'Roboto',
    default: 'System',
  }),
};

// Typography scale (1.25 ratio)
export const FontSizes = {
  xs: 11, // metadata
  sm: 13, // captions, time
  base: 16, // body text
  lg: 20, // subheadings
  xl: 25, // card titles
  '2xl': 31, // section headers
  '3xl': 39, // main headlines
};

// Line heights
export const LineHeights = {
  xs: 14,
  sm: 16,
  base: 22,
  lg: 26,
  xl: 32,
  '2xl': 38,
  '3xl': 46,
};

// Letter spacing
export const LetterSpacing = {
  tight: -0.5,
  normal: 0,
  wide: 0.5,
  wider: 1,
};

// Font weights
export const FontWeights = {
  thin: '100' as const,
  light: '300' as const,
  normal: '400' as const,
  medium: '500' as const,
  semibold: '600' as const,
  bold: '700' as const,
  extrabold: '800' as const,
  black: '900' as const,
};

// Typography presets
export const Typography = {
  // Headlines
  h1: {
    fontFamily: FontFamilies.heading,
    fontSize: FontSizes['3xl'],
    lineHeight: LineHeights['3xl'],
    fontWeight: FontWeights.extrabold,
    letterSpacing: LetterSpacing.tight,
  },
  h2: {
    fontFamily: FontFamilies.heading,
    fontSize: FontSizes['2xl'],
    lineHeight: LineHeights['2xl'],
    fontWeight: FontWeights.bold,
    letterSpacing: LetterSpacing.tight,
  },
  h3: {
    fontFamily: FontFamilies.heading,
    fontSize: FontSizes.xl,
    lineHeight: LineHeights.xl,
    fontWeight: FontWeights.bold,
    letterSpacing: LetterSpacing.normal,
  },

  // Body text
  body: {
    fontFamily: FontFamilies.body,
    fontSize: FontSizes.base,
    lineHeight: LineHeights.base,
    fontWeight: FontWeights.normal,
  },
  bodyMedium: {
    fontFamily: FontFamilies.bodyMedium,
    fontSize: FontSizes.base,
    lineHeight: LineHeights.base,
    fontWeight: FontWeights.medium,
  },
  bodySemiBold: {
    fontFamily: FontFamilies.bodySemiBold,
    fontSize: FontSizes.base,
    lineHeight: LineHeights.base,
    fontWeight: FontWeights.semibold,
  },

  // Small text
  caption: {
    fontFamily: FontFamilies.body,
    fontSize: FontSizes.sm,
    lineHeight: LineHeights.sm,
    fontWeight: FontWeights.normal,
  },
  metadata: {
    fontFamily: FontFamilies.mono,
    fontSize: FontSizes.xs,
    lineHeight: LineHeights.xs,
    fontWeight: FontWeights.normal,
    letterSpacing: LetterSpacing.wide,
  },

  // Special
  time: {
    fontFamily: FontFamilies.mono,
    fontSize: FontSizes.sm,
    lineHeight: LineHeights.sm,
    fontWeight: FontWeights.medium,
  },
  button: {
    fontFamily: FontFamilies.bodySemiBold,
    fontSize: FontSizes.base,
    fontWeight: FontWeights.semibold,
    letterSpacing: LetterSpacing.wide,
  },
};