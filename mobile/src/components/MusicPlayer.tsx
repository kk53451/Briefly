import React from "react";
import { View, Text, StyleSheet, TouchableOpacity, Dimensions } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import Slider from "@react-native-community/slider";
import { LinearGradient } from "expo-linear-gradient";
import { useAudioPlayer } from "../contexts/AudioPlayerContext";
import { Colors, Spacing, BorderRadius, FontSizes, FontWeights } from "../constants/theme";
import { getCategoryName, getCategoryIcon } from "../constants/categories";

const { width } = Dimensions.get("window");

export const MusicPlayer: React.FC = () => {
  const {
    currentTrack,
    isPlaying,
    position,
    duration,
    progress,
    togglePlayPause,
    skip,
    seekTo,
  } = useAudioPlayer();

  if (!currentTrack) {
    return (
      <View style={styles.emptyContainer}>
        <Ionicons name="radio-outline" size={80} color={Colors.textMuted} />
        <Text style={styles.emptyText}>재생할 팟캐스트를 선택하세요</Text>
      </View>
    );
  }

  const formatTime = (millis: number) => {
    const minutes = Math.floor(millis / 60000);
    const seconds = Math.floor((millis % 60000) / 1000);
    return `${minutes}:${seconds.toString().padStart(2, "0")}`;
  };

  return (
    <View style={styles.container}>
      {/* Album Art Style Category Display */}
      <View style={styles.albumArtContainer}>
        <LinearGradient
          colors={[Colors.primary, Colors.secondary]}
          style={styles.albumArt}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
        >
          <Text style={styles.albumIcon}>{getCategoryIcon(currentTrack.category)}</Text>
          <Text style={styles.albumCategory}>{getCategoryName(currentTrack.category)}</Text>
        </LinearGradient>
      </View>

      {/* Track Info */}
      <View style={styles.trackInfo}>
        <Text style={styles.trackTitle} numberOfLines={2}>
          {currentTrack.date} 뉴스 브리핑
        </Text>
        <Text style={styles.trackArtist}>{getCategoryName(currentTrack.category)} 주파수</Text>
      </View>

      {/* Progress Bar */}
      <View style={styles.progressContainer}>
        <Slider
          style={styles.slider}
          minimumValue={0}
          maximumValue={1}
          value={progress}
          onSlidingComplete={(value) => seekTo(value * duration)}
          minimumTrackTintColor={Colors.primary}
          maximumTrackTintColor={Colors.border}
          thumbTintColor={Colors.primary}
        />
        <View style={styles.timeContainer}>
          <Text style={styles.timeText}>{formatTime(position)}</Text>
          <Text style={styles.timeText}>{formatTime(duration)}</Text>
        </View>
      </View>

      {/* Controls */}
      <View style={styles.controls}>
        <TouchableOpacity onPress={() => skip(-15)} style={styles.controlButton}>
          <Ionicons name="play-back" size={32} color={Colors.text} />
          <Text style={styles.skipText}>15</Text>
        </TouchableOpacity>

        <TouchableOpacity onPress={togglePlayPause} style={styles.playButton}>
          <LinearGradient
            colors={[Colors.primary, Colors.primaryDark]}
            style={styles.playButtonGradient}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
          >
            <Ionicons
              name={isPlaying ? "pause" : "play"}
              size={36}
              color={Colors.white}
              style={isPlaying ? undefined : { marginLeft: 4 }}
            />
          </LinearGradient>
        </TouchableOpacity>

        <TouchableOpacity onPress={() => skip(15)} style={styles.controlButton}>
          <Ionicons name="play-forward" size={32} color={Colors.text} />
          <Text style={styles.skipText}>15</Text>
        </TouchableOpacity>
      </View>

      {/* Additional Controls */}
      <View style={styles.additionalControls}>
        <TouchableOpacity style={styles.iconButton}>
          <Ionicons name="repeat" size={24} color={Colors.textSecondary} />
        </TouchableOpacity>
        <TouchableOpacity style={styles.iconButton}>
          <Ionicons name="share-outline" size={24} color={Colors.textSecondary} />
        </TouchableOpacity>
        <TouchableOpacity style={styles.iconButton}>
          <Ionicons name="speedometer-outline" size={24} color={Colors.textSecondary} />
        </TouchableOpacity>
        <TouchableOpacity style={styles.iconButton}>
          <Ionicons name="heart-outline" size={24} color={Colors.textSecondary} />
        </TouchableOpacity>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
    alignItems: "center",
    paddingVertical: Spacing.xl,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: Colors.background,
  },
  emptyText: {
    fontSize: FontSizes.md,
    color: Colors.textMuted,
    marginTop: Spacing.lg,
  },
  albumArtContainer: {
    marginVertical: Spacing.xl,
    shadowColor: Colors.primary,
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.3,
    shadowRadius: 20,
    elevation: 10,
  },
  albumArt: {
    width: width - 100,
    height: width - 100,
    borderRadius: BorderRadius.xl,
    justifyContent: "center",
    alignItems: "center",
  },
  albumIcon: {
    fontSize: 100,
    marginBottom: Spacing.md,
  },
  albumCategory: {
    fontSize: FontSizes.xl,
    fontWeight: FontWeights.bold,
    color: Colors.white,
  },
  trackInfo: {
    alignItems: "center",
    marginVertical: Spacing.lg,
    paddingHorizontal: Spacing.xl,
  },
  trackTitle: {
    fontSize: FontSizes.xl,
    fontWeight: FontWeights.bold,
    color: Colors.text,
    textAlign: "center",
    marginBottom: Spacing.xs,
  },
  trackArtist: {
    fontSize: FontSizes.md,
    color: Colors.textSecondary,
  },
  progressContainer: {
    width: width - 60,
    marginVertical: Spacing.lg,
  },
  slider: {
    width: "100%",
    height: 40,
  },
  timeContainer: {
    flexDirection: "row",
    justifyContent: "space-between",
    paddingHorizontal: Spacing.sm,
  },
  timeText: {
    fontSize: FontSizes.xs,
    color: Colors.textSecondary,
  },
  controls: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    marginVertical: Spacing.xl,
    gap: Spacing.xl,
  },
  controlButton: {
    width: 60,
    height: 60,
    justifyContent: "center",
    alignItems: "center",
    position: "relative",
  },
  skipText: {
    position: "absolute",
    bottom: 8,
    fontSize: 10,
    color: Colors.textSecondary,
    fontWeight: FontWeights.bold,
  },
  playButton: {
    width: 80,
    height: 80,
    borderRadius: 40,
    shadowColor: Colors.primary,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  playButtonGradient: {
    width: "100%",
    height: "100%",
    borderRadius: 40,
    justifyContent: "center",
    alignItems: "center",
  },
  additionalControls: {
    flexDirection: "row",
    justifyContent: "space-around",
    width: width - 80,
    marginTop: Spacing.xl,
  },
  iconButton: {
    padding: Spacing.sm,
  },
});
