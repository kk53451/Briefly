// 8px base grid system
export const Spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  '2xl': 48,
  '3xl': 64,
};

// Common paddings
export const Padding = {
  card: Spacing.md,
  screen: Spacing.md,
  button: {
    vertical: 12,
    horizontal: Spacing.lg,
  },
};

// Common margins
export const Margin = {
  section: Spacing.lg,
  paragraph: Spacing.md,
  item: Spacing.sm,
};

// Border radius hierarchy
export const BorderRadius = {
  button: 8,
  card: 12,
  pill: 20,
  modalTop: 24,
  full: 9999,
};

// Shadow configurations
export const Shadows = {
  light: {
    small: {
      shadowColor: '#000',
      shadowOffset: {
        width: 0,
        height: 1,
      },
      shadowOpacity: 0.06,
      shadowRadius: 2,
      elevation: 2,
    },
    medium: {
      shadowColor: '#000',
      shadowOffset: {
        width: 0,
        height: 2,
      },
      shadowOpacity: 0.08,
      shadowRadius: 4,
      elevation: 4,
    },
    large: {
      shadowColor: '#000',
      shadowOffset: {
        width: 0,
        height: 4,
      },
      shadowOpacity: 0.1,
      shadowRadius: 8,
      elevation: 6,
    },
  },
  dark: {
    // Dark mode uses borders instead of shadows
    small: {
      borderWidth: 1,
      borderColor: '#334155',
    },
    medium: {
      borderWidth: 1,
      borderColor: '#334155',
    },
    large: {
      borderWidth: 1,
      borderColor: '#334155',
    },
  },
};

// Common dimensions
export const Dimensions = {
  // Touch targets (minimum 48px for accessibility)
  touchTarget: 48,

  // Component heights
  miniPlayer: 64,
  tabBar: 56,
  header: 56,

  // Card heights
  cardCompact: 120,
  cardStandard: 180,
  cardExpanded: 260,

  // Button sizes
  buttonSmall: 32,
  buttonMedium: 40,
  buttonLarge: 48,

  // Icon sizes
  iconSmall: 16,
  iconMedium: 24,
  iconLarge: 32,
  iconXLarge: 48,

  // Player controls
  playButtonLarge: 80,
  playButtonMedium: 56,
  playButtonSmall: 40,
};