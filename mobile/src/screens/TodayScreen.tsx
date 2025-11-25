/**
 * Today Screen - Category-grouped news
 * GET /api/news/today
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../contexts/ThemeContext';
import { apiClient } from '../services/api';
import { TodayNewsResponse, NewsItem } from '../types/api';
import { NewsImage } from '../components/NewsImage';
import { ErrorView } from '../components/ErrorView';
import { getCategoryById } from '../constants/categories';
import { Spacing, Typography, BorderRadius, Shadows } from '../constants/theme';

export const TodayScreen: React.FC = () => {
  const { colors } = useTheme();
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
    } catch (error) {
      console.error('Failed to load today news:', error);
      setError('오늘의 뉴스를 불러오는데 실패했습니다. 다시 시도해주세요.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await loadNews();
    setIsRefreshing(false);
  };

  const renderNewsItem = (news: NewsItem, isFirst: boolean) => (
    <TouchableOpacity
      key={news.news_id}
      style={[
        styles.newsCard,
        isFirst && styles.featuredCard,
        { backgroundColor: colors.card },
        Shadows.sm,
      ]}
      activeOpacity={0.7}
    >
      {isFirst && <NewsImage uri={news.images} style={styles.featuredImage} />}
      <View style={styles.newsContent}>
        <Text style={[styles.newsTitle, { color: colors.text }]} numberOfLines={isFirst ? 3 : 2}>
          {news.title}
        </Text>
        <Text style={[styles.newsPublisher, { color: colors.textSecondary }]}>
          {news.provider}
        </Text>
      </View>
    </TouchableOpacity>
  );

  if (isLoading) {
    return (
      <View style={[styles.centerContainer, { backgroundColor: colors.background }]}>
        <ActivityIndicator size="large" color={colors.primary} />
      </View>
    );
  }

  if (error) {
    return <ErrorView message={error} onRetry={loadNews} />;
  }

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: colors.background }]}>
      {/* Header */}
      <View style={[styles.header, { borderBottomColor: colors.border }]}>
        <Text style={[styles.headerTitle, { color: colors.text }]}>투데이</Text>
      </View>

      {/* Content */}
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        refreshControl={
          <RefreshControl
            refreshing={isRefreshing}
            onRefresh={handleRefresh}
            tintColor={colors.primary}
          />
        }
        showsVerticalScrollIndicator={false}
      >
        {Object.entries(newsData).map(([categoryId, articles]) => {
          const category = getCategoryById(categoryId);
          if (!category || articles.length === 0) return null;

          return (
            <View key={categoryId} style={styles.categorySection}>
              <View style={styles.categoryHeader}>
                <View style={styles.categoryTitleContainer}>
                  <Ionicons name={category.icon} size={24} color={category.color} />
                  <Text style={[styles.categoryName, { color: colors.text }]}>
                    {category.name}
                  </Text>
                </View>
                <TouchableOpacity>
                  <Text style={[styles.seeAll, { color: colors.primary }]}>더보기</Text>
                </TouchableOpacity>
              </View>

              {articles.slice(0, 6).map((article, index) => renderNewsItem(article, index === 0))}
            </View>
          );
        })}
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: {
    paddingHorizontal: Spacing.lg,
    paddingVertical: Spacing.md,
    borderBottomWidth: 1,
  },
  headerTitle: {
    fontSize: Typography.fontSize.xxl,
    fontWeight: Typography.fontWeight.bold,
  },
  scrollContent: {
    padding: Spacing.lg,
  },
  categorySection: {
    marginBottom: Spacing.xl,
  },
  categoryHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: Spacing.md,
  },
  categoryTitleContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  categoryName: {
    fontSize: Typography.fontSize.lg,
    fontWeight: Typography.fontWeight.bold,
    marginLeft: Spacing.sm,
  },
  seeAll: {
    fontSize: Typography.fontSize.sm,
    fontWeight: Typography.fontWeight.semibold,
  },
  newsCard: {
    borderRadius: BorderRadius.lg,
    marginBottom: Spacing.md,
    overflow: 'hidden',
  },
  featuredCard: {
    marginBottom: Spacing.lg,
  },
  featuredImage: {
    width: '100%',
    borderTopLeftRadius: BorderRadius.lg,
    borderTopRightRadius: BorderRadius.lg,
  },
  newsContent: {
    padding: Spacing.md,
  },
  newsTitle: {
    fontSize: Typography.fontSize.base,
    fontWeight: Typography.fontWeight.semibold,
    marginBottom: Spacing.xs,
    lineHeight: Typography.fontSize.base * Typography.lineHeight.normal,
  },
  newsPublisher: {
    fontSize: Typography.fontSize.sm,
  },
});
