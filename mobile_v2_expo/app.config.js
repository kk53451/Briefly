/**
 * Expo App Configuration — Briefly v3 (Expo Router + Supabase)
 * Secrets (Supabase URL / anon key) are read from EXPO_PUBLIC_* env at runtime.
 */

export default {
  expo: {
    name: "Briefly",
    slug: "briefly",
    version: "2.0.0",
    orientation: "portrait",
    icon: "./assets/icon.png",
    userInterfaceStyle: "light",
    scheme: "briefly",
    newArchEnabled: true,
    splash: {
      image: "./assets/splash-icon.png",
      resizeMode: "contain",
      backgroundColor: "#f7f2e9"
    },
    ios: {
      supportsTablet: true,
      bundleIdentifier: "com.briefly.app",
      infoPlist: {
        UIBackgroundModes: ["audio"]
      }
    },
    android: {
      adaptiveIcon: {
        foregroundImage: "./assets/adaptive-icon.png",
        backgroundColor: "#f7f2e9"
      },
      package: "com.briefly.app",
      permissions: ["FOREGROUND_SERVICE", "WAKE_LOCK"],
      edgeToEdgeEnabled: true,
      predictiveBackGestureEnabled: false
    },
    web: {
      bundler: "metro",
      favicon: "./assets/favicon.png"
    },
    plugins: [
      "expo-router",
      "expo-font",
      [
        "expo-av",
        { microphonePermission: false }
      ],
      "expo-web-browser"
    ],
    experiments: {
      typedRoutes: true
    },
    extra: {
      eas: {
        projectId: "your-project-id-here"
      }
    }
  }
};
