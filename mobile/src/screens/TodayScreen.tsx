/**
 * Today Screen - Daily TOP 10 News with swipeable cards
 * Redesigned based on 투데이스크린.png reference
 */

import React, { useState, useEffect, useMemo, useRef, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  ActivityIndicator,
  Dimensions,
  NativeSyntheticEvent,
  NativeScrollEvent,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../contexts/ThemeContext';
import { apiClient } from '../services/api';
import { TodayNewsResponse, RankedNewsItem } from '../types/api';
import { TopNewsCard } from '../components/TopNewsCard';
import { ErrorView } from '../components/ErrorView';
import { Spacing, Typography, BorderRadius } from '../constants/theme';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

// Format date header: "11월 26일 수요일"
const formatDateHeader = (): string => {
  const now = new Date();
  const month = now.getMonth() + 1;
  const day = now.getDate();
  const weekdays = ['일요일', '월요일', '화요일', '수요일', '목요일', '금요일', '토요일'];
  const weekday = weekdays[now.getDay()];
  return `${month}월 ${day}일 ${weekday}`;
};

// Get TOP 10 news from API response (rank 1 from each category)
const getTop10News = (newsData: TodayNewsResponse): RankedNewsItem[] => {
  const top10: RankedNewsItem[] = [];

  Object.entries(newsData).forEach(([categoryName, articles]) => {
    // Get rank 1 article from each category
    const sortedArticles = [...articles].sort((a, b) => (a.rank || 999) - (b.rank || 999));
    if (sortedArticles.length > 0) {
      top10.push({
        ...sortedArticles[0],
        categoryName,
      });
    }
  });

  // Sort by rank and limit to 10
  return top10.sort((a, b) => (a.rank || 999) - (b.rank || 999)).slice(0, 10);
};

export const TodayScreen: React.FC = () => {
  const { colors } = useTheme();
  const flatListRef = useRef<FlatList>(null);

  const [newsData, setNewsData] = useState<TodayNewsResponse>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentIndex, setCurrentIndex] = useState(0);

  useEffect(() => {
    loadNews();
  }, []);

  const loadNews = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await apiClient.getTodayNews();
      setNewsData(data);
    } catch (err) {
      console.error('Failed to load today news:', err);
      setError('뉴스를 불러오는데 실패했습니다. 다시 시도해주세요.');
    } finally {
      setIsLoading(false);
    }
  };

  const top10News = useMemo(() => getTop10News(newsData), [newsData]);

  const handleScrollEnd = useCallback(
    (event: NativeSyntheticEvent<NativeScrollEvent>) => {
      const offsetX = event.nativeEvent.contentOffset.x;
      const index = Math.round(offsetX / SCREEN_WIDTH);
      setCurrentIndex(index);
    },
    []
  );

  const scrollToIndex = useCallback((index: number) => {
    if (flatListRef.current && index >= 0 && index < top10News.length) {
      flatListRef.current.scrollToOffset({
        offset: index * SCREEN_WIDTH,
        animated: true,
      });
      setCurrentIndex(index);
    }
  }, [top10News.length]);

  const renderCard = useCallback(
    ({ item, index }: { item: RankedNewsItem; index: number }) => (
      <TopNewsCard item={item} rank={index + 1} />
    ),
    []
  );

  const keyExtractor = useCallback((item: RankedNewsItem) => item.news_id, []);

  if (isLoading) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: colors.background }]}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={colors.primary} />
        </View>
      </SafeAreaView>
    );
  }

  if (error) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: colors.background }]}>
        <ErrorView message={error} onRetry={loadNews} />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: colors.background }]}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={[styles.dateText, { color: colors.textSecondary }]}>
          {formatDateHeader()}
        </Text>
        <Text style={[styles.headerTitle, { color: colors.text }]}>
          데일리 TOP10
        </Text>
        <View style={[styles.infoPill, { backgroundColor: colors.backgroundSecondary }]}>
          <Ionicons name="information-circle-outline" size={16} color={colors.textSecondary} />
          <Text style={[styles.infoText, { color: colors.textSecondary }]}>
            전날 21시 ~ 6시까지 모은 주요뉴스
          </Text>
        </View>
      </View>

      {/* Page Indicator */}
      <View style={styles.indicatorContainer}>
        {top10News.map((_, index) => (
          <TouchableOpacity
            key={index}
            onPress={() => scrollToIndex(index)}
            style={styles.indicatorTouchable}
          >
            <View
              style={[
                styles.indicator,
                {
                  backgroundColor:
                    index === currentIndex ? colors.primary : colors.border,
                },
              ]}
            />
          </TouchableOpacity>
        ))}
      </View>

      {/* Card Carousel */}
      <View style={styles.carouselContainer}>
        <FlatList
          ref={flatListRef}
          data={top10News}
          renderItem={renderCard}
          keyExtractor={keyExtractor}
          horizontal
          pagingEnabled
          showsHorizontalScrollIndicator={false}
          onMomentumScrollEnd={handleScrollEnd}
          getItemLayout={(_, index) => ({
            length: SCREEN_WIDTH,
            offset: SCREEN_WIDTH * index,
            index,
          })}
          initialNumToRender={3}
          maxToRenderPerBatch={3}
          windowSize={5}
          ListEmptyComponent={
            <View style={[styles.emptyContainer, { width: SCREEN_WIDTH }]}>
              <Ionicons name="newspaper-outline" size={64} color={colors.textTertiary} />
              <Text style={[styles.emptyText, { color: colors.textSecondary }]}>
                오늘의 뉴스가 없습니다
              </Text>
            </View>
          }
        />

        {/* Previous Button */}
        {currentIndex > 0 && (
          <TouchableOpacity
            style={[styles.navButton, styles.prevButton, { backgroundColor: colors.card }]}
            onPress={() => scrollToIndex(currentIndex - 1)}
            activeOpacity={0.8}
          >
            <Ionicons name="chevron-back" size={28} color={colors.primary} />
          </TouchableOpacity>
        )}
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: {
    paddingHorizontal: Spacing.lg,
    paddingTop: Spacing.md,
    paddingBottom: Spacing.sm,
  },
  dateText: {
    fontSize: Typography.fontSize.sm,
    marginBottom: Spacing.xs,
  },
  headerTitle: {
    fontSize: Typography.fontSize.xxxl,
    fontWeight: Typography.fontWeight.bold,
    marginBottom: Spacing.sm,
  },
  infoPill: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.xs,
    borderRadius: BorderRadius.full,
    gap: Spacing.xs,
  },
  infoText: {
    fontSize: Typography.fontSize.xs,
  },
  indicatorContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: Spacing.md,
    gap: Spacing.xs,
  },
  indicatorTouchable: {
    padding: Spacing.xs,
  },
  indicator: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  carouselContainer: {
    flex: 1,
    position: 'relative',
  },
  navButton: {
    position: 'absolute',
    bottom: Spacing.xxl,
    width: 48,
    height: 48,
    borderRadius: 24,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 4,
    elevation: 4,
  },
  prevButton: {
    left: Spacing.md,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: Spacing.xxl * 2,
  },
  emptyText: {
    fontSize: Typography.fontSize.base,
    marginTop: Spacing.md,
  },
});
