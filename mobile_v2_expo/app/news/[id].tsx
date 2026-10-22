import {
  View,
  Text,
  Pressable,
  ScrollView,
  ActivityIndicator,
  Linking,
} from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';
import Ionicons from '@expo/vector-icons/Ionicons';
import { Screen } from '@/components/Screen';
import { CatBadge } from '@/components/CatBadge';
import { Placeholder } from '@/components/Placeholder';
import { colors, fontFamily, radius, spacing } from '@/theme/tokens';
import { useNewsCard } from '@/hooks/useNewsCards';

export default function NewsDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { card, loading, error } = useNewsCard(id);

  return (
    <Screen>
      <View
        style={{
          paddingHorizontal: spacing.lg,
          paddingVertical: spacing.md - 4,
          flexDirection: 'row',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <Pressable onPress={() => router.back()} hitSlop={12}>
          <Ionicons name="arrow-back" size={22} color={colors.ink} />
        </Pressable>
        <View style={{ flexDirection: 'row', gap: 18 }}>
          <Ionicons name="bookmark-outline" size={20} color={colors.ink3} />
          <Ionicons name="share-outline" size={20} color={colors.ink3} />
          <Ionicons name="ellipsis-horizontal" size={20} color={colors.ink3} />
        </View>
      </View>

      {loading ? (
        <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>
          <ActivityIndicator color={colors.ink} />
        </View>
      ) : error || !card ? (
        <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', gap: 12 }}>
          <Ionicons name="alert-circle-outline" size={48} color={colors.ink4} />
          <Text style={{ fontSize: 14, color: colors.ink3 }}>기사를 찾을 수 없어요</Text>
        </View>
      ) : (
        <>
          <ScrollView contentContainerStyle={{ paddingHorizontal: spacing.lg, paddingBottom: spacing.lg }}>
            <CatBadge categoryId={card.category} size="md" />
            <Text
              style={{
                fontFamily: fontFamily.serifBlack,
                fontSize: 26,
                lineHeight: 32,
                color: colors.ink,
                letterSpacing: -0.5,
                marginTop: 10,
              }}
            >
              {card.title}
            </Text>
            <Text
              style={{
                fontSize: 10.5,
                color: colors.ink3,
                letterSpacing: 1.2,
                marginTop: 12,
              }}
            >
              {[card.provider, card.byline, card.published_at].filter(Boolean).join(' · ')}
            </Text>
            <View style={{ marginTop: 16 }}>
              <Placeholder
                uri={card.images}
                height={200}
                categoryId={card.category}
                label="기사 사진"
              />
            </View>

            {card.hilight && (
              <View style={{ marginTop: 18, flexDirection: 'row', gap: 14 }}>
                <View style={{ width: 3, backgroundColor: colors.accent }} />
                <View style={{ flex: 1 }}>
                  <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6, marginBottom: 6 }}>
                    <Ionicons name="sparkles-outline" size={12} color={colors.accent} />
                    <Text style={{ fontSize: 10, color: colors.accent, letterSpacing: 1.2 }}>
                      AI 요약
                    </Text>
                  </View>
                  <Text
                    style={{
                      fontFamily: fontFamily.serifRegular,
                      fontSize: 15,
                      lineHeight: 25,
                      color: colors.ink,
                    }}
                  >
                    {card.hilight}
                  </Text>
                </View>
              </View>
            )}

            {card.content && (
              <Text
                style={{
                  marginTop: 22,
                  fontFamily: fontFamily.serifRegular,
                  fontSize: 15.5,
                  lineHeight: 28,
                  color: colors.ink2,
                }}
              >
                {card.content}
              </Text>
            )}

            <View
              style={{
                marginTop: 22,
                padding: 14,
                backgroundColor: colors.paper2,
                borderRadius: radius.sm,
              }}
            >
              <Text style={{ fontSize: 12, color: colors.ink3, lineHeight: 19 }}>
                이 기사는 관련 보도{' '}
                <Text style={{ color: colors.ink, fontWeight: '700' }}>{card.cluster_size}건</Text>
                의 대표 기사입니다.
              </Text>
            </View>
          </ScrollView>

          {card.provider_link_page && (
            <View
              style={{
                paddingHorizontal: spacing.lg,
                paddingVertical: spacing.md - 4,
                borderTopColor: colors.line,
                borderTopWidth: 1,
                backgroundColor: colors.card,
              }}
            >
              <Pressable
                onPress={() => Linking.openURL(card.provider_link_page!)}
                style={{
                  paddingVertical: 14,
                  backgroundColor: colors.ink,
                  borderRadius: radius.sm,
                  flexDirection: 'row',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: 8,
                }}
              >
                <Text style={{ color: colors.paper, fontSize: 14, fontWeight: '600' }}>원문 보기</Text>
                <Ionicons name="open-outline" size={14} color={colors.paper} />
              </Pressable>
            </View>
          )}
        </>
      )}
    </Screen>
  );
}
