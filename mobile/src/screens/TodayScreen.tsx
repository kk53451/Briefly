import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
  ActivityIndicator,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useNavigation } from "@react-navigation/native";
import { NativeStackNavigationProp } from "@react-navigation/native-stack";
import { RootStackParamList } from "../navigation/types";
import { NewsCard } from "../components/NewsCard";
import { apiClient } from "../services/api";
import { NewsItem } from "../types/api";
import { CATEGORIES } from "../constants/categories";
import { Colors, Spacing, FontSizes, FontWeights } from "../constants/theme";

type NavigationProp = NativeStackNavigationProp<RootStackParamList>;

const TodayScreen: React.FC = () => {
  const navigation = useNavigation<NavigationProp>();
  const [selectedCategory, setSelectedCategory] = useState<string>("politics");
  const [newsData, setNewsData] = useState<{ [key: string]: NewsItem[] }>({});
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadTodayNews();
  }, []);

  const loadTodayNews = async () => {
    try {
      setLoading(true);
      const response = await apiClient.getTodayNews();
      setNewsData(response.categories);
    } catch (error) {
      console.error("Failed to load today news:", error);
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadTodayNews();
    setRefreshing(false);
  };

  const handleBookmark = async (newsId: string, isBookmarked: boolean) => {
    try {
      if (isBookmarked) {
        await apiClient.removeBookmark(newsId);
      } else {
        await apiClient.bookmarkNews(newsId);
      }

      // 로컬 상태 업데이트
      setNewsData((prev) => {
        const updated = { ...prev };
        Object.keys(updated).forEach((category) => {
          updated[category] = updated[category].map((news) =>
            news.news_id === newsId ? { ...news, is_bookmarked: !isBookmarked } : news
          );
        });
        return updated;
      });
    } catch (error) {
      console.error("Failed to toggle bookmark:", error);
    }
  };

  const currentNews = newsData[selectedCategory] || [];

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color={Colors.primary} />
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={["top"]}>
      <View style={styles.header}>
        <Text style={styles.title}>오늘의 뉴스</Text>
        <Text style={styles.subtitle}>매일 업데이트되는 최신 뉴스</Text>
      </View>

      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        style={styles.categoryScroll}
        contentContainerStyle={styles.categoryScrollContent}
      >
        {CATEGORIES.map((category) => (
          <TouchableOpacity
            key={category.id}
            style={[
              styles.categoryTab,
              selectedCategory === category.id && styles.categoryTabActive,
            ]}
            onPress={() => setSelectedCategory(category.id)}
          >
            <Text style={styles.categoryIcon}>{category.icon}</Text>
            <Text
              style={[
                styles.categoryText,
                selectedCategory === category.id && styles.categoryTextActive,
              ]}
            >
              {category.name}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      <ScrollView
        style={styles.newsScroll}
        contentContainerStyle={styles.newsContent}
        showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
      >
        {currentNews.length > 0 ? (
          currentNews.map((news) => (
            <NewsCard
              key={news.news_id}
              news={news}
              onPress={() =>
                navigation.navigate("NewsDetail", { newsId: news.news_id })
              }
              onBookmark={() => handleBookmark(news.news_id, news.is_bookmarked)}
            />
          ))
        ) : (
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyText}>뉴스가 없습니다</Text>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  centerContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: Colors.background,
  },
  header: {
    paddingHorizontal: Spacing.lg,
    paddingTop: Spacing.md,
    paddingBottom: Spacing.sm,
  },
  title: {
    fontSize: FontSizes.xxl,
    fontWeight: FontWeights.bold,
    color: Colors.text,
  },
  subtitle: {
    fontSize: FontSizes.sm,
    color: Colors.textSecondary,
    marginTop: 4,
  },
  categoryScroll: {
    maxHeight: 60,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  categoryScrollContent: {
    paddingHorizontal: Spacing.lg,
    paddingVertical: Spacing.sm,
    gap: Spacing.sm,
  },
  categoryTab: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: Spacing.sm,
    paddingHorizontal: Spacing.md,
    backgroundColor: Colors.backgroundLight,
    borderRadius: 20,
    gap: 6,
  },
  categoryTabActive: {
    backgroundColor: Colors.primary,
  },
  categoryIcon: {
    fontSize: 18,
  },
  categoryText: {
    fontSize: FontSizes.sm,
    fontWeight: FontWeights.medium,
    color: Colors.textSecondary,
  },
  categoryTextActive: {
    color: Colors.white,
  },
  newsScroll: {
    flex: 1,
  },
  newsContent: {
    padding: Spacing.lg,
  },
  emptyContainer: {
    paddingVertical: Spacing.xxl,
    alignItems: "center",
  },
  emptyText: {
    fontSize: FontSizes.md,
    color: Colors.textMuted,
  },
});

export default TodayScreen;
