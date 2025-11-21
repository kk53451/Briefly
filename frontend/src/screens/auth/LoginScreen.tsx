import React, { useState } from 'react';
import {
  View,
  StyleSheet,
  Image,
  Dimensions as RNDimensions,
  Alert,
} from 'react-native';
import { Text, Button, useTheme } from 'react-native-paper';
import { SafeAreaView } from 'react-native-safe-area-context';
import * as WebBrowser from 'expo-web-browser';
import * as AuthSession from 'expo-auth-session';
import { AuthStackScreenProps } from '../../navigation/types';
import { API_CONFIG } from '../../lib/api/config';
import { Typography, Spacing, BorderRadius } from '../../lib/theme';

// Enable web browser completion for auth session
WebBrowser.maybeCompleteAuthSession();

const { width: screenWidth } = RNDimensions.get('window');

export default function LoginScreen({ navigation }: AuthStackScreenProps<'Login'>) {
  const theme = useTheme();
  const [isLoading, setIsLoading] = useState(false);

  const redirectUri = AuthSession.makeRedirectUri({
    scheme: 'briefly',
    path: 'auth/callback',
  });

  const handleKakaoLogin = async () => {
    try {
      setIsLoading(true);

      // Build Kakao OAuth URL
      const authUrl = `${API_CONFIG.BASE_URL}/api/auth/kakao/login?redirect_uri=${encodeURIComponent(
        redirectUri
      )}`;

      // Open in-app browser for Kakao OAuth
      const result = await WebBrowser.openAuthSessionAsync(authUrl, redirectUri);

      if (result.type === 'success' && result.url) {
        // Extract code from redirect URL
        const url = new URL(result.url);
        const code = url.searchParams.get('code');

        if (code) {
          // Navigate to callback screen with code
          navigation.navigate('KakaoCallback', { code });
        } else {
          Alert.alert('로그인 실패', '인증 코드를 받지 못했습니다.');
        }
      } else if (result.type === 'cancel') {
        // User cancelled the auth session
        console.log('Auth session cancelled');
      }
    } catch (error) {
      console.error('Kakao login error:', error);
      Alert.alert('로그인 오류', '카카오 로그인 중 오류가 발생했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <View style={styles.content}>
        {/* Logo Section */}
        <View style={styles.logoSection}>
          <View style={[styles.logoPlaceholder, { backgroundColor: theme.colors.primary }]}>
            <Text style={[styles.logoText, { color: '#FFFFFF' }]}>B</Text>
          </View>
          <Text style={[styles.appName, { color: theme.colors.textPrimary }]}>
            Briefly
          </Text>
          <Text style={[styles.tagline, { color: theme.colors.textSecondary }]}>
            Your Personal News Curator
          </Text>
        </View>

        {/* Description Section */}
        <View style={styles.descriptionSection}>
          <Text style={[styles.description, { color: theme.colors.textSecondary }]}>
            AI가 큐레이팅한 프리미엄 오디오 뉴스를{'\n'}
            매일 아침 만나보세요
          </Text>
        </View>

        {/* Login Button Section */}
        <View style={styles.buttonSection}>
          <Button
            mode="contained"
            onPress={handleKakaoLogin}
            loading={isLoading}
            disabled={isLoading}
            style={[styles.kakaoButton, { backgroundColor: '#FEE500' }]}
            labelStyle={[styles.kakaoButtonLabel, { color: '#000000' }]}
            contentStyle={styles.buttonContent}
            icon={() => (
              <Image
                source={{ uri: 'https://developers.kakao.com/assets/img/about/logos/kakaolink/kakaolink_btn_small.png' }}
                style={styles.kakaoIcon}
              />
            )}
          >
            카카오로 시작하기
          </Button>

          <Text style={[styles.termsText, { color: theme.colors.textTertiary }]}>
            로그인 시 서비스 이용약관과{'\n'}
            개인정보 처리방침에 동의하게 됩니다
          </Text>
        </View>
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
    paddingHorizontal: Spacing.xl,
    justifyContent: 'space-between',
    paddingVertical: Spacing['2xl'],
  },
  logoSection: {
    alignItems: 'center',
    marginTop: screenWidth * 0.15,
  },
  logoPlaceholder: {
    width: 100,
    height: 100,
    borderRadius: BorderRadius.pill,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: Spacing.lg,
  },
  logoText: {
    fontSize: 48,
    fontFamily: 'Outfit-Bold',
    fontWeight: '800',
  },
  appName: {
    ...Typography.h1,
    marginBottom: Spacing.sm,
  },
  tagline: {
    ...Typography.body,
    textAlign: 'center',
  },
  descriptionSection: {
    alignItems: 'center',
  },
  description: {
    ...Typography.body,
    textAlign: 'center',
    lineHeight: 24,
  },
  buttonSection: {
    alignItems: 'center',
  },
  kakaoButton: {
    width: '100%',
    borderRadius: BorderRadius.button,
    marginBottom: Spacing.md,
  },
  kakaoButtonLabel: {
    ...Typography.button,
    fontSize: 16,
    marginLeft: Spacing.sm,
  },
  buttonContent: {
    height: 52,
  },
  kakaoIcon: {
    width: 24,
    height: 24,
  },
  termsText: {
    ...Typography.caption,
    textAlign: 'center',
    lineHeight: 18,
  },
});