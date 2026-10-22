import { useEffect, useMemo, useState } from 'react';
import {
  View,
  Text,
  Pressable,
  ScrollView,
  ActivityIndicator,
} from 'react-native';
import Slider from '@react-native-community/slider';
import Ionicons from '@expo/vector-icons/Ionicons';
import { Screen } from '@/components/Screen';
import { BrieflyMark } from '@/components/BrieflyMark';
import { colors, fontFamily, radius, spacing } from '@/theme/tokens';
import {
  useRecentEpisodes,
  type EpisodeSlot,
  type EpisodeStatus,
} from '@/hooks/usePodcast';
import { usePodcastPlayer, formatMs } from '@/hooks/usePodcastPlayer';
import {
  currentSlot,
  formatShortDate,
  formatDateKo,
  weekdayKo,
  todayKst,
} from '@/lib/date';
import type { Slot } from '@/types/db';

export default function PodcastScreen() {
  const { timeline, loading } = useRecentEpisodes(7);

  // Default active = today's currently-available slot; fall back to the most
  // recent playable row in the timeline.
  const defaultActive = useMemo(() => {
    const today = todayKst();
    const nowSlot = currentSlot();
    const todaysCurrent = timeline.find(
      (t) => t.date === today && t.slot === nowSlot && t.episode
    );
    if (todaysCurrent) return todaysCurrent;
    return timeline.find((t) => t.episode) ?? timeline[0] ?? null;
  }, [timeline]);

  const [activeKey, setActiveKey] = useState<string | null>(null);
  const active = useMemo<EpisodeSlot | null>(() => {
    if (activeKey) {
      return timeline.find((t) => `${t.date}#${t.slot}` === activeKey) ?? defaultActive;
    }
    return defaultActive;
  }, [activeKey, timeline, defaultActive]);

  useEffect(() => {
    if (!activeKey && defaultActive) {
      setActiveKey(`${defaultActive.date}#${defaultActive.slot}`);
    }
  }, [defaultActive, activeKey]);

  const audioUrl = active?.episode?.audioUrl ?? null;
  const player = usePodcastPlayer(audioUrl);

  // `title` = Gemma4-generated one-line summary (e.g. "추경 35조 합의, 서울 아파트 반등, …").
  // `duration_sec` = mutagen-probed length; falls back to player duration when NULL.
  const durationSec = active?.episode?.duration_sec;
  const duration = durationSec
    ? formatMs(durationSec * 1000)
    : formatMs(player.durationMillis);
  const headline =
    active?.episode?.title ||
    (active?.episode ? '오늘의 주요 이슈 브리핑' : null);

  return (
    <Screen>
      {/* Header */}
      <View
        style={{
          paddingHorizontal: spacing.lg,
          paddingTop: spacing.md - 2,
          paddingBottom: 10,
          flexDirection: 'row',
          justifyContent: 'space-between',
          alignItems: 'center',
          borderBottomColor: colors.line,
          borderBottomWidth: 1,
        }}
      >
        <BrieflyMark size={16} />
        <Text style={{ fontSize: 10, color: colors.ink3, letterSpacing: 1.2 }}>
          {active && active.status === 'playing' ? '재생 중' : '오늘의 팟캐스트'}
        </Text>
        <Ionicons name="share-outline" size={18} color={colors.ink3} />
      </View>

      <ScrollView style={{ flex: 1 }}>
        {/* Wide ink album art */}
        <View
          style={{
            height: 180,
            backgroundColor: colors.ink,
            paddingHorizontal: spacing.lg,
            paddingVertical: 20,
            justifyContent: 'space-between',
          }}
        >
          <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'baseline' }}>
            <Text
              style={{
                fontFamily: fontFamily.monoBold,
                fontSize: 10,
                letterSpacing: 1.2,
                color: colors.accent,
              }}
            >
              ● 오늘의 팟캐스트{active ? ` · ${active.slot}` : ''}
            </Text>
            {active && (
              <Text
                style={{
                  fontSize: 10,
                  color: 'rgba(247,242,233,0.9)',
                  letterSpacing: 0.6,
                }}
              >
                {formatDateKo(active.date)} · {active.slot === 'AM' ? '오전' : '오후'}
              </Text>
            )}
          </View>
          <View>
            <Text
              style={{
                fontFamily: fontFamily.serifBlack,
                fontSize: 36,
                letterSpacing: -1.2,
                lineHeight: 38,
                color: colors.paper,
              }}
            >
              오늘의 팟캐스트
            </Text>
            {active && (
              <Text
                style={{
                  fontFamily: fontFamily.serifRegular,
                  fontStyle: 'italic',
                  fontSize: 14,
                  color: colors.paper,
                  opacity: 0.85,
                  marginTop: 6,
                }}
              >
                {formatDateKo(active.date)} · {active.slot === 'AM' ? '오전' : '오후'} 브리핑
                {active.episode?.duration_sec ? ` · ${duration}` : ''}
              </Text>
            )}
          </View>
        </View>

        {/* Subtitle + progress + controls */}
        <View style={{ paddingHorizontal: spacing.lg, paddingTop: 18, paddingBottom: 10 }}>
          {headline && (
            <Text
              style={{
                fontFamily: fontFamily.serif,
                fontSize: 18,
                lineHeight: 24,
                letterSpacing: -0.3,
                color: colors.ink,
                marginBottom: 14,
              }}
              numberOfLines={2}
            >
              {headline}
            </Text>
          )}
          <Progress player={player} />
          <Controls player={player} disabled={!audioUrl} />
        </View>

        {/* Script preview */}
        {active?.episode?.script && (
          <View style={{ paddingHorizontal: spacing.lg, paddingTop: 18 }}>
            <View
              style={{
                flexDirection: 'row',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: 10,
              }}
            >
              <Text
                style={{
                  fontFamily: fontFamily.serif,
                  fontSize: 12,
                  color: colors.accent,
                  letterSpacing: -0.2,
                }}
              >
                오늘의 대본
              </Text>
              <Text style={{ fontSize: 11, color: colors.ink3 }}>전체 보기</Text>
            </View>
            <View
              style={{
                backgroundColor: colors.paper2,
                padding: 14,
                borderLeftColor: colors.accent,
                borderLeftWidth: 2,
              }}
            >
              <Text
                style={{
                  fontFamily: fontFamily.serifRegular,
                  fontSize: 13.5,
                  lineHeight: 23,
                  color: colors.ink2,
                }}
                numberOfLines={10}
              >
                {active.episode.script}
              </Text>
            </View>
          </View>
        )}

        {/* Recent episodes */}
        <View style={{ paddingHorizontal: spacing.lg, paddingTop: 16, paddingBottom: spacing.xl }}>
          <View
            style={{
              flexDirection: 'row',
              justifyContent: 'space-between',
              alignItems: 'baseline',
              paddingBottom: 10,
              borderBottomColor: colors.line,
              borderBottomWidth: 1,
            }}
          >
            <Text style={{ fontSize: 10, color: colors.ink3, letterSpacing: 1.2 }}>
              최근 에피소드
            </Text>
          </View>

          {loading && timeline.length === 0 ? (
            <ActivityIndicator style={{ marginTop: 24 }} color={colors.ink} />
          ) : (
            timeline.map((t, i) => (
              <EpisodeRow
                key={`${t.date}#${t.slot}`}
                slot={t}
                isCurrent={active ? `${active.date}#${active.slot}` === `${t.date}#${t.slot}` : false}
                isPlaying={player.isPlaying}
                isLast={i === timeline.length - 1}
                onPress={() => {
                  if (t.episode) setActiveKey(`${t.date}#${t.slot}`);
                }}
              />
            ))
          )}
        </View>
      </ScrollView>
    </Screen>
  );
}

function EpisodeRow({
  slot,
  isCurrent,
  isPlaying,
  isLast,
  onPress,
}: {
  slot: EpisodeSlot;
  isCurrent: boolean;
  isPlaying: boolean;
  isLast: boolean;
  onPress: () => void;
}) {
  const isUp = slot.status === 'upcoming';
  const isMissed = slot.status === 'missed' && !slot.episode;
  const tileBg = isCurrent ? colors.accent : isUp || isMissed ? colors.paper2 : colors.ink;
  const tileTextColor = isUp || isMissed ? colors.ink3 : colors.paper;

  return (
    <Pressable
      onPress={onPress}
      disabled={!slot.episode}
      style={{
        flexDirection: 'row',
        alignItems: 'center',
        gap: 12,
        paddingVertical: 12,
        borderBottomColor: colors.lineSoft,
        borderBottomWidth: isLast ? 0 : 1,
        opacity: isUp || isMissed ? 0.55 : 1,
      }}
    >
      {/* Date/slot tile */}
      <View
        style={{
          width: 44,
          height: 44,
          borderRadius: radius.sm,
          backgroundColor: tileBg,
          alignItems: 'center',
          justifyContent: 'center',
          borderColor: isUp ? colors.ink4 : 'transparent',
          borderWidth: isUp ? 1 : 0,
          borderStyle: isUp ? 'dashed' : undefined,
        }}
      >
        <Text
          style={{
            fontFamily: fontFamily.mono,
            fontSize: 9,
            letterSpacing: 0.9,
            color: tileTextColor,
            opacity: 0.75,
          }}
        >
          {formatShortDate(slot.date)}
        </Text>
        <Text
          style={{
            fontFamily: fontFamily.serifBlack,
            fontSize: 13,
            color: tileTextColor,
            marginTop: 1,
          }}
        >
          {slot.slot}
        </Text>
      </View>

      <View style={{ flex: 1, minWidth: 0 }}>
        <View style={{ flexDirection: 'row', alignItems: 'baseline', gap: 6, flexWrap: 'wrap' }}>
          <Text
            style={{
              fontFamily: fontFamily.serif,
              fontSize: 14,
              color: isCurrent ? colors.accent : colors.ink,
            }}
          >
            {formatDateKo(slot.date)} ({weekdayKo(slot.date)}) {slot.slot === 'AM' ? '오전' : '오후'}
          </Text>
          <StatusBadge status={slot.status} isPlaying={isCurrent && isPlaying} />
        </View>
        <Text
          numberOfLines={1}
          style={{ fontSize: 11.5, color: colors.ink3, marginTop: 2 }}
        >
          {slot.episode?.title ?? (isUp ? '브리핑 준비 중' : isMissed ? '방송 정보 없음' : '오늘의 브리핑')}
        </Text>
        <Text
          style={{
            fontSize: 9.5,
            color: colors.ink4,
            letterSpacing: 0.6,
            marginTop: 3,
          }}
        >
          {isUp
            ? `${slot.slot === 'AM' ? '07:30' : '18:00'} 발행 예정`
            : slot.episode?.duration_sec
              ? formatMs(slot.episode.duration_sec * 1000)
              : isMissed
                ? '—'
                : '재생 가능'}
        </Text>
      </View>

      {isCurrent ? (
        isPlaying ? (
          <Ionicons name="volume-high" size={18} color={colors.accent} />
        ) : (
          <Ionicons name="pause" size={16} color={colors.accent} />
        )
      ) : isUp ? (
        <Ionicons name="notifications-outline" size={16} color={colors.ink4} />
      ) : isMissed ? (
        <Ionicons name="remove" size={16} color={colors.ink4} />
      ) : (
        <Ionicons name="play" size={16} color={colors.ink3} />
      )}
    </Pressable>
  );
}

function StatusBadge({ status, isPlaying }: { status: EpisodeStatus; isPlaying: boolean }) {
  if (isPlaying) {
    return (
      <Text style={{ fontSize: 9, color: colors.accent, letterSpacing: 1 }}>● 재생 중</Text>
    );
  }
  if (status === 'upcoming') {
    return (
      <Text style={{ fontFamily: fontFamily.mono, fontSize: 9, color: colors.ink3, letterSpacing: 0.6 }}>
        예정
      </Text>
    );
  }
  return null;
}

function Progress({ player }: { player: ReturnType<typeof usePodcastPlayer> }) {
  const dur = player.durationMillis || 1;
  return (
    <View>
      <Slider
        minimumValue={0}
        maximumValue={dur}
        value={player.positionMillis}
        minimumTrackTintColor={colors.ink}
        maximumTrackTintColor={colors.line}
        thumbTintColor={colors.ink}
        onSlidingComplete={(v) => player.seekTo(v)}
        disabled={!player.isLoaded}
        style={{ height: 30 }}
      />
      <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginTop: 2 }}>
        <Text style={{ fontFamily: fontFamily.mono, fontSize: 11, color: colors.ink3, letterSpacing: 0.6 }}>
          {formatMs(player.positionMillis)}
        </Text>
        <Text style={{ fontFamily: fontFamily.mono, fontSize: 11, color: colors.ink3, letterSpacing: 0.6 }}>
          {formatMs(player.durationMillis)}
        </Text>
      </View>
    </View>
  );
}

function Controls({
  player,
  disabled,
}: {
  player: ReturnType<typeof usePodcastPlayer>;
  disabled?: boolean;
}) {
  const rate = player.rate === 1 ? 1.5 : 1;
  return (
    <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginTop: 20 }}>
      <Pressable
        onPress={() => player.setRate(rate)}
        disabled={disabled}
        style={{
          paddingHorizontal: 10,
          paddingVertical: 5,
          borderRadius: 999,
          borderColor: colors.line,
          borderWidth: 1,
        }}
      >
        <Text style={{ fontFamily: fontFamily.monoBold, fontSize: 11, color: colors.ink3, letterSpacing: 0.8 }}>
          {player.rate.toFixed(1)}×
        </Text>
      </Pressable>

      <Pressable onPress={() => player.seekBy(-15000)} disabled={disabled}>
        <Ionicons name="play-back" size={28} color={disabled ? colors.ink4 : colors.ink} />
      </Pressable>

      <Pressable
        onPress={player.toggle}
        disabled={disabled || player.loading}
        style={{
          width: 64,
          height: 64,
          borderRadius: 32,
          backgroundColor: disabled ? colors.ink4 : colors.ink,
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        {player.loading ? (
          <ActivityIndicator color={colors.paper} />
        ) : (
          <Ionicons name={player.isPlaying ? 'pause' : 'play'} size={26} color={colors.paper} />
        )}
      </Pressable>

      <Pressable onPress={() => player.seekBy(15000)} disabled={disabled}>
        <Ionicons name="play-forward" size={28} color={disabled ? colors.ink4 : colors.ink} />
      </Pressable>

      <View style={{ paddingHorizontal: 10, paddingVertical: 6, borderRadius: 999, borderColor: colors.line, borderWidth: 1 }}>
        <Ionicons name="list" size={14} color={colors.ink3} />
      </View>
    </View>
  );
}
