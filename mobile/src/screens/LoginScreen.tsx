/**
 * Login Screen (게스트 모드, Kakao 제거)
 *
 * 현재는 실제 로그인 없이 "시작하기" 버튼 → 게스트 로그인.
 * 추후 이메일/Google/Apple 로그인 등으로 교체 예정.
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Image,
  ActivityIndicator,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import { Spacing, Typography, BorderRadius } from '../constants/theme';

export const LoginScreen: React.FC = () => {
  const { colors, activeTheme } = useTheme();
  const { login } = useAuth();
  const [isLoading, setIsLoading] = useState(false);

  const handleGuestStart = async () => {
    try {
      setIsLoading(true);
      await login();
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
        <View style={styles.logoContainer}>
          <Image source={{ uri: logoUrl }} style={styles.logo} resizeMode="contain" />
        </View>

        <Text style={styles.tagline}>AI가 전하는 오늘의 뉴스</Text>
        <Text style={styles.subtitle}>팟캐스트로 듣는 맞춤형 뉴스 브리핑</Text>

        <TouchableOpacity
          style={[styles.loginButton, isLoading && styles.loginButtonDisabled]}
          onPress={handleGuestStart}
          disabled={isLoading}
        >
          {isLoading ? (
            <ActivityIndicator color="#FFFFFF" />
          ) : (
            <Text style={styles.loginButtonText}>시작하기</Text>
          )}
        </TouchableOpacity>

        <Text style={styles.footer}>
          지금은 게스트 모드로 운영 중입니다{'\n'}
          로그인 기능은 추후 추가될 예정입니다
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
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(255,255,255,0.2)',
    paddingVertical: Spacing.md,
    paddingHorizontal: Spacing.xl,
    borderRadius: BorderRadius.lg,
    width: '100%',
    maxWidth: 300,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.4)',
  },
  loginButtonDisabled: {
    opacity: 0.6,
  },
  loginButtonText: {
    fontSize: Typography.fontSize.lg,
    fontWeight: Typography.fontWeight.semibold,
    color: '#FFFFFF',
  },
  footer: {
    marginTop: Spacing.xxl,
    fontSize: Typography.fontSize.sm,
    color: 'rgba(255,255,255,0.8)',
    textAlign: 'center',
    lineHeight: Typography.fontSize.sm * Typography.lineHeight.relaxed,
  },
});
