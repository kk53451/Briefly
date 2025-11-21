import React, { useEffect } from 'react';
import { View, StyleSheet } from 'react-native';
import { Text, ActivityIndicator, useTheme } from 'react-native-paper';
import { SafeAreaView } from 'react-native-safe-area-context';
import { AuthStackScreenProps } from '../../navigation/types';
import { authService } from '../../lib/api/services';
import { useAuthStore } from '../../store/authStore';
import { Spacing } from '../../lib/theme';

export default function KakaoCallbackScreen({ route, navigation }: AuthStackScreenProps<'KakaoCallback'>) {
  const theme = useTheme();
  const { login } = useAuthStore();
  const { code } = route.params;

  useEffect(() => {
    handleCallback();
  }, [code]);

  const handleCallback = async () => {
    try {
      // Exchange code for JWT token
      const authResponse = await authService.kakaoCallback(code);

      // Store auth data in zustand store
      await login(authResponse);

      // Navigate based on onboarding status
      if (!authResponse.onboarding_completed) {
        navigation.replace('Onboarding');
      }
      // If onboarding is complete, RootNavigator will automatically show Main
    } catch (error) {
      console.error('Kakao callback error:', error);
      // Navigate back to login with error
      navigation.replace('Login');
    }
  };

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <View style={styles.content}>
        <ActivityIndicator size="large" color={theme.colors.primary} />
        <Text style={[styles.text, { color: theme.colors.textSecondary }]}>
          로그인 중입니다...
        </Text>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  text: {
    marginTop: Spacing.md,
    fontSize: 16,
    fontFamily: 'PlusJakartaSans-Medium',
  },
});