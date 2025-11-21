import React, { useEffect, useState } from 'react';
import { StatusBar } from 'expo-status-bar';
import { View, useColorScheme, ActivityIndicator } from 'react-native';
import { PaperProvider } from 'react-native-paper';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import * as Font from 'expo-font';
import { GestureHandlerRootView } from 'react-native-gesture-handler';

import RootNavigator from './src/navigation/RootNavigator';
import { lightTheme, darkTheme } from './src/lib/theme';

// Create a QueryClient instance
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 10 * 60 * 1000, // 10 minutes (formerly cacheTime)
      retry: 3,
      refetchOnWindowFocus: false,
      refetchOnReconnect: 'always',
    },
  },
});

// Font assets - all premium fonts loaded
const availableFonts: any = {
  // English fonts
  'Outfit-Bold': require('./assets/fonts/Outfit-Bold.ttf'),
  'Outfit-ExtraBold': require('./assets/fonts/Outfit-ExtraBold.ttf'),
  'PlusJakartaSans-Regular': require('./assets/fonts/PlusJakartaSans-Regular.ttf'),
  'PlusJakartaSans-Medium': require('./assets/fonts/PlusJakartaSans-Medium.ttf'),
  'PlusJakartaSans-SemiBold': require('./assets/fonts/PlusJakartaSans-SemiBold.ttf'),
  'JetBrainsMono-Regular': require('./assets/fonts/JetBrainsMono-Regular.ttf'),

  // Korean fonts (Pretendard)
  'Pretendard-Regular': require('./assets/fonts/Pretendard-Regular.ttf'),
  'Pretendard-Medium': require('./assets/fonts/Pretendard-Medium.ttf'),
  'Pretendard-Bold': require('./assets/fonts/Pretendard-Bold.ttf'),
};

export default function App() {
  const colorScheme = useColorScheme();
  const [fontsLoaded, setFontsLoaded] = useState(false);
  const theme = colorScheme === 'dark' ? darkTheme : lightTheme;

  useEffect(() => {
    async function loadFonts() {
      try {
        await Font.loadAsync(availableFonts);
        setFontsLoaded(true);
      } catch (error) {
        console.error('Error loading fonts:', error);
        // Even if fonts fail to load, continue with system fonts
        setFontsLoaded(true);
      }
    }
    loadFonts();
  }, []);

  if (!fontsLoaded) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
        <ActivityIndicator size="large" />
      </View>
    );
  }

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <QueryClientProvider client={queryClient}>
        <PaperProvider theme={theme}>
          <StatusBar style={colorScheme === 'dark' ? 'light' : 'dark'} />
          <RootNavigator />
        </PaperProvider>
      </QueryClientProvider>
    </GestureHandlerRootView>
  );
}
