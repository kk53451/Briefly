import { useMemo, useState } from 'react';
import {
  View,
  Text,
  Pressable,
  ScrollView,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import { router } from 'expo-router';
import { Screen } from '@/components/Screen';
import { BrieflyMark } from '@/components/BrieflyMark';
import { CatBadge } from '@/components/CatBadge';
import { Placeholder } from '@/components/Placeholder';
import { Divider } from '@/components/Divider';
import { colors, fontFamily, spacing } from '@/theme/tokens';
import { CATEGORIES, getCategory, type CategoryId } from '@/theme/categories';
import { useNewsCards } from '@/hooks/useNewsCards';
import { useProfile } from '@/hooks/useProfile';
import { useAuth } from '@/hooks/useAuth';
import { formatPublishedAt } from '@/lib/date';
import type { NewsCard } from '@/types/db';

type Tab = 'all' | 'my' | CategoryId;

const TABS: { id: Tab; ko: string }[] = [
  { id: 'all', ko: '종합' },
  { id: 'my', ko: 'MY' },
  ...CATEGORIES.map((c) => ({ id: c.id as Tab, ko: c.ko })),
];

export default function HomeScreen() {
  const [tab, setTab] = useState<Tab>('all');
  const { user } = useAuth();
  const { profile } = useProfile(user?.id ?? null);
  const interests = (profile?.interests ?? []) as CategoryId[];
  const { cards, loading, error } = useNewsCards(tab, interests);

  const refreshTs = useMemo(() => {
    const d = new Date();
    const hh = String(d.getHours()).padStart(2, '0');
    const mm = String(d.getMinutes()).padStart(2, '0');
    return `${d.getFullYear()}. ${d.getMonth() + 1}. ${d.getDate()}. ${hh}:${mm} 업데이트`;
  }, [cards]);

  const [refreshing, setRefreshing] = useState(false);
  const onRefresh = async () => {
    setRefreshing(true);
    // Trigger re-fetch by toggling tab state equal (via setState to same value triggers re-render but not fetch; use a date bump instead).
    setTab((t) => t);
    setTimeout(() => setRefreshing(false), 600);
  };

  const [lead, ...rest] = cards;

  return (
    <Screen>
      {/* Masthead */}
      <View style={{ paddingHorizontal: spacing.lg, paddingTop: spacing.md - 4 }}>
        <View
          style={{
            flexDirection: 'row',
            justifyContent: 'space-between',
            alignItems: 'flex-end',
            paddingBottom: 10,
            borderBottomColor: colors.ink,
            borderBottomWidth: 2,
          }}
        >
          <BrieflyMark size={18} />
          <View style={{ flexDirection: 'row', gap: 14 }}>
            <Ionicons name="search-outline" size={18} color={colors.ink3} />
            <Ionicons name="notifications-outline" size={18} color={colors.ink3} />
          </View>
        </View>
      </View>

      {/* Category tabs */}
      <View style={{ borderBottomColor: colors.line, borderBottomWidth: 1 }}>
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={{ paddingHorizontal: spacing.md, paddingVertical: 10, gap: 2 }}
        >
          {TABS.map((t) => {
            const on = t.id === tab;
            const cat = getCategory(t.id);
            const underline = on ? (cat?.color ?? colors.ink) : 'transparent';
            return (
              <Pressable
                key={t.id}
                onPress={() => setTab(t.id)}
                style={{
                  paddingHorizontal: 14,
                  paddingVertical: 8,
                  borderBottomColor: underline,
                  borderBottomWidth: 2,
                  marginBottom: -1,
                }}
              >
                <Text
                  style={{
                    fontFamily: fontFamily.serif,
                    fontWeight: on ? '700' : '500',
                    fontSize: 15,
                    letterSpacing: -0.2,
                    color: on ? colors.ink : colors.ink3,
                  }}
                >
                  {t.ko}
                </Text>
              </Pressable>
            );
          })}
        </ScrollView>
      </View>

      {/* Sort bar */}
      <View
        style={{
          paddingHorizontal: spacing.lg,
          paddingVertical: 12,
          flexDirection: 'row',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
          <Ionicons name="swap-vertical-outline" size={14} color={colors.ink2} />
          <Text style={{ fontSize: 13, color: colors.ink2, fontWeight: '600' }}>트렌드순</Text>
        </View>
        <Text style={{ fontSize: 10, color: colors.ink3, letterSpacing: 0.6 }}>{refreshTs}</Text>
      </View>

      {loading && cards.length === 0 ? (
        <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>
          <ActivityIndicator color={colors.ink} />
        </View>
      ) : error ? (
        <EmptyOrError icon="cloud-offline-outline" text="뉴스를 불러오지 못했어요" />
      ) : cards.length === 0 ? (
        <EmptyOrError
          icon="newspaper-outline"
          text={
            tab === 'my' && interests.length === 0
              ? '관심 카테고리를 설정해주세요'
              : '표시할 뉴스가 없습니다'
          }
        />
      ) : (
        <ScrollView
          contentContainerStyle={{ paddingHorizontal: spacing.lg, paddingBottom: 16 }}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.ink3} />}
        >
          {lead && <LeadCard card={lead} displayCategoryId={tab === 'all' || tab === 'my' ? lead.category : tab} />}
          {rest.map((n, i) => (
            <RowCard
              key={n.news_id}
              card={n}
              isLast={i === rest.length - 1}
              displayCategoryId={tab === 'all' || tab === 'my' ? n.category : tab}
            />
          ))}
        </ScrollView>
      )}
    </Screen>
  );
}

function LeadCard({ card, displayCategoryId }: { card: NewsCard; displayCategoryId: string }) {
  return (
    <Pressable
      onPress={() => router.push(`/news/${encodeURIComponent(card.news_id)}`)}
      style={{ paddingBottom: 18, borderBottomColor: colors.line, borderBottomWidth: 1 }}
    >
      <Placeholder
        uri={card.images}
        height={180}
        categoryId={card.category}
        label="리드 사진"
      />
      <View style={{ marginTop: 12 }}>
        <CatBadge categoryId={displayCategoryId} />
        <Text
          style={{
            fontFamily: fontFamily.serifBlack,
            fontSize: 22,
            lineHeight: 28,
            letterSpacing: -0.4,
            marginTop: 8,
            color: colors.ink,
          }}
        >
          {card.title}
        </Text>
        <View style={{ flexDirection: 'row', gap: 8, marginTop: 8 }}>
          {card.provider && <Text style={{ fontSize: 11.5, color: colors.ink3 }}>{card.provider}</Text>}
          <Text style={{ fontSize: 11.5, color: colors.ink3 }}>·</Text>
          <Text style={{ fontSize: 11.5, color: colors.ink3 }}>관련 {card.cluster_size}건</Text>
          {card.published_at && (
            <>
              <Text style={{ fontSize: 11.5, color: colors.ink3 }}>·</Text>
              <Text style={{ fontSize: 11.5, color: colors.ink3 }}>{formatPublishedAt(card.published_at)}</Text>
            </>
          )}
        </View>
      </View>
    </Pressable>
  );
}

function RowCard({
  card,
  isLast,
  displayCategoryId,
}: {
  card: NewsCard;
  isLast: boolean;
  displayCategoryId: string;
}) {
  return (
    <Pressable
      onPress={() => router.push(`/news/${encodeURIComponent(card.news_id)}`)}
      style={{ flexDirection: 'row', gap: 14, paddingVertical: 16 }}
    >
      <View style={{ flex: 1 }}>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 4 }}>
          <Text style={{ fontFamily: fontFamily.mono, fontSize: 10, color: colors.ink3, letterSpacing: 0.8 }}>
            #{card.rank}
          </Text>
          <CatBadge categoryId={displayCategoryId} />
        </View>
        <Text
          style={{
            fontFamily: fontFamily.serif,
            fontSize: 15.5,
            lineHeight: 21,
            color: colors.ink,
            letterSpacing: -0.15,
          }}
          numberOfLines={2}
        >
          {card.title}
        </Text>
        <Text style={{ fontSize: 11, color: colors.ink3, marginTop: 6 }}>
          {[card.provider, `관련 ${card.cluster_size}건`, formatPublishedAt(card.published_at)]
            .filter(Boolean)
            .join(' · ')}
        </Text>
      </View>
      <Placeholder
        uri={card.images}
        width={84}
        height={84}
        categoryId={card.category}
        label={String(card.rank)}
      />
      {!isLast && (
        <View style={{ position: 'absolute', left: 0, right: 0, bottom: 0 }}>
          <Divider soft />
        </View>
      )}
    </Pressable>
  );
}

function EmptyOrError({ icon, text }: { icon: keyof typeof Ionicons.glyphMap; text: string }) {
  return (
    <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', gap: 12 }}>
      <Ionicons name={icon} size={48} color={colors.ink4} />
      <Text style={{ fontSize: 14, color: colors.ink3 }}>{text}</Text>
    </View>
  );
}
