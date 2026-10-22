import { useEffect } from 'react';
import { Slot } from 'expo-router';
import { View } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import * as SplashScreen from 'expo-splash-screen';
import {
  useFonts,
  NotoSerifKR_400Regular,
  NotoSerifKR_500Medium,
  NotoSerifKR_700Bold,
  NotoSerifKR_900Black,
} from '@expo-google-fonts/noto-serif-kr';
import {
  JetBrainsMono_400Regular,
  JetBrainsMono_500Medium,
  JetBrainsMono_700Bold,
} from '@expo-google-fonts/jetbrains-mono';
import { colors } from '@/theme/tokens';

SplashScreen.preventAutoHideAsync().catch(() => {});

export default function RootLayout() {
  const [fontsLoaded, fontError] = useFonts({
    NotoSerifKR_400Regular,
    NotoSerifKR_500Medium,
    NotoSerifKR_700Bold,
    NotoSerifKR_900Black,
    JetBrainsMono_400Regular,
    JetBrainsMono_500Medium,
    JetBrainsMono_700Bold,
  });

  useEffect(() => {
    if (fontsLoaded || fontError) {
      SplashScreen.hideAsync().catch(() => {});
    }
  }, [fontsLoaded, fontError]);

  if (!fontsLoaded && !fontError) return null;

  return (
    <SafeAreaProvider>
      <View style={{ flex: 1, backgroundColor: colors.paper }}>
        <StatusBar style="dark" />
        <Slot />
      </View>
    </SafeAreaProvider>
  );
}
