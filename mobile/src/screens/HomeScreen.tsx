/**
 * Home Screen - Category-filtered news with ranking
 * Redesigned based on 뉴스홈.jpg reference
 */

import React, { useState, useEffect, useMemo, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
  Modal,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useNavigation } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';
import { useTheme } from '../contexts/ThemeContext';
import { useAuth } from '../contexts/AuthContext';
import { apiClient } from '../services/api';
import { TodayNewsResponse, NewsItem, RankedNewsItem } from '../types/api';
import { RootStackParamList } from '../types/navigation';
import { CategoryTabs, CategoryTab, CATEGORY_TABS } from '../components/CategoryTabs';
import { HorizontalNewsCard } from '../components/HorizontalNewsCard';
import { ErrorView } from '../components/ErrorView';
import { Spacing, Typography, BorderRadius } from '../constants/theme';
import { CATEGORIES, getCategoryByName } from '../constants/categories';

type NavigationProp = StackNavigationProp<RootStackParamList>;

type SortOption = 'trend' | 'latest';

// Format today's date: "2025.11.26"
const formatTodayDate = (): string => {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  return `${year}.${month}.${day}`;
};

// Map English category ID to Korean name
const getCategoryKoreanName = (categoryId: string): string => {
  const category = CATEGORIES.find((c) => c.id === categoryId);
  return category?.name || categoryId;
};

export const HomeScreen: React.FC = () => {
  const { colors } = useTheme();
  const { user } = useAuth();
  const navigation = useNavigation<NavigationProp>();

  const [selectedTab, setSelectedTab] = useState<CategoryTab>('종합');
  const [sortBy, setSortBy] = useState<SortOption>('trend');
  const [showSortModal, setShowSortModal] = useState(false);
  const [newsData, setNewsData] = useState<TodayNewsResponse>({});
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
      console.error('Failed to load news:', err);
      setError('뉴스를 불러오는데 실패했습니다. 다시 시도해주세요.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await loadNews();
    setIsRefreshing(false);
  };

  // Transform and filter news based on selected tab
  const filteredNews = useMemo((): RankedNewsItem[] => {
    const allNews: RankedNewsItem[] = [];

    // Convert API response to flat list with categoryName
    Object.entries(newsData).forEach(([categoryName, articles]) => {
      articles.forEach((article) => {
        allNews.push({
          ...article,
          categoryName,
        });
      });
    });

    let filtered: RankedNewsItem[] = [];

    switch (selectedTab) {
      case 'MY':
        // Filter by user's interests
        const userInterests = user?.interests || [];
        if (userInterests.length === 0) {
          // If no interests set, show empty or prompt
          filtered = [];
        } else {
          filtered = allNews.filter((item) =>
            userInterests.includes(item.categoryName)
          );
        }
        break;

      case '종합':
        // Get rank 1 news from each category
        const rank1News: RankedNewsItem[] = [];
        Object.entries(newsData).forEach(([categoryName, articles]) => {
          // Find rank 1 article (lowest rank number)
          const sortedArticles = [...articles].sort(
            (a, b) => (a.rank || 999) - (b.rank || 999)
          );
          if (sortedArticles.length > 0) {
            rank1News.push({
              ...sortedArticles[0],
              categoryName,
            });
          }
        });
        filtered = rank1News;
        break;

      default:
        // Filter by specific category
        filtered = allNews.filter((item) => item.categoryName === selectedTab);
        break;
    }

    // Sort based on sortBy option
    if (sortBy === 'trend') {
      filtered.sort((a, b) => (a.rank || 999) - (b.rank || 999));
    } else {
      filtered.sort(
        (a, b) =>
          new Date(b.published_at).getTime() - new Date(a.published_at).getTime()
      );
    }

    return filtered;
  }, [newsData, selectedTab, sortBy, user?.interests]);

  const handleNewsPress = useCallback(
    (item: RankedNewsItem) => {
      navigation.navigate('NewsDetail', {
        newsId: item.news_id,
        categoryName: item.categoryName,
        rank: item.rank,
      });
    },
    [navigation]
  );

  const handleSortSelect = (option: SortOption) => {
    setSortBy(option);
    setShowSortModal(false);
  };

  const renderNewsCard = useCallback(
    ({ item }: { item: RankedNewsItem }) => (
      <HorizontalNewsCard item={item} onPress={() => handleNewsPress(item)} />
    ),
    [handleNewsPress]
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
      {/* Category Tabs */}
      <CategoryTabs selectedTab={selectedTab} onTabChange={setSelectedTab} />

      {/* Sort Bar */}
      <View style={[styles.sortBar, { borderBottomColor: colors.border }]}>
        <TouchableOpacity
          style={styles.sortButton}
          onPress={() => setShowSortModal(true)}
        >
          <Text style={[styles.sortText, { color: colors.text }]}>
            {sortBy === 'trend' ? '트렌드순' : '최신순'}
          </Text>
          <Ionicons name="chevron-down" size={16} color={colors.text} />
        </TouchableOpacity>
        <Text style={[styles.dateText, { color: colors.textSecondary }]}>
          {formatTodayDate()}
        </Text>
      </View>

      {/* News List */}
      <FlatList
        data={filteredNews}
        renderItem={renderNewsCard}
        keyExtractor={keyExtractor}
        refreshControl={
          <RefreshControl
            refreshing={isRefreshing}
            onRefresh={handleRefresh}
            tintColor={colors.primary}
          />
        }
        showsVerticalScrollIndicator={false}
        ListEmptyComponent={
          <View style={styles.emptyState}>
            <Ionicons name="newspaper-outline" size={64} color={colors.textTertiary} />
            <Text style={[styles.emptyText, { color: colors.textSecondary }]}>
              {selectedTab === 'MY' && (!user?.interests || user.interests.length === 0)
                ? '관심 카테고리를 설정해주세요'
                : '표시할 뉴스가 없습니다'}
            </Text>
          </View>
        }
      />

      {/* Sort Modal */}
      <Modal
        visible={showSortModal}
        transparent
        animationType="fade"
        onRequestClose={() => setShowSortModal(false)}
      >
        <TouchableOpacity
          style={styles.modalOverlay}
          activeOpacity={1}
          onPress={() => setShowSortModal(false)}
        >
          <View
            style={[styles.modalContent, { backgroundColor: colors.card }]}
          >
            <TouchableOpacity
              style={[
                styles.modalOption,
                sortBy === 'trend' && { backgroundColor: colors.backgroundSecondary },
              ]}
              onPress={() => handleSortSelect('trend')}
            >
              <Text
                style={[
                  styles.modalOptionText,
                  { color: sortBy === 'trend' ? colors.primary : colors.text },
                ]}
              >
                트렌드순
              </Text>
              {sortBy === 'trend' && (
                <Ionicons name="checkmark" size={20} color={colors.primary} />
              )}
            </TouchableOpacity>
            <TouchableOpacity
              style={[
                styles.modalOption,
                sortBy === 'latest' && { backgroundColor: colors.backgroundSecondary },
              ]}
              onPress={() => handleSortSelect('latest')}
            >
              <Text
                style={[
                  styles.modalOptionText,
                  { color: sortBy === 'latest' ? colors.primary : colors.text },
                ]}
              >
                최신순
              </Text>
              {sortBy === 'latest' && (
                <Ionicons name="checkmark" size={20} color={colors.primary} />
              )}
            </TouchableOpacity>
          </View>
        </TouchableOpacity>
      </Modal>
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
  sortBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: Spacing.lg,
    paddingVertical: Spacing.sm,
    borderBottomWidth: 1,
  },
  sortButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.xs,
  },
  sortText: {
    fontSize: Typography.fontSize.sm,
    fontWeight: Typography.fontWeight.medium,
  },
  dateText: {
    fontSize: Typography.fontSize.sm,
  },
  emptyState: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: Spacing.xxl * 2,
  },
  emptyText: {
    fontSize: Typography.fontSize.base,
    marginTop: Spacing.md,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContent: {
    width: '80%',
    borderRadius: BorderRadius.lg,
    overflow: 'hidden',
  },
  modalOption: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: Spacing.md,
    paddingHorizontal: Spacing.lg,
  },
  modalOptionText: {
    fontSize: Typography.fontSize.base,
    fontWeight: Typography.fontWeight.medium,
  },
});
