/**
 * HeadlineCard - Card component for Today's Briefing Headlines
 * Full-screen swipeable card with headline, summary, and detail link
 */

import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Dimensions,
  Linking,
  ScrollView,
} from 'react-native';
import { useTheme } from '../contexts/ThemeContext';
import { HeadlineItem } from '../types/api';
import { NewsImage } from './NewsImage';
import { Spacing, Typography, BorderRadius } from '../constants/theme';

const { width: SCREEN_WIDTH } = Dimensions.get('window');
const CARD_HORIZONTAL_MARGIN = Spacing.lg;

interface HeadlineCardProps {
  item: HeadlineItem;
  index: number;
}

export const HeadlineCard: React.FC<HeadlineCardProps> = ({ item, index }) => {
  const { colors } = useTheme();

  // v2 backend는 대표 기사의 원문 링크를 직접 제공하지 않으므로
  // "자세히 보기" 동작은 추후 토픽 상세 화면 또는 클러스터 기사 목록으로 확장
  const handleDetailPress = () => {
    // TODO: 토픽 상세 뷰 네비게이션 (추후 구현)
    console.log('topic detail:', item.topic_id, item.headline);
  };

  // 카테고리 배지 텍스트
  const categoryLabel = item.category_ko || '뉴스';

  return (
    <View style={[styles.cardContainer, { width: SCREEN_WIDTH }]}>
      <View style={[styles.card, { backgroundColor: colors.card }]}>
        <ScrollView
          showsVerticalScrollIndicator={false}
          contentContainerStyle={styles.scrollContent}
        >
          {/* Category Badge + Article Count */}
          <View style={styles.badgeRow}>
            <View style={[styles.categoryBadge, { backgroundColor: colors.primary }]}>
              <Text style={styles.categoryText}>{categoryLabel}</Text>
            </View>
            <View style={[styles.countBadge, { backgroundColor: colors.backgroundSecondary }]}>
              <Text style={[styles.countText, { color: colors.textSecondary }]}>
                {item.cluster_size}개 기사
              </Text>
            </View>
          </View>

          {/* Headline (Gemma4 로컬 생성) */}
          <Text style={[styles.headline, { color: colors.text }]} numberOfLines={3}>
            {item.headline}
          </Text>

          {/* Divider */}
          <View style={[styles.divider, { backgroundColor: colors.border }]} />

          {/* Summary (Gemma4 생성, ~요/~해요 체) */}
          <Text style={[styles.summary, { color: colors.text }]}>
            {item.summary}
          </Text>

          {/* Representative Article Image */}
          {item.representative_image && (
            <NewsImage
              uri={item.representative_image}
              style={styles.image}
            />
          )}

          {/* Representative Article Title + Press */}
          {item.representative_title && (
            <Text
              style={[styles.repTitle, { color: colors.textSecondary }]}
              numberOfLines={2}
            >
              {item.representative_title}
            </Text>
          )}
          {item.representative_press && (
            <Text style={[styles.providerText, { color: colors.textTertiary }]}>
              {item.representative_press}
            </Text>
          )}

          {/* Detail Button */}
          <TouchableOpacity
            style={[styles.detailButton, { backgroundColor: colors.primary }]}
            onPress={handleDetailPress}
            activeOpacity={0.8}
          >
            <Text style={styles.detailButtonText}>자세히 보기</Text>
          </TouchableOpacity>
        </ScrollView>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  cardContainer: {
    paddingHorizontal: CARD_HORIZONTAL_MARGIN,
    paddingBottom: Spacing.lg,
  },
  card: {
    flex: 1,
    borderRadius: BorderRadius.xl,
    padding: Spacing.lg,
  },
  scrollContent: {
    paddingBottom: Spacing.md,
  },
  badgeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.sm,
    marginBottom: Spacing.md,
  },
  categoryBadge: {
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.xs,
    borderRadius: BorderRadius.full,
  },
  categoryText: {
    color: '#FFFFFF',
    fontSize: Typography.fontSize.sm,
    fontWeight: Typography.fontWeight.semibold,
  },
  countBadge: {
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.xs,
    borderRadius: BorderRadius.full,
  },
  countText: {
    fontSize: Typography.fontSize.sm,
  },
  headline: {
    fontSize: Typography.fontSize.xxl,
    fontWeight: Typography.fontWeight.bold,
    lineHeight: Typography.fontSize.xxl * Typography.lineHeight.tight,
    marginBottom: Spacing.sm,
  },
  divider: {
    height: 1,
    marginVertical: Spacing.md,
  },
  summary: {
    fontSize: Typography.fontSize.base,
    lineHeight: Typography.fontSize.base * Typography.lineHeight.relaxed,
    marginBottom: Spacing.lg,
  },
  image: {
    width: '100%',
    height: 200,
    borderRadius: BorderRadius.lg,
    marginBottom: Spacing.md,
  },
  repTitle: {
    fontSize: Typography.fontSize.sm,
    fontWeight: Typography.fontWeight.medium,
    lineHeight: Typography.fontSize.sm * Typography.lineHeight.normal,
    marginBottom: Spacing.xs,
  },
  providerText: {
    fontSize: Typography.fontSize.sm,
    marginBottom: Spacing.lg,
  },
  detailButton: {
    paddingVertical: Spacing.md,
    borderRadius: BorderRadius.lg,
    alignItems: 'center',
  },
  detailButtonText: {
    color: '#FFFFFF',
    fontSize: Typography.fontSize.base,
    fontWeight: Typography.fontWeight.semibold,
  },
});
