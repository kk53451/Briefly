/**
 * HorizontalNewsCard - Horizontal layout news card
 * Left: Category badge, title, date
 * Right: Thumbnail image
 */

import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Image,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../contexts/ThemeContext';
import { Spacing, Typography, BorderRadius } from '../constants/theme';
import { NewsItem } from '../types/api';
import { getCategoryByName } from '../constants/categories';

interface HorizontalNewsCardProps {
  item: NewsItem & { categoryName: string };
  onPress: () => void;
}

// Format date: "2025.11.25. 00:58"
const formatDate = (dateString: string): string => {
  try {
    const date = new Date(dateString);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${year}.${month}.${day}. ${hours}:${minutes}`;
  } catch {
    return dateString;
  }
};

export const HorizontalNewsCard: React.FC<HorizontalNewsCardProps> = ({
  item,
  onPress,
}) => {
  const { colors } = useTheme();
  const category = getCategoryByName(item.categoryName);
  const rankLabel = `${item.categoryName} ${item.rank}위`;

  return (
    <TouchableOpacity
      style={[styles.container, { borderBottomColor: colors.border }]}
      onPress={onPress}
      activeOpacity={0.7}
    >
      {/* Left: Text content */}
      <View style={styles.textContent}>
        {/* Category rank badge */}
        <View style={[styles.badge, { backgroundColor: colors.primary }]}>
          <Text style={styles.badgeText}>{rankLabel}</Text>
        </View>

        {/* Title */}
        <Text
          style={[styles.title, { color: colors.text }]}
          numberOfLines={2}
        >
          {item.title}
        </Text>

        {/* Date */}
        <Text style={[styles.date, { color: colors.textSecondary }]}>
          {formatDate(item.published_at)}
        </Text>
      </View>

      {/* Right: Thumbnail */}
      <View style={styles.thumbnailContainer}>
        {item.images ? (
          <Image
            source={{ uri: item.images }}
            style={styles.thumbnail}
            resizeMode="cover"
          />
        ) : (
          <LinearGradient
            colors={[colors.backgroundSecondary, colors.border]}
            style={styles.thumbnail}
          >
            <Ionicons
              name="newspaper-outline"
              size={24}
              color={colors.textTertiary}
            />
          </LinearGradient>
        )}
      </View>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    paddingVertical: Spacing.md,
    paddingHorizontal: Spacing.lg,
    borderBottomWidth: 1,
  },
  textContent: {
    flex: 1,
    paddingRight: Spacing.md,
    justifyContent: 'center',
  },
  badge: {
    alignSelf: 'flex-start',
    paddingHorizontal: Spacing.sm,
    paddingVertical: Spacing.xs,
    borderRadius: BorderRadius.sm,
    marginBottom: Spacing.sm,
  },
  badgeText: {
    color: '#FFFFFF',
    fontSize: Typography.fontSize.xs,
    fontWeight: Typography.fontWeight.semibold,
  },
  title: {
    fontSize: Typography.fontSize.base,
    fontWeight: Typography.fontWeight.semibold,
    lineHeight: Typography.fontSize.base * Typography.lineHeight.normal,
    marginBottom: Spacing.xs,
  },
  date: {
    fontSize: Typography.fontSize.sm,
  },
  thumbnailContainer: {
    width: 100,
    height: 75,
    borderRadius: BorderRadius.md,
    overflow: 'hidden',
  },
  thumbnail: {
    width: '100%',
    height: '100%',
    justifyContent: 'center',
    alignItems: 'center',
  },
});
