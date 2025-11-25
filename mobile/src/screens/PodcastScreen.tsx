/**
 * Podcast Screen - Audio player with 2 style modes
 * Minimal music player style & Detailed podcast style
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import Slider from '@react-native-community/slider';
import { useTheme } from '../contexts/ThemeContext';
import { useAudioPlayer } from '../contexts/AudioPlayerContext';
import { apiClient } from '../services/api';
import { FrequencyItem } from '../types/api';
import { getCategoryById } from '../constants/categories';
import { Spacing, Typography, BorderRadius } from '../constants/theme';

type PlayerStyle = 'minimal' | 'detailed';

export const PodcastScreen: React.FC = () => {
  const { colors } = useTheme();
  const {
    currentTrack,
    isPlaying,
    isLoading: audioLoading,
    position,
    duration,
    playbackRate,
    isRepeating,
    play,
    pause,
    resume,
    seekTo,
    skipForward,
    skipBackward,
    setPlaybackRate,
    toggleRepeat,
  } = useAudioPlayer();

  const [frequencies, setFrequencies] = useState<FrequencyItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [playerStyle, setPlayerStyle] = useState<PlayerStyle>('minimal');

  useEffect(() => {
    loadFrequencies();
  }, []);

  const loadFrequencies = async () => {
    try {
      setIsLoading(true);
      const data = await apiClient.getFrequencies();
      setFrequencies(data);

      // Auto-play first track if available
      if (data.length > 0 && !currentTrack) {
        await play(data[0]);
      }
    } catch (error) {
      console.error('Failed to load frequencies:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handlePlayPause = async () => {
    if (isPlaying) {
      await pause();
    } else {
      if (currentTrack) {
        await resume();
      } else if (frequencies.length > 0) {
        await play(frequencies[0]);
      }
    }
  };

  const handleSeek = async (value: number) => {
    await seekTo(value);
  };

  const formatTime = (millis: number): string => {
    const totalSeconds = Math.floor(millis / 1000);
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  const togglePlayerStyle = () => {
    setPlayerStyle(playerStyle === 'minimal' ? 'detailed' : 'minimal');
  };

  if (isLoading) {
    return (
      <View style={[styles.centerContainer, { backgroundColor: colors.background }]}>
        <ActivityIndicator size="large" color={colors.primary} />
      </View>
    );
  }

  const category = currentTrack ? getCategoryById(currentTrack.category) : null;

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: colors.background }]} edges={['top']}>
      {/* Header */}
      <View style={[styles.header, { borderBottomColor: colors.border }]}>
        <Text style={[styles.headerTitle, { color: colors.text }]}>팟캐스트</Text>
        <TouchableOpacity onPress={togglePlayerStyle}>
          <Ionicons
            name={playerStyle === 'minimal' ? 'list' : 'musical-notes'}
            size={24}
            color={colors.text}
          />
        </TouchableOpacity>
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        {playerStyle === 'minimal' ? (
          // Minimal Music Player Style
          <View style={styles.minimalPlayer}>
            <LinearGradient
              colors={category ? [category.color, colors.primary] : [colors.primary, colors.primaryLight]}
              style={styles.albumArt}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
            >
              <Ionicons name={category?.icon || 'radio'} size={80} color="#FFFFFF" />
            </LinearGradient>

            <View style={styles.trackInfo}>
              <Text style={[styles.trackTitle, { color: colors.text }]} numberOfLines={2}>
                {category?.name || '팟캐스트'}
              </Text>
              <Text style={[styles.trackSubtitle, { color: colors.textSecondary }]}>
                {currentTrack?.date || 'Today'}
              </Text>
            </View>

            {/* Progress Slider */}
            <View style={styles.progressContainer}>
              <Text style={[styles.timeText, { color: colors.textSecondary }]}>
                {formatTime(position)}
              </Text>
              <Slider
                style={styles.slider}
                value={position}
                minimumValue={0}
                maximumValue={duration || 1}
                onSlidingComplete={handleSeek}
                minimumTrackTintColor={colors.primary}
                maximumTrackTintColor={colors.border}
                thumbTintColor={colors.primary}
              />
              <Text style={[styles.timeText, { color: colors.textSecondary }]}>
                {formatTime(duration)}
              </Text>
            </View>

            {/* Controls */}
            <View style={styles.controls}>
              <TouchableOpacity onPress={() => skipBackward(15)}>
                <Ionicons name="play-back" size={32} color={colors.text} />
              </TouchableOpacity>

              <TouchableOpacity
                style={[styles.playButton, { backgroundColor: colors.primary }]}
                onPress={handlePlayPause}
              >
                {audioLoading ? (
                  <ActivityIndicator color="#FFFFFF" />
                ) : (
                  <Ionicons
                    name={isPlaying ? 'pause' : 'play'}
                    size={40}
                    color="#FFFFFF"
                  />
                )}
              </TouchableOpacity>

              <TouchableOpacity onPress={() => skipForward(15)}>
                <Ionicons name="play-forward" size={32} color={colors.text} />
              </TouchableOpacity>
            </View>
          </View>
        ) : (
          // Detailed Podcast Style
          <View style={styles.detailedPlayer}>
            <View style={[styles.detailedCard, { backgroundColor: colors.card }]}>
              <LinearGradient
                colors={category ? [category.color, colors.primary] : [colors.primary, colors.primaryLight]}
                style={styles.detailedArt}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
              >
                <Ionicons name={category?.icon || 'radio'} size={60} color="#FFFFFF" />
              </LinearGradient>

              <View style={styles.detailedInfo}>
                <Text style={[styles.detailedTitle, { color: colors.text }]} numberOfLines={2}>
                  {category?.name || '팟캐스트'}
                </Text>
                <Text style={[styles.detailedDate, { color: colors.textSecondary }]}>
                  {currentTrack?.date}
                </Text>

                {/* Script Preview */}
                {currentTrack?.script && (
                  <Text style={[styles.scriptPreview, { color: colors.textSecondary }]} numberOfLines={4}>
                    {currentTrack.script}
                  </Text>
                )}

                {/* Progress */}
                <View style={styles.detailedProgress}>
                  <Slider
                    style={styles.slider}
                    value={position}
                    minimumValue={0}
                    maximumValue={duration || 1}
                    onSlidingComplete={handleSeek}
                    minimumTrackTintColor={colors.primary}
                    maximumTrackTintColor={colors.border}
                    thumbTintColor={colors.primary}
                  />
                  <View style={styles.detailedTimes}>
                    <Text style={[styles.timeText, { color: colors.textSecondary }]}>
                      {formatTime(position)}
                    </Text>
                    <Text style={[styles.timeText, { color: colors.textSecondary }]}>
                      {formatTime(duration)}
                    </Text>
                  </View>
                </View>

                {/* Controls */}
                <View style={styles.detailedControls}>
                  <TouchableOpacity onPress={toggleRepeat}>
                    <Ionicons
                      name={isRepeating ? 'repeat' : 'repeat-outline'}
                      size={24}
                      color={isRepeating ? colors.primary : colors.textSecondary}
                    />
                  </TouchableOpacity>

                  <View style={styles.mainControls}>
                    <TouchableOpacity onPress={() => skipBackward(15)}>
                      <Ionicons name="play-back" size={28} color={colors.text} />
                    </TouchableOpacity>

                    <TouchableOpacity
                      style={[styles.detailedPlayButton, { backgroundColor: colors.primary }]}
                      onPress={handlePlayPause}
                    >
                      {audioLoading ? (
                        <ActivityIndicator color="#FFFFFF" />
                      ) : (
                        <Ionicons
                          name={isPlaying ? 'pause' : 'play'}
                          size={32}
                          color="#FFFFFF"
                        />
                      )}
                    </TouchableOpacity>

                    <TouchableOpacity onPress={() => skipForward(15)}>
                      <Ionicons name="play-forward" size={28} color={colors.text} />
                    </TouchableOpacity>
                  </View>

                  <TouchableOpacity onPress={() => setPlaybackRate(playbackRate === 1 ? 1.5 : 1)}>
                    <Text style={[styles.speedText, { color: colors.textSecondary }]}>
                      {playbackRate}x
                    </Text>
                  </TouchableOpacity>
                </View>
              </View>
            </View>

            {/* Playlist */}
            <Text style={[styles.sectionTitle, { color: colors.text }]}>재생목록</Text>
            {frequencies.map((freq) => {
              const cat = getCategoryById(freq.category);
              const isActive = currentTrack?.frequency_id === freq.frequency_id;

              return (
                <TouchableOpacity
                  key={freq.frequency_id}
                  style={[
                    styles.playlistItem,
                    { backgroundColor: isActive ? colors.primaryLight + '20' : colors.card },
                  ]}
                  onPress={() => play(freq)}
                >
                  <View
                    style={[
                      styles.playlistIcon,
                      { backgroundColor: cat?.color || colors.primary },
                    ]}
                  >
                    <Ionicons name={cat?.icon || 'radio'} size={20} color="#FFFFFF" />
                  </View>

                  <View style={styles.playlistInfo}>
                    <Text style={[styles.playlistTitle, { color: colors.text }]}>
                      {cat?.name || freq.category}
                    </Text>
                    <Text style={[styles.playlistDate, { color: colors.textSecondary }]}>
                      {freq.date}
                    </Text>
                  </View>

                  {isActive && isPlaying && (
                    <Ionicons name="volume-high" size={20} color={colors.primary} />
                  )}
                </TouchableOpacity>
              );
            })}
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: Spacing.lg,
    paddingVertical: Spacing.md,
    borderBottomWidth: 1,
  },
  headerTitle: {
    fontSize: Typography.fontSize.xxl,
    fontWeight: Typography.fontWeight.bold,
  },
  scrollContent: {
    padding: Spacing.lg,
  },

  // Minimal Player Style
  minimalPlayer: {
    alignItems: 'center',
    paddingVertical: Spacing.xxl,
  },
  albumArt: {
    width: 250,
    height: 250,
    borderRadius: BorderRadius.xl,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: Spacing.xl,
  },
  trackInfo: {
    alignItems: 'center',
    marginBottom: Spacing.xl,
  },
  trackTitle: {
    fontSize: Typography.fontSize.xxl,
    fontWeight: Typography.fontWeight.bold,
    textAlign: 'center',
  },
  trackSubtitle: {
    fontSize: Typography.fontSize.base,
    marginTop: Spacing.xs,
  },
  progressContainer: {
    width: '100%',
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: Spacing.xl,
  },
  slider: {
    flex: 1,
    marginHorizontal: Spacing.md,
  },
  timeText: {
    fontSize: Typography.fontSize.sm,
    width: 40,
    textAlign: 'center',
  },
  controls: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: Spacing.xxl,
  },
  playButton: {
    width: 80,
    height: 80,
    borderRadius: BorderRadius.full,
    justifyContent: 'center',
    alignItems: 'center',
  },

  // Detailed Player Style
  detailedPlayer: {
    paddingBottom: Spacing.xl,
  },
  detailedCard: {
    borderRadius: BorderRadius.lg,
    padding: Spacing.lg,
    marginBottom: Spacing.xl,
  },
  detailedArt: {
    width: '100%',
    height: 200,
    borderRadius: BorderRadius.lg,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: Spacing.lg,
  },
  detailedInfo: {
    width: '100%',
  },
  detailedTitle: {
    fontSize: Typography.fontSize.xl,
    fontWeight: Typography.fontWeight.bold,
    marginBottom: Spacing.xs,
  },
  detailedDate: {
    fontSize: Typography.fontSize.sm,
    marginBottom: Spacing.md,
  },
  scriptPreview: {
    fontSize: Typography.fontSize.sm,
    lineHeight: Typography.fontSize.sm * Typography.lineHeight.relaxed,
    marginBottom: Spacing.lg,
  },
  detailedProgress: {
    marginBottom: Spacing.lg,
  },
  detailedTimes: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  detailedControls: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  mainControls: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.lg,
  },
  detailedPlayButton: {
    width: 60,
    height: 60,
    borderRadius: BorderRadius.full,
    justifyContent: 'center',
    alignItems: 'center',
  },
  speedText: {
    fontSize: Typography.fontSize.base,
    fontWeight: Typography.fontWeight.semibold,
  },
  sectionTitle: {
    fontSize: Typography.fontSize.lg,
    fontWeight: Typography.fontWeight.bold,
    marginBottom: Spacing.md,
  },
  playlistItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: Spacing.md,
    borderRadius: BorderRadius.lg,
    marginBottom: Spacing.sm,
  },
  playlistIcon: {
    width: 40,
    height: 40,
    borderRadius: BorderRadius.md,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: Spacing.md,
  },
  playlistInfo: {
    flex: 1,
  },
  playlistTitle: {
    fontSize: Typography.fontSize.base,
    fontWeight: Typography.fontWeight.semibold,
  },
  playlistDate: {
    fontSize: Typography.fontSize.sm,
    marginTop: 2,
  },
});
