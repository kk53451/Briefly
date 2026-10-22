/**
 * Briefly design tokens — warm editorial.
 * Source of truth: briefly_design/project/styles/briefly.css
 */

export const colors = {
  // Paper & ink
  paper: '#f7f2e9',
  paper2: '#efe8da',
  card: '#fcfaf4',
  ink: '#1a1714',
  ink2: '#4a423b',
  ink3: '#857a6d',
  ink4: '#b8ad9d',
  line: '#dcd3c1',
  lineSoft: '#e8e0cd',

  // Accent — rust
  accent: '#a03a28',
  accentSoft: '#eadbc9',
  accentInk: '#6b2416',

  // Live indicator / studio dot
  live: '#d97654',
} as const;

export const fontFamily = {
  serif: 'NotoSerifKR_700Bold',
  serifBlack: 'NotoSerifKR_900Black',
  serifMedium: 'NotoSerifKR_500Medium',
  serifRegular: 'NotoSerifKR_400Regular',
  // Pretendard falls back to the platform Korean sans until a local Pretendard asset is added.
  sans: undefined as unknown as string,
  mono: 'JetBrainsMono_400Regular',
  monoMedium: 'JetBrainsMono_500Medium',
  monoBold: 'JetBrainsMono_700Bold',
} as const;

export const fontSize = {
  xxxl: 32,
  xxl: 24,
  xl: 20,
  lg: 18,
  base: 16,
  sm: 14,
  xs: 12,
  xxs: 10,
} as const;

export const spacing = {
  xxs: 2,
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
} as const;

export const radius = {
  none: 0,
  sm: 2,
  md: 4,
  lg: 8,
  xl: 12,
  full: 9999,
} as const;

export const shadow = {
  card: {
    shadowColor: '#281e14',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.06,
    shadowRadius: 20,
    elevation: 3,
  },
  albumArt: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 20 },
    shadowOpacity: 0.15,
    shadowRadius: 40,
    elevation: 8,
  },
} as const;
