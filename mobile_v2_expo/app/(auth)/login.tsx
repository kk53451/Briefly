import { useEffect, useRef, useState } from 'react';
import { View, Text, Pressable, Animated, Easing } from 'react-native';
import { router } from 'expo-router';
import Ionicons from '@expo/vector-icons/Ionicons';
import { Screen } from '@/components/Screen';
import { AuthSheet } from '@/components/AuthSheet';
import { useHeadlineTicker } from '@/hooks/useHeadlineTicker';
import { useAuth } from '@/hooks/useAuth';
import { colors, fontFamily, radius, spacing } from '@/theme/tokens';

const SAMPLE_HEADLINES = [
  '지방 경선결과 진행상황',
  '미국-이란 전쟁 상황',
  '동물원 늑대 탈출',
  '다주택자 과세율 변동',
  '유가 상승에 따른 물가',
  '서울시 민원 폭탄',
  'AI 규제 법안 국회 통과',
  '전국 기온 급강하 주의보',
  '코스피 3,200선 안착',
  '반도체 수출 호조',
];

export default function LoginScreen() {
  const ticker = useHeadlineTicker(SAMPLE_HEADLINES);
  const { session } = useAuth();
  const [sheetOpen, setSheetOpen] = useState(false);

  // Persisted session → jump back to the root gate.
  useEffect(() => {
    if (session) router.replace('/');
  }, [session]);

  // Live dot pulse + caret blink
  const dot = useRef(new Animated.Value(1)).current;
  const caret = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(dot, { toValue: 0.35, duration: 600, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
        Animated.timing(dot, { toValue: 1, duration: 600, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
      ])
    ).start();
    Animated.loop(
      Animated.sequence([
        Animated.timing(caret, { toValue: 0, duration: 425, useNativeDriver: true }),
        Animated.timing(caret, { toValue: 1, duration: 425, useNativeDriver: true }),
      ])
    ).start();
  }, [caret, dot]);

  return (
    <Screen>
      <View style={{ flex: 1, paddingHorizontal: 28, paddingTop: 40, paddingBottom: spacing.lg }}>
        <View style={{ flex: 1, justifyContent: 'center', marginTop: -40 }}>
          <Text
            style={{
              fontFamily: fontFamily.serifBlack,
              fontSize: 82,
              lineHeight: 76,
              letterSpacing: -3,
              color: colors.ink,
            }}
          >
            Briefly
            <Text style={{ color: colors.accent }}>.</Text>
          </Text>

          {/* Rotating headline ticker — fixed-height to prevent jitter. */}
          <View style={{ marginTop: 44, flexDirection: 'row', alignItems: 'center', gap: 10, height: 32 }}>
            <Animated.View
              style={{
                width: 7,
                height: 7,
                borderRadius: 4,
                backgroundColor: colors.accent,
                opacity: dot,
              }}
            />
            <View style={{ flexDirection: 'row', alignItems: 'center', flexShrink: 1, height: 32 }}>
              <Text
                numberOfLines={1}
                style={{
                  fontFamily: fontFamily.serifRegular,
                  fontStyle: 'italic',
                  fontSize: 22,
                  lineHeight: 32,
                  color: colors.ink2,
                  letterSpacing: -0.2,
                }}
              >
                {ticker}
              </Text>
              <Animated.View
                style={{
                  width: 2,
                  height: 22,
                  marginLeft: 2,
                  backgroundColor: colors.ink,
                  opacity: caret,
                }}
              />
            </View>
          </View>

          <Text
            style={{
              fontFamily: fontFamily.serifMedium,
              fontStyle: 'italic',
              fontSize: 26,
              color: colors.ink2,
              marginTop: 14,
              lineHeight: 34,
              letterSpacing: -0.3,
            }}
          >
            목소리로 편하게 듣는{'\n'}오늘의 헤드라인
          </Text>
        </View>

        {/* CTA — opens bottom sheet */}
        <Pressable
          onPress={() => setSheetOpen(true)}
          style={({ pressed }) => ({
            backgroundColor: colors.ink,
            borderRadius: radius.sm,
            paddingVertical: 18,
            paddingHorizontal: 20,
            flexDirection: 'row',
            alignItems: 'center',
            justifyContent: 'space-between',
            opacity: pressed ? 0.85 : 1,
          })}
        >
          <Text style={{ color: colors.paper, fontSize: 15, fontWeight: '600' }}>
            시작하기
          </Text>
          <Ionicons name="arrow-forward" size={18} color={colors.paper} />
        </Pressable>
      </View>

      <AuthSheet
        visible={sheetOpen}
        onClose={() => setSheetOpen(false)}
        onAuthenticated={() => {
          setSheetOpen(false);
          router.replace('/');
        }}
      />
    </Screen>
  );
}
