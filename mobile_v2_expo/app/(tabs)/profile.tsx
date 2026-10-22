import { useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  Pressable,
  Switch,
  Alert,
  ActivityIndicator,
} from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import { router } from 'expo-router';
import { Screen } from '@/components/Screen';
import { BrieflyMark } from '@/components/BrieflyMark';
import { colors, fontFamily, radius, spacing } from '@/theme/tokens';
import { getCategory, type CategoryId } from '@/theme/categories';
import { useAuth, signOut } from '@/hooks/useAuth';
import { useProfile } from '@/hooks/useProfile';

export default function ProfileScreen() {
  const { user, loading: authLoading } = useAuth();
  const { profile, loading: profileLoading } = useProfile(user?.id ?? null);
  const [darkMode, setDarkMode] = useState(false); // reserved for post-v1

  const interests = (profile?.interests ?? []) as CategoryId[];

  const doSignOut = () => {
    Alert.alert('로그아웃', '정말 로그아웃 하시겠어요?', [
      { text: '취소', style: 'cancel' },
      {
        text: '로그아웃',
        style: 'destructive',
        onPress: async () => {
          await signOut();
          router.replace('/(auth)/login');
        },
      },
    ]);
  };

  if (authLoading || (user && profileLoading)) {
    return (
      <Screen>
        <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>
          <ActivityIndicator color={colors.ink} />
        </View>
      </Screen>
    );
  }

  const firstChar = profile?.nickname?.trim()?.charAt(0) ?? '독';

  return (
    <Screen>
      <View
        style={{
          paddingHorizontal: spacing.lg,
          paddingTop: spacing.md - 2,
          paddingBottom: 10,
          borderBottomColor: colors.ink,
          borderBottomWidth: 2,
        }}
      >
        <BrieflyMark size={18} />
      </View>

      <ScrollView style={{ flex: 1 }}>
        {/* Profile card */}
        <View
          style={{
            paddingHorizontal: spacing.lg,
            paddingVertical: spacing.lg - 6,
            flexDirection: 'row',
            alignItems: 'center',
            gap: 16,
            borderBottomColor: colors.line,
            borderBottomWidth: 1,
          }}
        >
          <View
            style={{
              width: 64,
              height: 64,
              borderRadius: 32,
              backgroundColor: colors.accentSoft,
              borderColor: colors.line,
              borderWidth: 1,
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Text
              style={{
                fontFamily: fontFamily.serifBlack,
                fontSize: 26,
                color: colors.accent,
              }}
            >
              {firstChar}
            </Text>
          </View>
          <View style={{ flex: 1 }}>
            <Text style={{ fontFamily: fontFamily.serif, fontSize: 20, color: colors.ink }}>
              {profile?.nickname ?? '독자'}
            </Text>
            <Text style={{ fontSize: 10.5, color: colors.ink3, letterSpacing: 0.6, marginTop: 4 }}>
              {user?.email ?? '게스트 구독'}
            </Text>
          </View>
        </View>

        {/* Interests */}
        <View
          style={{
            paddingHorizontal: spacing.lg,
            paddingTop: spacing.md + 2,
            paddingBottom: 8,
            flexDirection: 'row',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <Text style={{ fontFamily: fontFamily.serif, fontSize: 15, color: colors.ink2 }}>
            관심 주제
          </Text>
          <Pressable onPress={() => router.push('/(auth)/onboarding')}>
            <Text style={{ fontSize: 12, color: colors.accent, fontWeight: '600' }}>편집</Text>
          </Pressable>
        </View>

        <View
          style={{
            paddingHorizontal: spacing.lg,
            paddingBottom: spacing.lg - 4,
            flexDirection: 'row',
            gap: 6,
            flexWrap: 'wrap',
          }}
        >
          {interests.length === 0 ? (
            <Text style={{ fontSize: 12, color: colors.ink3 }}>
              관심 주제를 설정해주세요
            </Text>
          ) : (
            interests.map((id) => {
              const c = getCategory(id);
              if (!c) return null;
              return (
                <View
                  key={id}
                  style={{
                    paddingHorizontal: 12,
                    paddingVertical: 6,
                    borderColor: `${c.color}55`,
                    borderWidth: 1,
                    borderRadius: 999,
                    backgroundColor: `${c.color}0d`,
                  }}
                >
                  <Text style={{ fontSize: 12, color: c.color, fontWeight: '600' }}>{c.ko}</Text>
                </View>
              );
            })
          )}
        </View>

        {/* Settings list */}
        <View style={{ paddingHorizontal: spacing.lg }}>
          <View
            style={{
              paddingTop: 10,
              borderTopColor: colors.line,
              borderTopWidth: 1,
            }}
          >
            <Text
              style={{
                fontFamily: fontFamily.serif,
                fontSize: 15,
                color: colors.ink2,
                marginBottom: 6,
              }}
            >
              설정
            </Text>
          </View>

          <SettingRow
            icon="moon-outline"
            label="다크 모드"
            detail="후속 릴리스 예정"
            right={
              <Switch
                value={darkMode}
                onValueChange={setDarkMode}
                disabled
                trackColor={{ true: colors.accent, false: colors.line }}
              />
            }
          />
          <SettingRow icon="bookmark-outline" label="북마크" detail="준비 중" chevron />
          <SettingRow icon="notifications-outline" label="알림" detail="AM 07:30 · PM 18:00" chevron />
          <SettingRow icon="information-circle-outline" label="앱 정보" detail="v2.0.0" chevron last />
        </View>

        {user && (
          <View style={{ paddingHorizontal: spacing.lg, paddingTop: 10, paddingBottom: spacing.lg }}>
            <Pressable onPress={doSignOut} style={{ paddingVertical: 14, alignItems: 'center' }}>
              <Text style={{ fontSize: 13.5, color: colors.ink, fontWeight: '600' }}>로그아웃</Text>
            </Pressable>
          </View>
        )}
      </ScrollView>
    </Screen>
  );
}

function SettingRow({
  icon,
  label,
  detail,
  right,
  chevron,
  last,
}: {
  icon: keyof typeof Ionicons.glyphMap;
  label: string;
  detail?: string;
  right?: React.ReactNode;
  chevron?: boolean;
  last?: boolean;
}) {
  return (
    <View
      style={{
        flexDirection: 'row',
        alignItems: 'center',
        gap: 14,
        paddingVertical: 14,
        borderBottomColor: colors.lineSoft,
        borderBottomWidth: last ? 0 : 1,
      }}
    >
      <View
        style={{
          width: 32,
          height: 32,
          borderRadius: radius.sm,
          backgroundColor: colors.paper2,
          borderColor: colors.line,
          borderWidth: 1,
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <Ionicons name={icon} size={16} color={colors.ink2} />
      </View>
      <View style={{ flex: 1 }}>
        <Text style={{ fontFamily: fontFamily.serif, fontSize: 15, color: colors.ink, fontWeight: '600' }}>
          {label}
        </Text>
        {detail && <Text style={{ fontSize: 11.5, color: colors.ink3, marginTop: 1 }}>{detail}</Text>}
      </View>
      {right ?? (chevron && <Ionicons name="chevron-forward" size={16} color={colors.ink4} />)}
    </View>
  );
}
