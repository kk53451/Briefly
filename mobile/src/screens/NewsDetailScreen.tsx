/**
 * NewsDetailScreen - News article detail view
 * Shows full article content from BigKinds API
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Image,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useNavigation, useRoute, RouteProp } from '@react-navigation/native';
import { useTheme } from '../contexts/ThemeContext';
import { apiClient } from '../services/api';
import type { NewsItem } from '../types/api';
import { NewsStackParamList } from '../types/navigation';
import { Spacing, Typography, BorderRadius } from '../constants/theme';

type NewsDetailRouteProp = RouteProp<NewsStackParamList, 'NewsDetail'>;

// Format date: "2025.11.25. 화요일 오후"
const formatDetailDate = (dateString: string): string => {
  try {
    const date = new Date(dateString);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');

    const weekdays = ['일요일', '월요일', '화요일', '수요일', '목요일', '금요일', '토요일'];
    const weekday = weekdays[date.getDay()];

    const hours = date.getHours();
    const period = hours < 12 ? '오전' : '오후';

    return `${year}.${month}.${day}. ${weekday} ${period}`;
  } catch {
    return dateString;
  }
};

export const NewsDetailScreen: React.FC = () => {
  const { colors } = useTheme();
  const navigation = useNavigation();
  const route = useRoute<NewsDetailRouteProp>();
  const { newsId, categoryName, rank } = route.params;

  const [newsDetail, setNewsDetail] = useState<NewsItem | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadNewsDetail();
  }, [newsId]);

  const loadNewsDetail = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await apiClient.getNewsDetail(newsId);
      setNewsDetail(data);
    } catch (err) {
      console.error('Failed to load news detail:', err);
      setError('뉴스를 불러오는데 실패했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoBack = () => {
    navigation.goBack();
  };

  if (isLoading) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: colors.background }]}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={colors.primary} />
        </View>
      </SafeAreaView>
    );
  }

  if (error || !newsDetail) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: colors.background }]}>
        <View style={styles.header}>
          <TouchableOpacity onPress={handleGoBack} style={styles.backButton}>
            <Ionicons name="chevron-back" size={24} color={colors.text} />
          </TouchableOpacity>
        </View>
        <View style={styles.errorContainer}>
          <Ionicons name="alert-circle-outline" size={48} color={colors.textTertiary} />
          <Text style={[styles.errorText, { color: colors.textSecondary }]}>
            {error || '뉴스를 찾을 수 없습니다.'}
          </Text>
          <TouchableOpacity
            style={[styles.retryButton, { backgroundColor: colors.primary }]}
            onPress={loadNewsDetail}
          >
            <Text style={styles.retryButtonText}>다시 시도</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  const rankLabel = categoryName;

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: colors.background }]}>
      {/* Header */}
      <View style={[styles.header, { borderBottomColor: colors.border }]}>
        <TouchableOpacity onPress={handleGoBack} style={styles.backButton}>
          <Ionicons name="chevron-back" size={24} color={colors.text} />
        </TouchableOpacity>
      </View>

      <ScrollView
        style={styles.scrollView}
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.scrollContent}
      >
        {/* Category Badge */}
        <View style={[styles.badge, { backgroundColor: colors.primary }]}>
          <Text style={styles.badgeText}>{rankLabel}</Text>
        </View>

        {/* Title */}
        <Text style={[styles.title, { color: colors.text }]}>
          {newsDetail.title}
        </Text>

        {/* Date */}
        <Text style={[styles.date, { color: colors.textSecondary }]}>
          {formatDetailDate(newsDetail.published_at)}
        </Text>

        {/* Main Image */}
        <View style={styles.imageContainer}>
          {newsDetail.images ? (
            <Image
              source={{ uri: newsDetail.images }}
              style={styles.mainImage}
              resizeMode="cover"
            />
          ) : (
            <LinearGradient
              colors={[colors.backgroundSecondary, colors.border]}
              style={styles.mainImage}
            >
              <Ionicons
                name="newspaper-outline"
                size={48}
                color={colors.textTertiary}
              />
            </LinearGradient>
          )}
        </View>

        {/* Content Section */}
        <View style={styles.contentSection}>
          <View style={[styles.contentBar, { backgroundColor: colors.primary }]} />
          <View style={styles.contentTextContainer}>
            <Text style={[styles.contentLabel, { color: colors.textSecondary }]}>
              요약
            </Text>
            <Text style={[styles.content, { color: colors.text }]}>
              {newsDetail.hilight || '요약 내용이 없습니다.'}
            </Text>
          </View>
        </View>

        {/* Provider Info */}
        <View style={[styles.providerInfo, { borderTopColor: colors.border }]}>
          <Text style={[styles.providerText, { color: colors.textSecondary }]}>
            {newsDetail.provider}
            {newsDetail.byline && ` · ${newsDetail.byline}`}
          </Text>
        </View>
      </ScrollView>

      {/* Bottom CTA Button */}
      <View style={[styles.bottomContainer, { borderTopColor: colors.border }]}>
        <TouchableOpacity
          style={[styles.ctaButton, { backgroundColor: colors.primary }]}
          onPress={handleGoBack}
          activeOpacity={0.8}
        >
          <Text style={styles.ctaButtonText}>목록으로 돌아가기</Text>
        </TouchableOpacity>
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
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: Spacing.xl,
  },
  errorText: {
    fontSize: Typography.fontSize.base,
    marginTop: Spacing.md,
    marginBottom: Spacing.lg,
    textAlign: 'center',
  },
  retryButton: {
    paddingHorizontal: Spacing.lg,
    paddingVertical: Spacing.sm,
    borderRadius: BorderRadius.md,
  },
  retryButtonText: {
    color: '#FFFFFF',
    fontSize: Typography.fontSize.sm,
    fontWeight: Typography.fontWeight.semibold,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.sm,
    borderBottomWidth: 1,
  },
  backButton: {
    padding: Spacing.xs,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: Spacing.lg,
    paddingBottom: Spacing.xxl,
  },
  badge: {
    alignSelf: 'flex-start',
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.sm,
    borderRadius: BorderRadius.md,
    marginBottom: Spacing.md,
  },
  badgeText: {
    color: '#FFFFFF',
    fontSize: Typography.fontSize.sm,
    fontWeight: Typography.fontWeight.semibold,
  },
  title: {
    fontSize: Typography.fontSize.xxl,
    fontWeight: Typography.fontWeight.bold,
    lineHeight: Typography.fontSize.xxl * Typography.lineHeight.normal,
    marginBottom: Spacing.sm,
  },
  date: {
    fontSize: Typography.fontSize.sm,
    marginBottom: Spacing.lg,
  },
  imageContainer: {
    width: '100%',
    aspectRatio: 16 / 9,
    borderRadius: BorderRadius.lg,
    overflow: 'hidden',
    marginBottom: Spacing.lg,
  },
  mainImage: {
    width: '100%',
    height: '100%',
    justifyContent: 'center',
    alignItems: 'center',
  },
  contentSection: {
    flexDirection: 'row',
    marginBottom: Spacing.lg,
  },
  contentBar: {
    width: 4,
    borderRadius: 2,
    marginRight: Spacing.md,
  },
  contentTextContainer: {
    flex: 1,
  },
  contentLabel: {
    fontSize: Typography.fontSize.sm,
    fontWeight: Typography.fontWeight.medium,
    marginBottom: Spacing.sm,
  },
  content: {
    fontSize: Typography.fontSize.base,
    lineHeight: Typography.fontSize.base * Typography.lineHeight.relaxed,
  },
  providerInfo: {
    paddingTop: Spacing.md,
    borderTopWidth: 1,
  },
  providerText: {
    fontSize: Typography.fontSize.sm,
  },
  bottomContainer: {
    padding: Spacing.lg,
    borderTopWidth: 1,
  },
  ctaButton: {
    paddingVertical: Spacing.md,
    borderRadius: BorderRadius.lg,
    alignItems: 'center',
  },
  ctaButtonText: {
    color: '#FFFFFF',
    fontSize: Typography.fontSize.base,
    fontWeight: Typography.fontWeight.semibold,
  },
});
