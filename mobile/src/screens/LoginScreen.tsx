/**
 * Login Screen with Kakao OAuth
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Image,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { login as kakaoLogin } from '@react-native-kakao/user';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import { Spacing, Typography, BorderRadius } from '../constants/theme';

export const LoginScreen: React.FC = () => {
  const { colors, activeTheme } = useTheme();
  const { loginWithKakao } = useAuth();
  const [isLoading, setIsLoading] = useState(false);

  const handleKakaoLogin = async () => {
    try {
      setIsLoading(true);

      // Use Kakao Native SDK
      console.log('🔐 카카오 로그인 시작...');
      const result = await kakaoLogin();
      console.log('✅ 카카오 SDK 로그인 성공:', result);

      if (!result.accessToken) {
        throw new Error('카카오 액세스 토큰을 받지 못했습니다.');
      }

      // Login with backend using Kakao access token
      console.log('🔄 백엔드 로그인 요청 중...');
      await loginWithKakao(result.accessToken);
      console.log('✅ 백엔드 로그인 성공!');

    } catch (error: any) {
      console.error('❌ 카카오 로그인 실패:', error);

      // 에러 타입에 따른 상세한 메시지 제공
      let errorMessage = '카카오 로그인에 실패했습니다. 다시 시도해주세요.';

      if (error.code === 'E_CANCELLED_OPERATION') {
        // 사용자가 로그인 취소
        errorMessage = '로그인을 취소하셨습니다.';
      } else if (error.message?.includes('network') || error.message?.includes('Network')) {
        // 네트워크 오류
        errorMessage = '네트워크 연결을 확인해주세요.';
      } else if (error.message?.includes('token') || error.message?.includes('Token')) {
        // 토큰 관련 오류
        errorMessage = '인증에 실패했습니다. 다시 시도해주세요.';
      } else if (error.response?.status === 400) {
        // 서버에서 반환한 오류
        errorMessage = error.response?.data?.detail || '로그인 처리 중 오류가 발생했습니다.';
      } else if (error.response?.status === 500) {
        // 서버 오류
        errorMessage = '서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.';
      } else if (error.message) {
        // 기타 에러 메시지
        errorMessage = error.message;
      }

      Alert.alert(
        '로그인 실패',
        errorMessage
      );
    } finally {
      setIsLoading(false);
    }
  };

  const logoUrl =
    activeTheme === 'dark'
      ? process.env.EXPO_PUBLIC_LOGO_DARK_URL
      : process.env.EXPO_PUBLIC_LOGO_LIGHT_URL;

  return (
    <LinearGradient
      colors={[colors.primary, colors.primaryLight]}
      start={{ x: 0, y: 0 }}
      end={{ x: 0, y: 1 }}
      style={styles.container}
    >
      <View style={styles.content}>
        {/* Logo */}
        <View style={styles.logoContainer}>
          <Image source={{ uri: logoUrl }} style={styles.logo} resizeMode="contain" />
        </View>

        {/* Tagline */}
        <Text style={styles.tagline}>AI가 전하는 오늘의 뉴스</Text>
        <Text style={styles.subtitle}>팟캐스트로 듣는 맞춤형 뉴스 브리핑</Text>

        {/* Login Button */}
        <TouchableOpacity
          style={[styles.loginButton, isLoading && styles.loginButtonDisabled]}
          onPress={handleKakaoLogin}
          disabled={isLoading}
        >
          {isLoading ? (
            <ActivityIndicator color="#3C1E1E" />
          ) : (
            <>
              <View style={styles.kakaoLogo} />
              <Text style={styles.loginButtonText}>카카오로 시작하기</Text>
            </>
          )}
        </TouchableOpacity>

        {/* Footer */}
        <Text style={styles.footer}>
          간편하게 로그인하고{'\n'}나만의 뉴스 큐레이션을 시작하세요
        </Text>
      </View>
    </LinearGradient>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: Spacing.xl,
  },
  logoContainer: {
    marginBottom: Spacing.xxl,
  },
  logo: {
    width: 200,
    height: 60,
  },
  tagline: {
    fontSize: Typography.fontSize.xxl,
    fontWeight: Typography.fontWeight.bold,
    color: '#FFFFFF',
    textAlign: 'center',
    marginBottom: Spacing.sm,
  },
  subtitle: {
    fontSize: Typography.fontSize.base,
    color: 'rgba(255,255,255,0.9)',
    textAlign: 'center',
    marginBottom: Spacing.xxl * 2,
  },
  loginButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#FEE500', // Kakao yellow
    paddingVertical: Spacing.md,
    paddingHorizontal: Spacing.xl,
    borderRadius: BorderRadius.lg,
    width: '100%',
    maxWidth: 300,
  },
  loginButtonDisabled: {
    opacity: 0.6,
  },
  kakaoLogo: {
    width: 24,
    height: 24,
    marginRight: Spacing.sm,
  },
  loginButtonText: {
    fontSize: Typography.fontSize.lg,
    fontWeight: Typography.fontWeight.semibold,
    color: '#3C1E1E',
  },
  footer: {
    marginTop: Spacing.xxl,
    fontSize: Typography.fontSize.sm,
    color: 'rgba(255,255,255,0.8)',
    textAlign: 'center',
    lineHeight: Typography.fontSize.sm * Typography.lineHeight.relaxed,
  },
});
