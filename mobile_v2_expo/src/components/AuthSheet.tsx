import { useEffect, useRef, useState } from 'react';
import {
  Modal,
  View,
  Text,
  Pressable,
  Animated,
  Easing,
  ActivityIndicator,
  Alert,
  StyleSheet,
} from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import { colors, fontFamily, radius, spacing } from '@/theme/tokens';
import { signInWithProvider, type OAuthProvider } from '@/lib/auth';

interface Props {
  visible: boolean;
  onClose: () => void;
  onAuthenticated: () => void;
}

const BRAND: Record<OAuthProvider, {
  label: string;
  bg: string;
  fg: string;
  border: string;
  icon: keyof typeof Ionicons.glyphMap;
  iconColor: string;
  note?: string;
}> = {
  kakao: {
    label: '카카오로 시작하기',
    bg: '#FEE500',
    fg: '#1a1a1a',
    border: 'transparent',
    icon: 'chatbubble',
    iconColor: '#1a1a1a',
    note: '가장 빠름',
  },
  google: {
    label: 'Google로 시작하기',
    bg: '#FFFFFF',
    fg: '#1f1f1f',
    border: '#dadce0',
    icon: 'logo-google',
    iconColor: '#1f1f1f',
  },
};

export function AuthSheet({ visible, onClose, onAuthenticated }: Props) {
  const translate = useRef(new Animated.Value(1)).current;
  const [busy, setBusy] = useState<OAuthProvider | null>(null);

  useEffect(() => {
    Animated.timing(translate, {
      toValue: visible ? 0 : 1,
      duration: 260,
      easing: Easing.out(Easing.cubic),
      useNativeDriver: true,
    }).start();
  }, [visible, translate]);

  const sheetTranslateY = translate.interpolate({
    inputRange: [0, 1],
    outputRange: [0, 520],
  });
  const scrimOpacity = translate.interpolate({
    inputRange: [0, 1],
    outputRange: [1, 0],
  });

  const handlePress = async (provider: OAuthProvider) => {
    if (busy) return;
    setBusy(provider);
    try {
      const ok = await signInWithProvider(provider);
      if (ok) onAuthenticated();
    } catch (e) {
      Alert.alert('로그인 실패', (e as Error).message);
    } finally {
      setBusy(null);
    }
  };

  return (
    <Modal
      visible={visible}
      transparent
      animationType="none"
      onRequestClose={onClose}
      statusBarTranslucent
    >
      <View style={StyleSheet.absoluteFill}>
        {/* Scrim */}
        <Animated.View
          style={[
            StyleSheet.absoluteFill,
            { backgroundColor: 'rgba(26,23,20,0.35)', opacity: scrimOpacity },
          ]}
        >
          <Pressable style={StyleSheet.absoluteFill} onPress={onClose} />
        </Animated.View>

        {/* Sheet */}
        <Animated.View
          style={{
            position: 'absolute',
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: colors.paper,
            borderTopLeftRadius: 20,
            borderTopRightRadius: 20,
            paddingHorizontal: 28,
            paddingTop: 14,
            paddingBottom: 28 + 24, // home indicator clearance
            borderTopColor: colors.ink,
            borderTopWidth: 3,
            transform: [{ translateY: sheetTranslateY }],
            shadowColor: '#000',
            shadowOpacity: 0.2,
            shadowOffset: { width: 0, height: -20 },
            shadowRadius: 60,
            elevation: 18,
          }}
        >
          {/* Drag handle */}
          <View style={{ alignItems: 'center', marginBottom: 16 }}>
            <View
              style={{
                width: 36,
                height: 4,
                borderRadius: 2,
                backgroundColor: colors.ink3,
                opacity: 0.4,
              }}
            />
          </View>

          {/* Header */}
          <View style={{ alignItems: 'center', marginBottom: 22 }}>
            <Text
              style={{
                fontFamily: fontFamily.monoMedium,
                fontSize: 10,
                color: colors.ink3,
                letterSpacing: 1.4,
                marginBottom: 8,
              }}
            >
              SIGN IN
            </Text>
            <Text
              style={{
                fontFamily: fontFamily.serif,
                fontSize: 26,
                color: colors.ink,
                letterSpacing: -0.5,
                lineHeight: 32,
              }}
            >
              계정으로 시작하기
            </Text>
            <Text
              style={{
                fontFamily: fontFamily.serifRegular,
                fontStyle: 'italic',
                fontSize: 14,
                color: colors.ink2,
                marginTop: 6,
                letterSpacing: -0.2,
              }}
            >
              관심 카테고리가 기기 간 동기화됩니다.
            </Text>
          </View>

          {/* Buttons */}
          <View style={{ gap: 10 }}>
            {(['kakao', 'google'] as OAuthProvider[]).map((p) => (
              <SocialButton
                key={p}
                provider={p}
                busy={busy === p}
                disabled={!!busy && busy !== p}
                onPress={() => handlePress(p)}
              />
            ))}
          </View>

          {/* Legal */}
          <View style={{ marginTop: 22 }}>
            <Text
              style={{
                fontSize: 11,
                color: colors.ink3,
                textAlign: 'center',
                lineHeight: 18,
              }}
            >
              계속하면 <Text style={{ textDecorationLine: 'underline' }}>서비스 이용약관</Text>과{'\n'}
              <Text style={{ textDecorationLine: 'underline' }}>개인정보 처리방침</Text>에 동의하게 됩니다.
            </Text>
          </View>
        </Animated.View>
      </View>
    </Modal>
  );
}

function SocialButton({
  provider,
  busy,
  disabled,
  onPress,
}: {
  provider: OAuthProvider;
  busy: boolean;
  disabled: boolean;
  onPress: () => void;
}) {
  const brand = BRAND[provider];
  return (
    <Pressable
      onPress={onPress}
      disabled={disabled || busy}
      style={({ pressed }) => ({
        height: 52,
        backgroundColor: brand.bg,
        borderColor: brand.border,
        borderWidth: 1,
        borderRadius: radius.md,
        flexDirection: 'row',
        alignItems: 'center',
        paddingHorizontal: spacing.md,
        opacity: disabled ? 0.4 : pressed ? 0.85 : 1,
      })}
    >
      <Ionicons name={brand.icon} size={20} color={brand.iconColor} />
      <View style={{ position: 'absolute', left: 0, right: 0, alignItems: 'center' }}>
        {busy ? (
          <ActivityIndicator color={brand.fg} />
        ) : (
          <Text
            style={{
              fontSize: 15,
              fontWeight: '600',
              color: brand.fg,
              letterSpacing: -0.15,
            }}
          >
            {brand.label}
          </Text>
        )}
      </View>
      {brand.note && (
        <View
          style={{
            position: 'absolute',
            right: 14,
            top: -8,
            backgroundColor: colors.accent,
            paddingHorizontal: 8,
            paddingVertical: 3,
            borderRadius: 2,
          }}
        >
          <Text
            style={{
              fontFamily: fontFamily.monoBold,
              fontSize: 9.5,
              color: colors.paper,
              letterSpacing: 0.6,
            }}
          >
            {brand.note}
          </Text>
        </View>
      )}
    </Pressable>
  );
}
