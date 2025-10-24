import React, { useState, useEffect } from "react";
import { View, Text, StyleSheet, Image, Alert } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import * as WebBrowser from "expo-web-browser";
import * as Linking from "expo-linking";
import { Button } from "../components/Button";
import { useAuth } from "../contexts/AuthContext";
import { apiClient } from "../services/api";
import { Colors, Spacing, FontSizes, FontWeights } from "../constants/theme";

WebBrowser.maybeCompleteAuthSession();

const LoginScreen: React.FC = () => {
  const { login } = useAuth();
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const subscription = Linking.addEventListener("url", handleDeepLink);

    return () => {
      subscription.remove();
    };
  }, []);

  const handleDeepLink = async ({ url }: { url: string }) => {
    const parsed = Linking.parse(url);
    const code = parsed.queryParams?.code as string;

    if (code) {
      try {
        setLoading(true);
        const response = await apiClient.handleKakaoCallback(code);
        await login(response.access_token);
      } catch (error) {
        Alert.alert("로그인 실패", "카카오 로그인에 실패했습니다. 다시 시도해주세요.");
        console.error("Login failed:", error);
      } finally {
        setLoading(false);
      }
    }
  };

  const handleKakaoLogin = async () => {
    try {
      setLoading(true);
      const loginUrl = await apiClient.getKakaoLoginUrl();

      const result = await WebBrowser.openAuthSessionAsync(
        loginUrl,
        Linking.createURL("/")
      );

      if (result.type === "success" && result.url) {
        await handleDeepLink({ url: result.url });
      }
    } catch (error) {
      Alert.alert("오류", "로그인 중 문제가 발생했습니다.");
      console.error("Kakao login error:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        <View style={styles.header}>
          <Text style={styles.logo}>📻</Text>
          <Text style={styles.title}>Briefly</Text>
          <Text style={styles.subtitle}>매일 업데이트되는{"\n"}개인화 AI 뉴스 팟캐스트</Text>
        </View>

        <View style={styles.features}>
          <FeatureItem icon="🎯" text="관심 카테고리 맞춤 뉴스" />
          <FeatureItem icon="🎙️" text="AI 음성으로 듣는 팟캐스트" />
          <FeatureItem icon="⏱️" text="바쁜 일상 속 효율적인 정보 습득" />
        </View>

        <View style={styles.buttonContainer}>
          <Button
            title="카카오로 시작하기"
            onPress={handleKakaoLogin}
            loading={loading}
            fullWidth
            style={styles.kakaoButton}
          />
        </View>
      </View>
    </SafeAreaView>
  );
};

const FeatureItem: React.FC<{ icon: string; text: string }> = ({ icon, text }) => (
  <View style={styles.featureItem}>
    <Text style={styles.featureIcon}>{icon}</Text>
    <Text style={styles.featureText}>{text}</Text>
  </View>
);

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  content: {
    flex: 1,
    paddingHorizontal: Spacing.xl,
    justifyContent: "space-between",
    paddingTop: Spacing.xxl,
    paddingBottom: Spacing.xl,
  },
  header: {
    alignItems: "center",
    marginTop: Spacing.xxl,
  },
  logo: {
    fontSize: 80,
    marginBottom: Spacing.md,
  },
  title: {
    fontSize: FontSizes.xxxl,
    fontWeight: FontWeights.bold,
    color: Colors.primary,
    marginBottom: Spacing.sm,
  },
  subtitle: {
    fontSize: FontSizes.md,
    color: Colors.textSecondary,
    textAlign: "center",
    lineHeight: 24,
  },
  features: {
    gap: Spacing.lg,
  },
  featureItem: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: Colors.backgroundLight,
    padding: Spacing.md,
    borderRadius: 12,
  },
  featureIcon: {
    fontSize: 24,
    marginRight: Spacing.md,
  },
  featureText: {
    fontSize: FontSizes.md,
    color: Colors.text,
    flex: 1,
  },
  buttonContainer: {
    gap: Spacing.md,
  },
  kakaoButton: {
    backgroundColor: "#FEE500",
  },
});

export default LoginScreen;
