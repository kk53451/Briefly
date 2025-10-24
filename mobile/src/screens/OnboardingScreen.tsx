import React, { useState } from "react";
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Alert } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Button } from "../components/Button";
import { useAuth } from "../contexts/AuthContext";
import { apiClient } from "../services/api";
import { CATEGORIES } from "../constants/categories";
import { Colors, Spacing, BorderRadius, FontSizes, FontWeights } from "../constants/theme";

const OnboardingScreen: React.FC = () => {
  const { refreshUser } = useAuth();
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  const toggleCategory = (categoryId: string) => {
    if (selectedCategories.includes(categoryId)) {
      setSelectedCategories(selectedCategories.filter((id) => id !== categoryId));
    } else {
      setSelectedCategories([...selectedCategories, categoryId]);
    }
  };

  const handleComplete = async () => {
    if (selectedCategories.length === 0) {
      Alert.alert("알림", "최소 1개 이상의 카테고리를 선택해주세요.");
      return;
    }

    try {
      setLoading(true);
      await apiClient.updateUserCategories(selectedCategories);
      await apiClient.completeOnboarding();
      await refreshUser();
    } catch (error) {
      Alert.alert("오류", "설정 저장에 실패했습니다. 다시 시도해주세요.");
      console.error("Onboarding error:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.header}>
          <Text style={styles.emoji}>👋</Text>
          <Text style={styles.title}>환영합니다!</Text>
          <Text style={styles.subtitle}>
            관심있는 뉴스 카테고리를 선택하면{"\n"}매일 맞춤 팟캐스트를 제공해드려요
          </Text>
        </View>

        <View style={styles.categoriesContainer}>
          <Text style={styles.sectionTitle}>관심 카테고리 선택</Text>
          <View style={styles.categoriesGrid}>
            {CATEGORIES.map((category) => {
              const isSelected = selectedCategories.includes(category.id);
              return (
                <TouchableOpacity
                  key={category.id}
                  style={[styles.categoryCard, isSelected && styles.categoryCardSelected]}
                  onPress={() => toggleCategory(category.id)}
                  activeOpacity={0.7}
                >
                  <Text style={styles.categoryIcon}>{category.icon}</Text>
                  <Text style={[styles.categoryName, isSelected && styles.categoryNameSelected]}>
                    {category.name}
                  </Text>
                </TouchableOpacity>
              );
            })}
          </View>
        </View>

        <View style={styles.footer}>
          <Text style={styles.infoText}>
            선택한 카테고리: {selectedCategories.length}개
          </Text>
          <Button
            title="시작하기"
            onPress={handleComplete}
            loading={loading}
            disabled={selectedCategories.length === 0}
            fullWidth
          />
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  content: {
    flexGrow: 1,
    paddingHorizontal: Spacing.lg,
    paddingTop: Spacing.xl,
    paddingBottom: Spacing.lg,
  },
  header: {
    alignItems: "center",
    marginBottom: Spacing.xl,
  },
  emoji: {
    fontSize: 60,
    marginBottom: Spacing.md,
  },
  title: {
    fontSize: FontSizes.xxxl,
    fontWeight: FontWeights.bold,
    color: Colors.text,
    marginBottom: Spacing.sm,
  },
  subtitle: {
    fontSize: FontSizes.md,
    color: Colors.textSecondary,
    textAlign: "center",
    lineHeight: 22,
  },
  categoriesContainer: {
    flex: 1,
    marginBottom: Spacing.xl,
  },
  sectionTitle: {
    fontSize: FontSizes.lg,
    fontWeight: FontWeights.semibold,
    color: Colors.text,
    marginBottom: Spacing.md,
  },
  categoriesGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: Spacing.md,
  },
  categoryCard: {
    width: "47%",
    aspectRatio: 1.5,
    backgroundColor: Colors.backgroundLight,
    borderRadius: BorderRadius.lg,
    padding: Spacing.md,
    justifyContent: "center",
    alignItems: "center",
    borderWidth: 2,
    borderColor: Colors.border,
  },
  categoryCardSelected: {
    borderColor: Colors.primary,
    backgroundColor: Colors.primary + "20",
  },
  categoryIcon: {
    fontSize: 40,
    marginBottom: Spacing.sm,
  },
  categoryName: {
    fontSize: FontSizes.md,
    fontWeight: FontWeights.semibold,
    color: Colors.textSecondary,
  },
  categoryNameSelected: {
    color: Colors.primary,
  },
  footer: {
    gap: Spacing.md,
  },
  infoText: {
    fontSize: FontSizes.sm,
    color: Colors.textSecondary,
    textAlign: "center",
  },
});

export default OnboardingScreen;
