import { useMemo, useState } from 'react';
import {
  View,
  Text,
  Pressable,
  ScrollView,
  ActivityIndicator,
  Alert,
} from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import { router } from 'expo-router';
import { Screen } from '@/components/Screen';
import { CATEGORIES, type CategoryId } from '@/theme/categories';
import { colors, fontFamily, radius, spacing } from '@/theme/tokens';
import { useAuth } from '@/hooks/useAuth';
import { useProfile } from '@/hooks/useProfile';

export default function OnboardingScreen() {
  const { user } = useAuth();
  const { update } = useProfile(user?.id ?? null);
  const [selected, setSelected] = useState<Record<CategoryId, boolean>>({
    politics: false, economy: false, society: false,
    culture: false, international: false, tech: false,
  });
  const [saving, setSaving] = useState(false);

  const count = useMemo(
    () => (Object.values(selected).filter(Boolean).length),
    [selected]
  );

  const toggle = (id: CategoryId) =>
    setSelected((s) => ({ ...s, [id]: !s[id] }));

  const submit = async () => {
    if (count < 1) return;
    setSaving(true);
    try {
      const interests = (Object.entries(selected) as [CategoryId, boolean][])
        .filter(([, v]) => v)
        .map(([k]) => k);
      await update({ interests, onboarding_completed: true });
      router.replace('/(tabs)/today');
    } catch (e) {
      Alert.alert('저장 실패', (e as Error).message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Screen>
      <View
        style={{
          paddingHorizontal: spacing.lg,
          paddingTop: 18,
          flexDirection: 'row',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <Pressable onPress={() => router.back()} hitSlop={12}>
          <Ionicons name="arrow-back" size={22} color={colors.ink3} />
        </Pressable>
        <Text
          style={{
            fontFamily: fontFamily.monoMedium,
            fontSize: 10,
            color: colors.ink3,
            letterSpacing: 1.8,
          }}
        >
          2 / 2
        </Text>
      </View>

      <View style={{ paddingHorizontal: spacing.lg, paddingTop: spacing.md }}>
        <Text
          style={{
            fontFamily: fontFamily.serif,
            fontSize: 30,
            lineHeight: 36,
            letterSpacing: -0.6,
            color: colors.ink,
          }}
        >
          어떤 소식을{'\n'}전해드릴까요?
        </Text>
        <Text
          style={{
            fontSize: 13.5,
            color: colors.ink2,
            marginTop: 10,
            lineHeight: 21,
          }}
        >
          선택한 주제 중심으로 오늘의 브리핑과 팟캐스트를 준비합니다.
        </Text>
      </View>

      <ScrollView
        contentContainerStyle={{
          padding: spacing.md + 4,
          paddingBottom: spacing.lg,
        }}
        style={{ flex: 1 }}
      >
        <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 10 }}>
          {CATEGORIES.map((c) => {
            const on = selected[c.id];
            return (
              <Pressable
                key={c.id}
                onPress={() => toggle(c.id)}
                style={{
                  width: '48.5%',
                  aspectRatio: 1.35,
                  backgroundColor: on ? c.color : colors.card,
                  borderColor: on ? c.color : colors.line,
                  borderWidth: 1,
                  borderRadius: radius.md,
                  padding: 14,
                  justifyContent: 'space-between',
                }}
              >
                <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Ionicons name={c.icon} size={26} color={on ? colors.paper : c.color} />
                  {on && (
                    <View
                      style={{
                        width: 22,
                        height: 22,
                        borderRadius: 11,
                        backgroundColor: colors.paper,
                        alignItems: 'center',
                        justifyContent: 'center',
                      }}
                    >
                      <Ionicons name="checkmark" size={14} color={c.color} />
                    </View>
                  )}
                </View>
                <Text
                  style={{
                    fontFamily: fontFamily.serif,
                    fontSize: 20,
                    color: on ? colors.paper : colors.ink,
                    letterSpacing: -0.4,
                  }}
                >
                  {c.ko}
                </Text>
              </Pressable>
            );
          })}
        </View>
      </ScrollView>

      <View
        style={{
          borderTopColor: colors.line,
          borderTopWidth: 1,
          backgroundColor: colors.card,
          padding: spacing.md - 4,
          paddingHorizontal: spacing.lg,
        }}
      >
        <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginBottom: 10 }}>
          <Text style={{ fontSize: 12, color: colors.ink2 }}>
            <Text style={{ color: colors.accent, fontWeight: '700' }}>{count}개</Text> 선택됨
          </Text>
          <Text style={{ fontSize: 11, color: colors.ink3 }}>최소 1개 이상</Text>
        </View>
        <Pressable
          onPress={submit}
          disabled={count < 1 || saving}
          style={{
            backgroundColor: count < 1 ? colors.ink3 : colors.ink,
            paddingVertical: 16,
            borderRadius: radius.sm,
            alignItems: 'center',
            opacity: saving ? 0.75 : 1,
          }}
        >
          {saving ? (
            <ActivityIndicator color={colors.paper} />
          ) : (
            <Text style={{ color: colors.paper, fontSize: 15, fontWeight: '600' }}>
              시작하기
            </Text>
          )}
        </Pressable>
      </View>
    </Screen>
  );
}
