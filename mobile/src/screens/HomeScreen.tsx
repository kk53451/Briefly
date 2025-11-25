/**
 * Home Screen - Provider-grouped latest news
 * Similar to frontend /home route (GET /api/news/home)
 */

import React, { useState, useEffect, useMemo, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  SectionList,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../contexts/ThemeContext';
import { apiClient } from '../services/api';
import { HomeNewsResponse, NewsItem } from '../types/api';
import { NewsImage } from '../components/NewsImage';
import { ErrorView } from '../components/ErrorView';
import { Spacing, Typography, BorderRadius, Shadows } from '../constants/theme';

export const HomeScreen: React.FC = () => {
  const { colors, activeTheme } = useTheme();
  const [newsData, setNewsData] = useState<HomeNewsResponse>({});
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
      const data = await apiClient.getHomeNews();
      setNewsData(data);
    } catch (error) {
      console.error('Failed to load home news:', error);
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

  // Convert object to sections for SectionList
  const sections = useMemo(
    () =>
      Object.entries(newsData).map(([provider, articles]) => ({
        title: provider,
        data: articles.slice(0, 6),
      })),
    [newsData]
  );

  const renderNewsCard = useCallback(
    ({ item }: { item: NewsItem }) => (
      <TouchableOpacity
        style={[styles.newsCard, { backgroundColor: colors.card }, Shadows.sm]}
        activeOpacity={0.7}
      >
        <NewsImage uri={item.images} style={styles.newsImage} />
        <View style={styles.newsContent}>
          <Text style={[styles.newsTitle, { color: colors.text }]} numberOfLines={2}>
            {item.title}
          </Text>
          <Text style={[styles.newsProvider, { color: colors.textSecondary }]}>
            {item.provider}
          </Text>
        </View>
      </TouchableOpacity>
    ),
    [colors]
  );

  const renderSectionHeader = useCallback(
    ({ section }: { section: { title: string } }) => (
      <Text style={[styles.providerName, { color: colors.text }]}>{section.title}</Text>
    ),
    [colors]
  );

  const keyExtractor = useCallback((item: NewsItem) => item.news_id, []);

  const logoUrl =
    activeTheme === 'dark'
      ? process.env.EXPO_PUBLIC_LOGO_DARK_URL
      : process.env.EXPO_PUBLIC_LOGO_LIGHT_URL;

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
        <Text style={[styles.headerTitle, { color: colors.text }]}>홈</Text>
        <TouchableOpacity>
          <Ionicons name="search" size={24} color={colors.text} />
        </TouchableOpacity>
      </View>

      {/* Content */}
      <SectionList
        sections={sections}
        renderItem={renderNewsCard}
        renderSectionHeader={renderSectionHeader}
        keyExtractor={keyExtractor}
        contentContainerStyle={styles.scrollContent}
        refreshControl={
          <RefreshControl
            refreshing={isRefreshing}
            onRefresh={handleRefresh}
            tintColor={colors.primary}
          />
        }
        showsVerticalScrollIndicator={false}
        stickySectionHeadersEnabled={false}
        ListEmptyComponent={
          <View style={styles.emptyState}>
            <Ionicons name="newspaper-outline" size={64} color={colors.textTertiary} />
            <Text style={[styles.emptyText, { color: colors.textSecondary }]}>
              표시할 뉴스가 없습니다
            </Text>
          </View>
        }
      />
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
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
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
  providerSection: {
    marginBottom: Spacing.xl,
  },
  providerName: {
    fontSize: Typography.fontSize.lg,
    fontWeight: Typography.fontWeight.bold,
    marginBottom: Spacing.md,
  },
  newsCard: {
    borderRadius: BorderRadius.lg,
    marginBottom: Spacing.md,
    overflow: 'hidden',
  },
  newsImage: {
    width: '100%',
    borderRadius: BorderRadius.lg,
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
  newsProvider: {
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
});
