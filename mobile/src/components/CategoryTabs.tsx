/**
 * CategoryTabs - Horizontal scrollable category tab bar
 * Used in HomeScreen for filtering news by category
 */

import React from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
} from 'react-native';
import { useTheme } from '../contexts/ThemeContext';
import { Spacing, Typography, BorderRadius } from '../constants/theme';

export const CATEGORY_TABS = [
  'MY',
  '종합',
  '정치',
  '경제',
  '사회',
  '문화',
  '국제',
  '지역',
  '스포츠',
  'IT/과학',
] as const;

export type CategoryTab = (typeof CATEGORY_TABS)[number];

interface CategoryTabsProps {
  selectedTab: CategoryTab;
  onTabChange: (tab: CategoryTab) => void;
}

export const CategoryTabs: React.FC<CategoryTabsProps> = ({
  selectedTab,
  onTabChange,
}) => {
  const { colors } = useTheme();

  return (
    <View style={styles.container}>
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.scrollContent}
      >
        {CATEGORY_TABS.map((tab) => {
          const isSelected = tab === selectedTab;
          return (
            <TouchableOpacity
              key={tab}
              style={[
                styles.tab,
                isSelected && {
                  backgroundColor: colors.text,
                },
              ]}
              onPress={() => onTabChange(tab)}
              activeOpacity={0.7}
            >
              <Text
                style={[
                  styles.tabText,
                  {
                    color: isSelected ? colors.background : colors.textSecondary,
                    fontWeight: isSelected
                      ? Typography.fontWeight.semibold
                      : Typography.fontWeight.regular,
                  },
                ]}
              >
                {tab}
              </Text>
            </TouchableOpacity>
          );
        })}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    paddingVertical: Spacing.sm,
  },
  scrollContent: {
    paddingHorizontal: Spacing.md,
    gap: Spacing.sm,
  },
  tab: {
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.sm,
    borderRadius: BorderRadius.full,
  },
  tabText: {
    fontSize: Typography.fontSize.sm,
  },
});
