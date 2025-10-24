import React, { useState, useEffect } from "react";
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Alert } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useNavigation } from "@react-navigation/native";
import { Button } from "../components/Button";
import { useAuth } from "../contexts/AuthContext";
import { apiClient } from "../services/api";
import { CATEGORIES } from "../constants/categories";
import { Colors, Spacing, BorderRadius, FontSizes, FontWeights } from "../constants/theme";

const CategoriesScreen: React.FC = () => {
  const navigation = useNavigation();
  const { user, refreshUser } = useAuth();
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (user?.interests) {
      setSelectedCategories(user.interests);
    }
  }, [user]);

  const toggleCategory = (categoryId: string) => {
    if (selectedCategories.includes(categoryId)) {
      setSelectedCategories(selectedCategories.filter((id) => id !== categoryId));
    } else {
      setSelectedCategories([...selectedCategories, categoryId]);
    }
  };

  const handleSave = async () => {
    if (selectedCategories.length === 0) {
      Alert.alert("알림", "최소 1개 이상의 카테고리를 선택해주세요.");
      return;
    }

    try {
      setLoading(true);
      await apiClient.updateUserCategories(selectedCategories);
      await refreshUser();
      Alert.alert("성공", "카테고리가 업데이트되었습니다.");
      navigation.goBack();
    } catch (error) {
      Alert.alert("오류", "카테고리 업데이트에 실패했습니다.");
      console.error("Failed to update categories:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container} edges={["bottom"]}>
      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
      >
        <Text style={styles.description}>
          관심있는 카테고리를 선택하면{"\n"}맞춤 뉴스와 팟캐스트를 제공합니다
        </Text>

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

        <View style={styles.footer}>
          <Text style={styles.infoText}>선택한 카테고리: {selectedCategories.length}개</Text>
          <Button
            title="저장"
            onPress={handleSave}
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
  scroll: {
    flex: 1,
  },
  content: {
    padding: Spacing.lg,
  },
  description: {
    fontSize: FontSizes.md,
    color: Colors.textSecondary,
    textAlign: "center",
    lineHeight: 22,
    marginBottom: Spacing.xl,
  },
  categoriesGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: Spacing.md,
    marginBottom: Spacing.xl,
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

export default CategoriesScreen;
