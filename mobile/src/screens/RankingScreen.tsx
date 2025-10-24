import React, { useState, useEffect } from "react";
import { View, Text, StyleSheet, ScrollView, RefreshControl, ActivityIndicator } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useNavigation } from "@react-navigation/native";
import { NativeStackNavigationProp } from "@react-navigation/native-stack";
import { RootStackParamList } from "../navigation/types";
import { NewsCard } from "../components/NewsCard";
import { apiClient } from "../services/api";
import { NewsItem } from "../types/api";
import { Colors, Spacing, FontSizes, FontWeights } from "../constants/theme";

type NavigationProp = NativeStackNavigationProp<RootStackParamList>;

const RankingScreen: React.FC = () => {
  const navigation = useNavigation<NavigationProp>();
  const [news, setNews] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadRankingNews();
  }, []);

  const loadRankingNews = async () => {
    try {
      setLoading(true);
      // 모든 카테고리에서 조회수 높은 순으로 정렬
      const response = await apiClient.getTodayNews();
      const allNews: NewsItem[] = [];
      Object.values(response.categories).forEach((categoryNews) => {
        allNews.push(...categoryNews);
      });
      const sorted = allNews.sort((a, b) => b.view_count - a.view_count).slice(0, 20);
      setNews(sorted);
    } catch (error) {
      console.error("Failed to load ranking news:", error);
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadRankingNews();
    setRefreshing(false);
  };

  const handleBookmark = async (newsId: string, isBookmarked: boolean) => {
    try {
      if (isBookmarked) {
        await apiClient.removeBookmark(newsId);
      } else {
        await apiClient.bookmarkNews(newsId);
      }

      setNews((prev) =>
        prev.map((item) =>
          item.news_id === newsId ? { ...item, is_bookmarked: !isBookmarked } : item
        )
      );
    } catch (error) {
      console.error("Failed to toggle bookmark:", error);
    }
  };

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
        <Text style={styles.title}>🏆 인기 뉴스</Text>
        <Text style={styles.subtitle}>가장 많이 본 뉴스</Text>
      </View>

      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
      >
        {news.map((item, index) => (
          <View key={item.news_id} style={styles.newsItem}>
            <View style={styles.rankBadge}>
              <Text style={styles.rankText}>{index + 1}</Text>
            </View>
            <View style={styles.newsCardWrapper}>
              <NewsCard
                news={item}
                onPress={() => navigation.navigate("NewsDetail", { newsId: item.news_id })}
                onBookmark={() => handleBookmark(item.news_id, item.is_bookmarked)}
              />
            </View>
          </View>
        ))}
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
    paddingBottom: Spacing.md,
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
  scroll: {
    flex: 1,
  },
  content: {
    padding: Spacing.lg,
  },
  newsItem: {
    flexDirection: "row",
    alignItems: "flex-start",
    marginBottom: Spacing.md,
  },
  rankBadge: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: Colors.primary,
    justifyContent: "center",
    alignItems: "center",
    marginRight: Spacing.sm,
    marginTop: Spacing.sm,
  },
  rankText: {
    fontSize: FontSizes.sm,
    fontWeight: FontWeights.bold,
    color: Colors.white,
  },
  newsCardWrapper: {
    flex: 1,
  },
});

export default RankingScreen;
