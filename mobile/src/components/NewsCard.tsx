import React from "react";
import { View, Text, StyleSheet, Image, TouchableOpacity } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { NewsItem } from "../types/api";
import { Colors, Spacing, BorderRadius, FontSizes, FontWeights } from "../constants/theme";
import { getCategoryName, getCategoryIcon } from "../constants/categories";
import { format } from "date-fns";
import { ko } from "date-fns/locale";

interface NewsCardProps {
  news: NewsItem;
  onPress: () => void;
  onBookmark: () => void;
}

export const NewsCard: React.FC<NewsCardProps> = ({ news, onPress, onBookmark }) => {
  return (
    <TouchableOpacity style={styles.card} onPress={onPress} activeOpacity={0.7}>
      <View style={styles.header}>
        <View style={styles.categoryBadge}>
          <Text style={styles.categoryIcon}>{getCategoryIcon(news.category)}</Text>
          <Text style={styles.categoryText}>{getCategoryName(news.category)}</Text>
        </View>
        <TouchableOpacity onPress={onBookmark} hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}>
          <Ionicons
            name={news.is_bookmarked ? "bookmark" : "bookmark-outline"}
            size={20}
            color={news.is_bookmarked ? Colors.primary : Colors.textSecondary}
          />
        </TouchableOpacity>
      </View>

      {news.image_url && (
        <Image source={{ uri: news.image_url }} style={styles.image} resizeMode="cover" />
      )}

      <Text style={styles.title} numberOfLines={2}>
        {news.title}
      </Text>

      <Text style={styles.summary} numberOfLines={3}>
        {news.summary}
      </Text>

      <View style={styles.footer}>
        <Text style={styles.source}>{news.source}</Text>
        <Text style={styles.date}>
          {format(new Date(news.published_date), "MM월 dd일", { locale: ko })}
        </Text>
      </View>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: Colors.backgroundCard,
    borderRadius: BorderRadius.lg,
    padding: Spacing.md,
    marginBottom: Spacing.md,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: Spacing.sm,
  },
  categoryBadge: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: Colors.backgroundLight,
    paddingHorizontal: Spacing.sm,
    paddingVertical: 4,
    borderRadius: BorderRadius.md,
  },
  categoryIcon: {
    fontSize: FontSizes.sm,
    marginRight: 4,
  },
  categoryText: {
    fontSize: FontSizes.xs,
    color: Colors.textSecondary,
    fontWeight: FontWeights.medium,
  },
  image: {
    width: "100%",
    height: 180,
    borderRadius: BorderRadius.md,
    marginBottom: Spacing.sm,
    backgroundColor: Colors.backgroundLight,
  },
  title: {
    fontSize: FontSizes.lg,
    fontWeight: FontWeights.bold,
    color: Colors.text,
    marginBottom: Spacing.xs,
    lineHeight: 24,
  },
  summary: {
    fontSize: FontSizes.sm,
    color: Colors.textSecondary,
    lineHeight: 20,
    marginBottom: Spacing.sm,
  },
  footer: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  source: {
    fontSize: FontSizes.xs,
    color: Colors.textMuted,
  },
  date: {
    fontSize: FontSizes.xs,
    color: Colors.textMuted,
  },
});
