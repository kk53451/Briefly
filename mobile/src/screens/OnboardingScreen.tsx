/**
 * Onboarding Screen for category selection
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import { apiClient } from '../services/api';
import { CATEGORIES } from '../constants/categories';
import { Spacing, Typography, BorderRadius, Shadows } from '../constants/theme';

export const OnboardingScreen: React.FC = () => {
  const { colors } = useTheme();
  const { refreshUser } = useAuth();
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const toggleCategory = (categoryName: string) => {
    if (selectedCategories.includes(categoryName)) {
      setSelectedCategories(selectedCategories.filter((c) => c !== categoryName));
    } else {
      setSelectedCategories([...selectedCategories, categoryName]);
    }
  };

  const handleComplete = async () => {
    if (selectedCategories.length === 0) {
      Alert.alert('카테고리 선택', '최소 1개 이상의 관심 카테고리를 선택해주세요.');
      return;
    }

    try {
      setIsLoading(true);

      // Update user interests
      await apiClient.updateUserCategories(selectedCategories);

      // Mark onboarding as complete
      await apiClient.completeOnboarding();

      // Refresh user data
      await refreshUser();
    } catch (error) {
      console.error('Onboarding error:', error);
      Alert.alert('오류', '설정을 저장하는데 실패했습니다. 다시 시도해주세요.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: colors.background }]}>
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* Header */}
        <View style={styles.header}>
          <Text style={[styles.title, { color: colors.text }]}>
            관심있는 뉴스 카테고리를{'\n'}선택해주세요
          </Text>
          <Text style={[styles.subtitle, { color: colors.textSecondary }]}>
            선택하신 카테고리를 기반으로{'\n'}맞춤형 뉴스와 팟캐스트를 제공합니다
          </Text>
        </View>

        {/* Category Grid */}
        <View style={styles.grid}>
          {CATEGORIES.map((category) => {
            const isSelected = selectedCategories.includes(category.name);

            return (
              <TouchableOpacity
                key={category.id}
                style={[
                  styles.categoryCard,
                  {
                    backgroundColor: isSelected ? colors.primary : colors.card,
                    borderColor: isSelected ? colors.primary : colors.border,
                  },
                  Shadows.md,
                ]}
                onPress={() => toggleCategory(category.name)}
                activeOpacity={0.7}
              >
                <View
                  style={[
                    styles.iconContainer,
                    {
                      backgroundColor: isSelected
                        ? 'rgba(255,255,255,0.2)'
                        : colors.backgroundSecondary,
                    },
                  ]}
                >
                  <Ionicons
                    name={category.icon}
                    size={32}
                    color={isSelected ? '#FFFFFF' : category.color}
                  />
                </View>

                <Text
                  style={[
                    styles.categoryName,
                    { color: isSelected ? '#FFFFFF' : colors.text },
                  ]}
                >
                  {category.name}
                </Text>

                {isSelected && (
                  <View style={styles.checkmark}>
                    <Ionicons name="checkmark-circle" size={24} color="#FFFFFF" />
                  </View>
                )}
              </TouchableOpacity>
            );
          })}
        </View>

        {/* Selected Count */}
        <Text style={[styles.selectedCount, { color: colors.textSecondary }]}>
          {selectedCategories.length}개 선택됨
        </Text>
      </ScrollView>

      {/* Bottom Button */}
      <View style={[styles.bottomContainer, { backgroundColor: colors.background }]}>
        <TouchableOpacity
          style={[
            styles.completeButton,
            {
              backgroundColor: selectedCategories.length > 0 ? colors.primary : colors.border,
            },
          ]}
          onPress={handleComplete}
          disabled={isLoading || selectedCategories.length === 0}
          activeOpacity={0.8}
        >
          {isLoading ? (
            <ActivityIndicator color="#FFFFFF" />
          ) : (
            <Text style={styles.completeButtonText}>
              {selectedCategories.length > 0 ? '시작하기' : '카테고리를 선택해주세요'}
            </Text>
          )}
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollContent: {
    padding: Spacing.lg,
  },
  header: {
    marginBottom: Spacing.xl,
  },
  title: {
    fontSize: Typography.fontSize.xxl,
    fontWeight: Typography.fontWeight.bold,
    marginBottom: Spacing.md,
    lineHeight: Typography.fontSize.xxl * Typography.lineHeight.tight,
  },
  subtitle: {
    fontSize: Typography.fontSize.base,
    lineHeight: Typography.fontSize.base * Typography.lineHeight.normal,
  },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginHorizontal: -Spacing.sm,
  },
  categoryCard: {
    width: '50%',
    aspectRatio: 1,
    padding: Spacing.md,
    marginBottom: Spacing.md,
    paddingHorizontal: Spacing.sm,
    borderRadius: BorderRadius.lg,
    borderWidth: 2,
    justifyContent: 'center',
    alignItems: 'center',
    position: 'relative',
  },
  iconContainer: {
    width: 64,
    height: 64,
    borderRadius: BorderRadius.full,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: Spacing.sm,
  },
  categoryName: {
    fontSize: Typography.fontSize.lg,
    fontWeight: Typography.fontWeight.semibold,
    textAlign: 'center',
  },
  checkmark: {
    position: 'absolute',
    top: Spacing.sm,
    right: Spacing.sm,
  },
  selectedCount: {
    fontSize: Typography.fontSize.base,
    textAlign: 'center',
    marginVertical: Spacing.lg,
  },
  bottomContainer: {
    padding: Spacing.lg,
    borderTopWidth: 1,
    borderTopColor: 'rgba(0,0,0,0.1)',
  },
  completeButton: {
    paddingVertical: Spacing.md,
    borderRadius: BorderRadius.lg,
    alignItems: 'center',
  },
  completeButtonText: {
    color: '#FFFFFF',
    fontSize: Typography.fontSize.lg,
    fontWeight: Typography.fontWeight.semibold,
  },
});
