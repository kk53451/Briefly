import { useMemo, useRef, useState } from 'react';
import {
  View,
  Text,
  Pressable,
  ScrollView,
  Dimensions,
  ActivityIndicator,
  type NativeSyntheticEvent,
  type NativeScrollEvent,
} from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import { router } from 'expo-router';
import { Screen } from '@/components/Screen';
import { BrieflyMark } from '@/components/BrieflyMark';
import { CatBadge } from '@/components/CatBadge';
import { Placeholder } from '@/components/Placeholder';
import { Divider } from '@/components/Divider';
import { colors, fontFamily, radius, shadow, spacing } from '@/theme/tokens';
import { getCategory } from '@/theme/categories';
import { useHeadlines } from '@/hooks/useHeadlines';
import { currentSlot, formatTodayKorean } from '@/lib/date';
import type { Slot } from '@/types/db';

const { width: SCREEN_W } = Dimensions.get('window');

export default function TodayScreen() {
  const [slot, setSlot] = useState<Slot>(currentSlot());
  const { items, loading, error } = useHeadlines(slot);
  const scrollRef = useRef<ScrollView>(null);
  const [active, setActive] = useState(0);

  const today = useMemo(formatTodayKorean, []);

  const onScroll = (e: NativeSyntheticEvent<NativeScrollEvent>) => {
    const idx = Math.round(e.nativeEvent.contentOffset.x / SCREEN_W);
    if (idx !== active) setActive(idx);
  };

  return (
    <Screen>
      {/* Header */}
      <View style={{ paddingHorizontal: spacing.lg, paddingTop: spacing.md - 2 }}>
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
          <Text
            style={{
              fontFamily: fontFamily.mono,
              fontSize: 10,
              color: colors.ink3,
              letterSpacing: 0.8,
            }}
          >
            {today}
          </Text>
        </View>

        <View
          style={{
            flexDirection: 'row',
            justifyContent: 'space-between',
            alignItems: 'flex-end',
            marginTop: 14,
          }}
        >
          <Text
            style={{
              fontFamily: fontFamily.serifBlack,
              fontSize: 32,
              color: colors.ink,
              letterSpacing: -1,
            }}
          >
            오늘의 브리핑
          </Text>
          <SlotToggle slot={slot} onChange={setSlot} />
        </View>
      </View>

      {/* Progress dots */}
      <View style={{ flexDirection: 'row', gap: 4, paddingHorizontal: spacing.lg, paddingTop: 10, paddingBottom: 12 }}>
        {(items.length ? items : [0, 1, 2, 3, 4, 5]).map((_, i) => (
          <View
            key={i}
            style={{
              flex: 1,
              height: 3,
              borderRadius: 2,
              backgroundColor: i === active ? colors.ink : colors.line,
            }}
          />
        ))}
      </View>

      {loading ? (
        <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>
          <ActivityIndicator color={colors.ink} />
        </View>
      ) : error ? (
        <EmptyOrError icon="cloud-offline-outline" text="브리핑을 불러오지 못했어요" />
      ) : items.length === 0 ? (
        <EmptyOrError
          icon="newspaper-outline"
          text={`${slot === 'AM' ? '오전' : '오후'} 브리핑이 아직 준비되지 않았어요`}
        />
      ) : (
        <ScrollView
          ref={scrollRef}
          horizontal
          pagingEnabled
          showsHorizontalScrollIndicator={false}
          onScroll={onScroll}
          scrollEventThrottle={16}
        >
          {items.map((t, i) => (
            <TopicCard key={`${t.category}-${t.topic_id}`} topic={t} index={i} total={items.length} />
          ))}
        </ScrollView>
      )}
    </Screen>
  );
}

function SlotToggle({ slot, onChange }: { slot: Slot; onChange: (s: Slot) => void }) {
  return (
    <View
      style={{
        flexDirection: 'row',
        backgroundColor: colors.paper2,
        borderRadius: 999,
        padding: 3,
        borderColor: colors.line,
        borderWidth: 1,
      }}
    >
      {(['AM', 'PM'] as Slot[]).map((s) => {
        const on = s === slot;
        return (
          <Pressable
            key={s}
            onPress={() => onChange(s)}
            style={{
              paddingHorizontal: 14,
              paddingVertical: 6,
              borderRadius: 999,
              backgroundColor: on ? colors.ink : 'transparent',
            }}
          >
            <Text
              style={{
                fontFamily: fontFamily.monoMedium,
                fontSize: 11,
                color: on ? colors.paper : colors.ink3,
                letterSpacing: 0.4,
              }}
            >
              {s === 'AM' ? '오전' : '오후'}
            </Text>
          </Pressable>
        );
      })}
    </View>
  );
}

function TopicCard({
  topic,
  index,
  total,
}: {
  topic: { category: string; topic_id: number; headline: string; summary: string; cluster_size: number; representative_title: string; representative_image: string | null; representative_press: string; keywords: string[]; representative_news_id: string };
  index: number;
  total: number;
}) {
  const cat = getCategory(topic.category);
  const color = cat?.color ?? colors.ink;

  return (
    <ScrollView
      style={{ width: SCREEN_W }}
      contentContainerStyle={{ paddingHorizontal: 20, paddingBottom: 16 }}
      showsVerticalScrollIndicator={false}
    >
      <View
        style={{
          backgroundColor: colors.card,
          borderRadius: radius.md,
          borderColor: colors.line,
          borderWidth: 1,
          overflow: 'hidden',
          ...shadow.card,
        }}
      >
        {/* Header block */}
        <View
          style={{
            paddingHorizontal: 22,
            paddingTop: 18,
            paddingBottom: 14,
            borderBottomColor: colors.lineSoft,
            borderBottomWidth: 1,
          }}
        >
          <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
            <CatBadge categoryId={topic.category} size="md" />
            <Text
              style={{
                fontSize: 10,
                color: colors.ink3,
                letterSpacing: 1.2,
              }}
            >
              토픽 {String(index + 1).padStart(2, '0')} / {String(total).padStart(2, '0')}
            </Text>
          </View>
          <Text
            style={{
              fontFamily: fontFamily.serifBlack,
              fontSize: 26,
              lineHeight: 32,
              color: colors.ink,
              letterSpacing: -0.6,
              marginTop: 14,
            }}
          >
            {topic.headline}
          </Text>
          {topic.keywords?.length > 0 && (
            <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 6, marginTop: 12 }}>
              {topic.keywords.map((k) => (
                <View
                  key={k}
                  style={{
                    paddingHorizontal: 8,
                    paddingVertical: 3,
                    borderColor: `${color}33`,
                    borderWidth: 1,
                    backgroundColor: `${color}0d`,
                    borderRadius: 2,
                  }}
                >
                  <Text style={{ fontSize: 11, color }}>#{k}</Text>
                </View>
              ))}
            </View>
          )}
        </View>

        <Placeholder
          uri={topic.representative_image}
          height={170}
          categoryId={topic.category}
          borderRadius={0}
          label="대표 사진"
        />

        <View style={{ paddingHorizontal: 22, paddingTop: 16, paddingBottom: 20 }}>
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 10 }}>
            <Ionicons name="sparkles-outline" size={13} color={colors.accent} />
            <Text
              style={{
                fontSize: 10,
                color: colors.accent,
                letterSpacing: 1.2,
              }}
            >
              AI 요약
            </Text>
          </View>
          <Text
            style={{
              fontFamily: fontFamily.serifRegular,
              fontSize: 15.5,
              lineHeight: 27,
              color: colors.ink,
            }}
          >
            {topic.summary}
          </Text>

          <View style={{ marginTop: 18, paddingTop: 14 }}>
            <Divider soft />
            <View style={{ marginTop: 10 }}>
              <Text style={{ fontSize: 10, color: colors.ink3, letterSpacing: 1.2, marginBottom: 6 }}>
                대표 기사
              </Text>
              <Text
                style={{
                  fontFamily: fontFamily.serif,
                  fontSize: 14,
                  color: colors.ink2,
                  lineHeight: 20,
                }}
              >
                "{topic.representative_title}"
              </Text>
              <Text style={{ fontSize: 11.5, color: colors.ink3, marginTop: 6 }}>
                {topic.representative_press} · 관련 기사{' '}
                <Text style={{ color: colors.accent, fontWeight: '700' }}>
                  {topic.cluster_size}건
                </Text>
              </Text>
            </View>
          </View>
        </View>

        <View style={{ paddingHorizontal: 22, paddingBottom: 18 }}>
          <Pressable
            onPress={() => {
              if (topic.representative_news_id) {
                router.push(`/news/${encodeURIComponent(topic.representative_news_id)}`);
              }
            }}
            style={{
              paddingVertical: 12,
              borderRadius: radius.sm,
              borderColor: colors.ink,
              borderWidth: 1,
              flexDirection: 'row',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 8,
            }}
          >
            <Text style={{ fontSize: 13, fontWeight: '600', color: colors.ink }}>
              대표 기사 보기
            </Text>
            <Ionicons name="chevron-forward" size={14} color={colors.ink} />
          </Pressable>
        </View>
      </View>
    </ScrollView>
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
