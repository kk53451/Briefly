import React, { useState } from 'react';
import {
  View,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { Text, Button, Chip, useTheme } from 'react-native-paper';
import { SafeAreaView } from 'react-native-safe-area-context';
import { AuthStackScreenProps } from '../../navigation/types';
import { userService } from '../../lib/api/services';
import { useAuthStore } from '../../store/authStore';
import { CATEGORIES, CategoryColors } from '../../lib/constants/categories';
import { Typography, Spacing, BorderRadius, Dimensions, FontSizes } from '../../lib/theme';

export default function OnboardingScreen({ navigation }: AuthStackScreenProps<'Onboarding'>) {
  const theme = useTheme();
  const { updateUser } = useAuthStore();
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const toggleCategory = (category: string) => {
    setSelectedCategories(prev => {
      if (prev.includes(category)) {
        return prev.filter(c => c !== category);
      } else {
        return [...prev, category];
      }
    });
  };

  const handleComplete = async () => {
    if (selectedCategories.length < 3) {
      Alert.alert('카테고리 선택', '최소 3개 이상의 카테고리를 선택해주세요.');
      return;
    }

    try {
      setIsLoading(true);

      // Complete onboarding with selected categories
      const response = await userService.completeOnboarding({
        interests: selectedCategories,
      });

      // Update user in store
      updateUser(response.user);

      // Navigation will be handled by RootNavigator automatically
    } catch (error) {
      console.error('Onboarding error:', error);
      Alert.alert('오류', '온보딩 처리 중 오류가 발생했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={[styles.title, { color: theme.colors.textPrimary }]}>
            관심 카테고리를 선택해주세요
          </Text>
          <Text style={[styles.subtitle, { color: theme.colors.textSecondary }]}>
            선택하신 카테고리의 뉴스를 매일 아침{'\n'}
            AI가 요약해서 들려드립니다
          </Text>
          <Text style={[styles.hint, { color: theme.colors.textTertiary }]}>
            최소 3개 이상 선택
          </Text>
        </View>

        {/* Category Grid */}
        <View style={styles.categoryGrid}>
          {CATEGORIES.map(category => {
            const isSelected = selectedCategories.includes(category.korean);
            const categoryColor = CategoryColors[category.english];

            return (
              <TouchableOpacity
                key={category.english}
                onPress={() => toggleCategory(category.korean)}
                style={[
                  styles.categoryCard,
                  {
                    backgroundColor: isSelected ? categoryColor + '20' : theme.colors.surface,
                    borderColor: isSelected ? categoryColor : theme.colors.outline,
                    borderWidth: isSelected ? 2 : 1,
                  },
                ]}
              >
                <View
                  style={[
                    styles.categoryColorDot,
                    { backgroundColor: categoryColor }
                  ]}
                />
                <Text
                  style={[
                    styles.categoryName,
                    {
                      color: isSelected ? categoryColor : theme.colors.textSecondary,
                      fontWeight: isSelected ? '700' : '400',
                    },
                  ]}
                >
                  {category.korean}
                </Text>
              </TouchableOpacity>
            );
          })}
        </View>

        {/* Selected Count */}
        <View style={styles.countSection}>
          <Text style={[styles.countText, { color: theme.colors.textSecondary }]}>
            선택된 카테고리: {' '}
            <Text style={{ color: theme.colors.primary, fontWeight: '700' }}>
              {selectedCategories.length}개
            </Text>
          </Text>
        </View>
      </ScrollView>

      {/* Bottom Button */}
      <View style={[styles.bottomSection, { backgroundColor: theme.colors.background }]}>
        <Button
          mode="contained"
          onPress={handleComplete}
          loading={isLoading}
          disabled={isLoading || selectedCategories.length < 3}
          style={styles.completeButton}
          contentStyle={styles.completeButtonContent}
          labelStyle={styles.completeButtonLabel}
        >
          시작하기
        </Button>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollContent: {
    padding: Spacing.lg,
    paddingBottom: 100,
  },
  header: {
    marginBottom: Spacing.xl,
  },
  title: {
    ...Typography.h2,
    marginBottom: Spacing.sm,
  },
  subtitle: {
    ...Typography.body,
    lineHeight: 22,
    marginBottom: Spacing.sm,
  },
  hint: {
    ...Typography.caption,
  },
  categoryGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginHorizontal: -Spacing.xs,
  },
  categoryCard: {
    width: '47%',
    marginHorizontal: '1.5%',
    marginBottom: Spacing.md,
    paddingVertical: Spacing.lg,
    paddingHorizontal: Spacing.md,
    borderRadius: BorderRadius.card,
    flexDirection: 'row',
    alignItems: 'center',
  },
  categoryColorDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: Spacing.sm,
  },
  categoryName: {
    fontSize: FontSizes.base,
    fontFamily: 'Pretendard-Regular',
  },
  countSection: {
    marginTop: Spacing.lg,
    alignItems: 'center',
  },
  countText: {
    ...Typography.body,
  },
  bottomSection: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    paddingHorizontal: Spacing.lg,
    paddingVertical: Spacing.md,
    paddingBottom: Spacing.xl,
    borderTopWidth: 1,
    borderTopColor: '#E2E8F0',
  },
  completeButton: {
    borderRadius: BorderRadius.button,
  },
  completeButtonContent: {
    height: 52,
  },
  completeButtonLabel: {
    ...Typography.button,
    fontSize: 16,
  },
});