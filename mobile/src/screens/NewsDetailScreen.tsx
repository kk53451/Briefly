import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Image,
  TouchableOpacity,
  ActivityIndicator,
  Linking,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";
import { RouteProp, useRoute } from "@react-navigation/native";
import { RootStackParamList } from "../navigation/types";
import { apiClient } from "../services/api";
import { NewsDetail } from "../types/api";
import { getCategoryName, getCategoryIcon } from "../constants/categories";
import { Colors, Spacing, BorderRadius, FontSizes, FontWeights } from "../constants/theme";
import { format } from "date-fns";
import { ko } from "date-fns/locale";

type NewsDetailRouteProp = RouteProp<RootStackParamList, "NewsDetail">;

const NewsDetailScreen: React.FC = () => {
  const route = useRoute<NewsDetailRouteProp>();
  const { newsId } = route.params;
  const [news, setNews] = useState<NewsDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadNewsDetail();
  }, [newsId]);

  const loadNewsDetail = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getNewsDetail(newsId);
      setNews(data);
    } catch (error) {
      console.error("Failed to load news detail:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleBookmark = async () => {
    if (!news) return;

    try {
      if (news.is_bookmarked) {
        await apiClient.removeBookmark(newsId);
      } else {
        await apiClient.bookmarkNews(newsId);
      }
      setNews({ ...news, is_bookmarked: !news.is_bookmarked });
    } catch (error) {
      console.error("Failed to toggle bookmark:", error);
    }
  };

  const handleOpenUrl = () => {
    if (news?.url) {
      Linking.openURL(news.url);
    }
  };

  if (loading || !news) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color={Colors.primary} />
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={["bottom"]}>
      <ScrollView style={styles.scroll} showsVerticalScrollIndicator={false}>
        {news.image_url && (
          <Image source={{ uri: news.image_url }} style={styles.image} resizeMode="cover" />
        )}

        <View style={styles.content}>
          <View style={styles.header}>
            <View style={styles.categoryBadge}>
              <Text style={styles.categoryIcon}>{getCategoryIcon(news.category)}</Text>
              <Text style={styles.categoryText}>{getCategoryName(news.category)}</Text>
            </View>
            <TouchableOpacity onPress={handleBookmark}>
              <Ionicons
                name={news.is_bookmarked ? "bookmark" : "bookmark-outline"}
                size={24}
                color={news.is_bookmarked ? Colors.primary : Colors.textSecondary}
              />
            </TouchableOpacity>
          </View>

          <Text style={styles.title}>{news.title}</Text>

          <View style={styles.meta}>
            <Text style={styles.source}>{news.source}</Text>
            <Text style={styles.date}>
              {format(new Date(news.published_date), "yyyy년 MM월 dd일", { locale: ko })}
            </Text>
          </View>

          <Text style={styles.summary}>{news.summary}</Text>

          <View style={styles.divider} />

          <Text style={styles.contentText}>{news.content}</Text>

          {news.tags && news.tags.length > 0 && (
            <View style={styles.tags}>
              {news.tags.map((tag, index) => (
                <View key={index} style={styles.tag}>
                  <Text style={styles.tagText}>#{tag}</Text>
                </View>
              ))}
            </View>
          )}

          <TouchableOpacity style={styles.urlButton} onPress={handleOpenUrl}>
            <Ionicons name="open-outline" size={20} color={Colors.primary} />
            <Text style={styles.urlButtonText}>원본 기사 보기</Text>
          </TouchableOpacity>
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
  centerContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: Colors.background,
  },
  scroll: {
    flex: 1,
  },
  image: {
    width: "100%",
    height: 250,
    backgroundColor: Colors.backgroundLight,
  },
  content: {
    padding: Spacing.lg,
  },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: Spacing.md,
  },
  categoryBadge: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: Colors.backgroundLight,
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.sm,
    borderRadius: BorderRadius.md,
  },
  categoryIcon: {
    fontSize: FontSizes.md,
    marginRight: 6,
  },
  categoryText: {
    fontSize: FontSizes.sm,
    color: Colors.textSecondary,
    fontWeight: FontWeights.medium,
  },
  title: {
    fontSize: FontSizes.xl,
    fontWeight: FontWeights.bold,
    color: Colors.text,
    lineHeight: 32,
    marginBottom: Spacing.md,
  },
  meta: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: Spacing.md,
  },
  source: {
    fontSize: FontSizes.sm,
    color: Colors.textMuted,
  },
  date: {
    fontSize: FontSizes.sm,
    color: Colors.textMuted,
  },
  summary: {
    fontSize: FontSizes.md,
    color: Colors.textSecondary,
    lineHeight: 24,
    marginBottom: Spacing.lg,
    fontWeight: FontWeights.medium,
  },
  divider: {
    height: 1,
    backgroundColor: Colors.border,
    marginVertical: Spacing.lg,
  },
  contentText: {
    fontSize: FontSizes.md,
    color: Colors.text,
    lineHeight: 26,
    marginBottom: Spacing.lg,
  },
  tags: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: Spacing.sm,
    marginBottom: Spacing.lg,
  },
  tag: {
    backgroundColor: Colors.backgroundLight,
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.xs,
    borderRadius: BorderRadius.md,
  },
  tagText: {
    fontSize: FontSizes.sm,
    color: Colors.textSecondary,
  },
  urlButton: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: Colors.primary + "20",
    padding: Spacing.md,
    borderRadius: BorderRadius.lg,
    borderWidth: 1,
    borderColor: Colors.primary,
    gap: Spacing.sm,
  },
  urlButtonText: {
    fontSize: FontSizes.md,
    color: Colors.primary,
    fontWeight: FontWeights.semibold,
  },
});

export default NewsDetailScreen;
