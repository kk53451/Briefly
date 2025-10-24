import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";
import { MusicPlayer } from "../components/MusicPlayer";
import { useAudioPlayer } from "../contexts/AudioPlayerContext";
import { apiClient } from "../services/api";
import { FrequencyItem } from "../types/api";
import { getCategoryName, getCategoryIcon } from "../constants/categories";
import { Colors, Spacing, BorderRadius, FontSizes, FontWeights } from "../constants/theme";
import { format } from "date-fns";
import { ko } from "date-fns/locale";

const PodcastScreen: React.FC = () => {
  const { currentTrack, loadTrack } = useAudioPlayer();
  const [frequencies, setFrequencies] = useState<FrequencyItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [showPlayer, setShowPlayer] = useState(false);

  useEffect(() => {
    loadFrequencies();
  }, []);

  const loadFrequencies = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getUserFrequencies();
      setFrequencies(data);
    } catch (error) {
      console.error("Failed to load frequencies:", error);
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadFrequencies();
    setRefreshing(false);
  };

  const handlePlayFrequency = async (frequency: FrequencyItem) => {
    await loadTrack(frequency);
    setShowPlayer(true);
  };

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color={Colors.primary} />
      </View>
    );
  }

  if (showPlayer && currentTrack) {
    return (
      <SafeAreaView style={styles.container} edges={["top"]}>
        <View style={styles.playerHeader}>
          <TouchableOpacity onPress={() => setShowPlayer(false)}>
            <Ionicons name="chevron-down" size={28} color={Colors.text} />
          </TouchableOpacity>
          <Text style={styles.playerHeaderTitle}>재생 중</Text>
          <TouchableOpacity>
            <Ionicons name="ellipsis-vertical" size={24} color={Colors.text} />
          </TouchableOpacity>
        </View>
        <MusicPlayer />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={["top"]}>
      <View style={styles.header}>
        <Text style={styles.title}>📻 나의 주파수</Text>
        <Text style={styles.subtitle}>오늘의 맞춤 팟캐스트</Text>
      </View>

      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
      >
        {frequencies.length > 0 ? (
          frequencies.map((frequency) => (
            <FrequencyCard
              key={frequency.frequency_id}
              frequency={frequency}
              onPlay={() => handlePlayFrequency(frequency)}
              isPlaying={currentTrack?.frequency_id === frequency.frequency_id}
            />
          ))
        ) : (
          <View style={styles.emptyContainer}>
            <Ionicons name="radio-outline" size={80} color={Colors.textMuted} />
            <Text style={styles.emptyText}>아직 생성된 팟캐스트가 없습니다</Text>
            <Text style={styles.emptySubtext}>매일 새벽 6시에 업데이트됩니다</Text>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
};

const FrequencyCard: React.FC<{
  frequency: FrequencyItem;
  onPlay: () => void;
  isPlaying: boolean;
}> = ({ frequency, onPlay, isPlaying }) => {
  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  return (
    <TouchableOpacity style={styles.frequencyCard} onPress={onPlay} activeOpacity={0.7}>
      <View style={styles.frequencyIcon}>
        <Text style={styles.frequencyEmoji}>{getCategoryIcon(frequency.category)}</Text>
      </View>

      <View style={styles.frequencyInfo}>
        <Text style={styles.frequencyCategory}>{getCategoryName(frequency.category)}</Text>
        <Text style={styles.frequencyDate}>
          {format(new Date(frequency.date), "yyyy년 MM월 dd일", { locale: ko })}
        </Text>
        <Text style={styles.frequencyDuration}>{formatDuration(frequency.duration)}</Text>
      </View>

      <TouchableOpacity style={styles.playButton} onPress={onPlay}>
        <Ionicons
          name={isPlaying ? "pause-circle" : "play-circle"}
          size={48}
          color={Colors.primary}
        />
      </TouchableOpacity>
    </TouchableOpacity>
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
  playerHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingHorizontal: Spacing.lg,
    paddingVertical: Spacing.md,
  },
  playerHeaderTitle: {
    fontSize: FontSizes.md,
    fontWeight: FontWeights.semibold,
    color: Colors.text,
  },
  scroll: {
    flex: 1,
  },
  content: {
    padding: Spacing.lg,
  },
  emptyContainer: {
    paddingVertical: Spacing.xxl * 2,
    alignItems: "center",
  },
  emptyText: {
    fontSize: FontSizes.md,
    color: Colors.textMuted,
    marginTop: Spacing.lg,
  },
  emptySubtext: {
    fontSize: FontSizes.sm,
    color: Colors.textMuted,
    marginTop: Spacing.xs,
  },
  frequencyCard: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: Colors.backgroundCard,
    borderRadius: BorderRadius.lg,
    padding: Spacing.md,
    marginBottom: Spacing.md,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  frequencyIcon: {
    width: 60,
    height: 60,
    borderRadius: BorderRadius.md,
    backgroundColor: Colors.primary + "20",
    justifyContent: "center",
    alignItems: "center",
    marginRight: Spacing.md,
  },
  frequencyEmoji: {
    fontSize: 30,
  },
  frequencyInfo: {
    flex: 1,
  },
  frequencyCategory: {
    fontSize: FontSizes.md,
    fontWeight: FontWeights.semibold,
    color: Colors.text,
    marginBottom: 4,
  },
  frequencyDate: {
    fontSize: FontSizes.sm,
    color: Colors.textSecondary,
    marginBottom: 2,
  },
  frequencyDuration: {
    fontSize: FontSizes.xs,
    color: Colors.textMuted,
  },
  playButton: {
    marginLeft: Spacing.sm,
  },
});

export default PodcastScreen;
