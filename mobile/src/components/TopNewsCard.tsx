/**
 * TopNewsCard - Card component for Today Screen's Daily TOP 10
 * Full-screen swipeable card with rank badge, title, image, content preview
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
import { RankedNewsItem } from '../types/api';
import { NewsImage } from './NewsImage';
import { Spacing, Typography, BorderRadius } from '../constants/theme';

const { width: SCREEN_WIDTH } = Dimensions.get('window');
const CARD_HORIZONTAL_MARGIN = Spacing.lg;
const CARD_WIDTH = SCREEN_WIDTH - CARD_HORIZONTAL_MARGIN * 2;

interface TopNewsCardProps {
  item: RankedNewsItem;
  rank: number;
}

export const TopNewsCard: React.FC<TopNewsCardProps> = ({ item, rank }) => {
  const { colors } = useTheme();

  const handleDetailPress = async () => {
    if (item.provider_link_page) {
      try {
        await Linking.openURL(item.provider_link_page);
      } catch (error) {
        console.error('Failed to open URL:', error);
      }
    }
  };

  // Get content preview (first 200 characters)
  const contentPreview = item.content
    ? item.content.slice(0, 200) + (item.content.length > 200 ? '...' : '')
    : item.hilight || '';

  return (
    <View style={[styles.cardContainer, { width: SCREEN_WIDTH }]}>
      <View style={[styles.card, { backgroundColor: colors.card }]}>
        <ScrollView
          showsVerticalScrollIndicator={false}
          contentContainerStyle={styles.scrollContent}
        >
          {/* Rank Badge */}
          <View style={[styles.rankBadge, { backgroundColor: colors.backgroundSecondary }]}>
            <Text style={[styles.rankText, { color: colors.text }]}>
              {rank}위
            </Text>
          </View>

          {/* Title */}
          <Text style={[styles.title, { color: colors.text }]} numberOfLines={2}>
            {item.title}
          </Text>

          {/* Divider */}
          <View style={[styles.divider, { backgroundColor: colors.border }]} />

          {/* Subtitle/Hilight */}
          {item.hilight && (
            <Text style={[styles.subtitle, { color: colors.textSecondary }]} numberOfLines={2}>
              {item.hilight}
            </Text>
          )}

          {/* Image */}
          {item.images && (
            <NewsImage
              uri={item.images}
              style={styles.image}
            />
          )}

          {/* Content Preview */}
          {contentPreview && (
            <Text style={[styles.contentPreview, { color: colors.textSecondary }]}>
              {contentPreview}
            </Text>
          )}

          {/* Detail Button */}
          <TouchableOpacity
            style={[styles.detailButton, { backgroundColor: colors.primary }]}
            onPress={handleDetailPress}
            activeOpacity={0.8}
          >
            <Text style={styles.detailButtonText}>기사 상세 보기</Text>
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
  rankBadge: {
    alignSelf: 'flex-start',
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.xs,
    borderRadius: BorderRadius.full,
    marginBottom: Spacing.md,
  },
  rankText: {
    fontSize: Typography.fontSize.lg,
    fontWeight: Typography.fontWeight.bold,
  },
  title: {
    fontSize: Typography.fontSize.xxl,
    fontWeight: Typography.fontWeight.bold,
    lineHeight: Typography.fontSize.xxl * Typography.lineHeight.tight,
    marginBottom: Spacing.sm,
  },
  divider: {
    height: 1,
    marginVertical: Spacing.md,
  },
  subtitle: {
    fontSize: Typography.fontSize.base,
    lineHeight: Typography.fontSize.base * Typography.lineHeight.normal,
    marginBottom: Spacing.md,
  },
  image: {
    width: '100%',
    height: 200,
    borderRadius: BorderRadius.lg,
    marginBottom: Spacing.md,
  },
  contentPreview: {
    fontSize: Typography.fontSize.base,
    lineHeight: Typography.fontSize.base * Typography.lineHeight.relaxed,
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
